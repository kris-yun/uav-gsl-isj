# Smart Monitor for Claude Code - checks every 60s
# Only sends input when needed (confirmation or new instruction)

param(
    [int]$IntervalSec = 60,
    [string]$ResultsDir = 'D:\ZYC\A-gas\automation\results',
    [string]$ManualDir = 'D:\ZYC\A-gas\automation\manual'
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinMon {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$vscodeHandle = [IntPtr]2497872
$lastResultsHash = ''
$lastInstructionSent = ''
$logFile = 'D:\ZYC\A-gas\automation\monitor\smart_monitor.log'
$house01Done = $false
$house02Done = $false
$house03Done = $false
$summaryDone = $false

function Log($msg) {
    $ts = Get-Date -Format 'HH:mm:ss'
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content $logFile $line -ErrorAction SilentlyContinue
}

function Focus-VSCode {
    [WinMon]::ShowWindow($vscodeHandle, 9) | Out-Null
    [WinMon]::SetForegroundWindow($vscodeHandle) | Out-Null
    Start-Sleep -Milliseconds 400
}

function Get-TerminalEdit {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($vscodeHandle)
        $cond = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Edit)
        $edits = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
        foreach ($e in $edits) {
            if ($e.Current.Name -match '终端 15|Claude Code') { return $e }
        }
        return $null
    } catch { return $null }
}

function Has-ConfirmationButton {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($vscodeHandle)
        $cond = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button)
        $btns = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
        foreach ($b in $btns) {
            $name = $b.Current.Name
            if ($name -match '(?i)^(yes|allow|approve|continue|ok|run|accept|confirm|y)$') {
                return $name
            }
        }
    } catch {}
    return $null
}

function Send-Enter {
    $term = Get-TerminalEdit
    if ($term) {
        Focus-VSCode
        $term.SetFocus()
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        Log "Sent ENTER to terminal"
        return $true
    }
    Log "Terminal not found for ENTER"
    return $false
}

function Send-Text($text) {
    $term = Get-TerminalEdit
    if ($term) {
        Focus-VSCode
        $term.SetFocus()
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.Clipboard]::SetText($text)
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('^v')
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        Log "Sent text ($($text.Length) chars) to terminal"
        return $true
    }
    Log "Terminal not found for text"
    return $false
}

function Get-ResultsHash {
    if (!(Test-Path $ResultsDir)) { return '' }
    $files = Get-ChildItem $ResultsDir -File | Sort-Object Name | ForEach-Object { "$($_.Name):$($_.LastWriteTime.Ticks):$($_.Length)" }
    return ($files -join '|')
}

function Check-HouseResults {
    $h01 = Test-Path "$ResultsDir\iter11_gaden_house01.csv"
    $h02 = Test-Path "$ResultsDir\iter11_gaden_house02.csv"
    $h03 = Test-Path "$ResultsDir\iter11_gaden_house03.csv"
    $sum = Test-Path "$ResultsDir\iter11_gaden_summary.md"
    
    # Check if CSVs have enough rows (>1 = more than just header)
    $h01ok = $false; $h02ok = $false; $h03ok = $false
    if ($h01) { $h01ok = (Get-Content "$ResultsDir\iter11_gaden_house01.csv" | Measure-Object).Count -gt 2 }
    if ($h02) { $h02ok = (Get-Content "$ResultsDir\iter11_gaden_house02.csv" | Measure-Object).Count -gt 2 }
    if ($h03) { $h03ok = (Get-Content "$ResultsDir\iter11_gaden_house03.csv" | Measure-Object).Count -gt 2 }
    
    return @{ h01=$h01ok; h02=$h02ok; h03=$h03ok; summary=$sum }
}

function Get-NextInstruction {
    $status = Check-HouseResults
    
    if ($status.summary) {
        return @{ action='done'; msg='All GADEN experiments complete. Summary generated.' }
    }
    
    if (!$status.h02 -and $status.h01) {
        $inst = Get-Content "$ManualDir\step_gaden_houses.md" -Raw -ErrorAction SilentlyContinue
        if ($inst -and $lastInstructionSent -ne 'house02') {
            return @{ action='send'; msg='House01 done, send House02 instruction'; text=$inst }
        }
    }
    
    if ($status.h02 -and !$status.h03) {
        $inst = @"
House02完成。现在运行House03。

修改run_iter11_gaden.py中SCENARIOS只保留House03:
    SCENARIOS = [{
        "house": "House03",
        "config_id": "1-2,5_fast",
        "source": "-0.45 1.9 -0.1",
        "starts": "0,-5;-3,-1;0,0;-1,2;-4,-3",
    }]

然后运行: D:\Anaconda\python.exe scripts\run_iter11_gaden.py
"@
        if ($lastInstructionSent -ne 'house03') {
            return @{ action='send'; msg='House02 done, send House03 instruction'; text=$inst }
        }
    }
    
    if ($status.h01 -and $status.h02 -and $status.h03 -and !$status.summary) {
        $inst = @"
三个House的GADEN实验都完成了。现在生成汇总分析:

1. 运行run_iter11_gaden.py(它会自动生成iter11_gaden_summary.md)
2. 或者手动分析三个CSV文件，生成汇总
3. 比较DQA_AS_V2 vs DQA_AS vs 其他基线
4. 诚实记录结果，不调参
"@
        if ($lastInstructionSent -ne 'summary') {
            return @{ action='send'; msg='All houses done, send summary instruction'; text=$inst }
        }
    }
    
    return @{ action='wait'; msg='Waiting for results...' }
}

# Main loop
Log "=== Smart Monitor Started (interval=${IntervalSec}s) ==="
Log "Watching: $ResultsDir"

while ($true) {
    try {
        # Step 1: Check for confirmation button
        $btn = Has-ConfirmationButton
        if ($btn) {
            Log "Found confirmation button: $btn"
            Send-Enter | Out-Null
            Start-Sleep -Seconds $IntervalSec
            continue
        }
        
        # Step 2: Check if Claude Code process is still alive
        $proc = Get-Process -Id 660 -ErrorAction SilentlyContinue
        if (!$proc) {
            Log "Claude Code process died! Stopping monitor."
            break
        }
        
        # Step 3: Check results and decide next action
        $currentHash = Get-ResultsHash
        if ($currentHash -ne $lastResultsHash) {
            Log "Results changed (hash differs)"
            $lastResultsHash = $currentHash
            
            $next = Get-NextInstruction
            Log "Next action: $($next.action) - $($next.msg)"
            
            if ($next.action -eq 'send') {
                Start-Sleep -Seconds 5  # Wait for Claude to finish current output
                Send-Text $next.text
                if ($next.msg -match 'House02') { $script:lastInstructionSent = 'house02' }
                elseif ($next.msg -match 'House03') { $script:lastInstructionSent = 'house03' }
                elseif ($next.msg -match 'summary') { $script:lastInstructionSent = 'summary' }
            }
            elseif ($next.action -eq 'done') {
                Log "ALL DONE! GADEN experiments complete."
                # Don't break - keep monitoring for any follow-up
            }
        }
        else {
            # No change - just check for buttons periodically
            Log "No change. CPU=$([math]::Round($proc.CPU, 0))s"
        }
        
    } catch {
        Log "ERROR: $($_.Exception.Message)"
    }
    
    Start-Sleep -Seconds $IntervalSec
}

