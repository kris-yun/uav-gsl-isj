# Long-running GADEN monitor - checks every 2 minutes
param([int]$IntervalSec = 120, [int]$MaxHours = 12)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinMon2 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$handle = [IntPtr]2497872
$logFile = 'D:\ZYC\A-gas\automation\monitor\gaden_monitor.log'
$startTime = Get-Date
$lastHash = ''

function Log($msg) {
    $ts = Get-Date -Format 'HH:mm:ss'
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content $logFile $line -ErrorAction SilentlyContinue
}

function Get-Hash {
    $files = @(
        'D:\ZYC\A-gas\automation\results\iter11_gaden_house01.csv',
        'D:\ZYC\A-gas\automation\results\iter11_gaden_house02.csv',
        'D:\ZYC\A-gas\automation\results\iter11_gaden_house03.csv',
        'D:\ZYC\A-gas\automation\results\iter11_gaden_summary.md'
    )
    $parts = @()
    foreach ($f in $files) {
        if (Test-Path $f) {
            $i = Get-Item $f
            $parts += "$($i.Name):$($i.Length):$($i.LastWriteTime.Ticks)"
        }
    }
    return ($parts -join '|')
}

function Has-ConfirmButton {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
        $btnCond = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Button)
        $btns = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
        foreach ($b in $btns) {
            if ($b.Current.Name -match '(?i)^(yes|allow|approve|continue|ok|run|accept|confirm)$') {
                return $b.Current.Name
            }
        }
    } catch {}
    return $null
}

function Send-EnterToTerminal {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
        $editCond = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Edit)
        $edits = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
        foreach ($e in $edits) {
            if ($e.Current.Name -match '终端 15|Claude Code') {
                [WinMon2]::ShowWindow($handle, 9) | Out-Null
                [WinMon2]::SetForegroundWindow($handle) | Out-Null
                Start-Sleep -Milliseconds 300
                $e.SetFocus()
                Start-Sleep -Milliseconds 200
                [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
                return $true
            }
        }
    } catch {}
    return $false
}

function Check-Results {
    $h01 = 'D:\ZYC\A-gas\automation\results\iter11_gaden_house01.csv'
    $h02 = 'D:\ZYC\A-gas\automation\results\iter11_gaden_house02.csv'
    $h03 = 'D:\ZYC\A-gas\automation\results\iter11_gaden_house03.csv'
    $sum = 'D:\ZYC\A-gas\automation\results\iter11_gaden_summary.md'
    
    $status = @{ h01=0; h02=0; h03=0; sum=0 }
    if (Test-Path $h01) { $status.h01 = (Get-Content $h01 | Measure-Object).Count - 1 }
    if (Test-Path $h02) { $status.h02 = (Get-Content $h02 | Measure-Object).Count - 1 }
    if (Test-Path $h03) { $status.h03 = (Get-Content $h03 | Measure-Object).Count - 1 }
    if (Test-Path $sum) { $status.sum = 1 }
    return $status
}

Log "=== GADEN Monitor Started (interval=${IntervalSec}s, max=${MaxHours}h) ==="

while ($true) {
    $elapsed = (Get-Date) - $startTime
    if ($elapsed.TotalHours -ge $MaxHours) {
        Log "Max time reached ($MaxHours hours). Stopping."
        break
    }
    
    try {
        # Check Claude process
        $claude = Get-Process claude -ErrorAction SilentlyContinue
        if (!$claude) {
            Log "Claude process DEAD! Need restart."
            # Could auto-restart here
        }
        
        # Check for confirmation buttons
        $btn = Has-ConfirmButton
        if ($btn) {
            Log "Found button: $btn -> sending Enter"
            Send-EnterToTerminal | Out-Null
            Start-Sleep -Seconds $IntervalSec
            continue
        }
        
        # Check results
        $hash = Get-Hash
        if ($hash -ne $lastHash) {
            $lastHash = $hash
            $r = Check-Results
            Log "Results changed! H01=$($r.h01) H02=$($r.h02) H03=$($r.h03) Summary=$($r.sum)"
            
            if ($r.sum -eq 1) {
                Log "*** ALL DONE! Summary generated. ***"
                # Don't break - let user review
            }
        } else {
            # Check if python is running (experiment in progress)
            $pyProc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 1 }
            if ($pyProc) {
                $cpuSum = ($pyProc | Measure-Object CPU -Sum).Sum
                Log "Running: Claude=$([math]::Round($claude.CPU,0))s, Python(s)=$([math]::Round($cpuSum,0))s"
            } else {
                Log "Idle: Claude=$([math]::Round($claude.CPU,0))s, no python active"
            }
        }
    } catch {
        Log "ERROR: $($_.Exception.Message)"
    }
    
    Start-Sleep -Seconds $IntervalSec
}
