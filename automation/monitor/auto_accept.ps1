param(
  [int]$CheckIntervalSeconds = 30,
  [string]$ResultsDir = 'D:\ZYC\A-gas\automation\results'
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinApi50 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$script:lastResultHash = ''
$vscodeHandle = [IntPtr]2497872

function Focus-VSCode {
    [WinApi50]::ShowWindow($vscodeHandle, 9) | Out-Null
    [WinApi50]::SetForegroundWindow($vscodeHandle) | Out-Null
    Start-Sleep -Milliseconds 400
}

function Get-TerminalEdits {
    try {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($vscodeHandle)
        $editCondition = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::Edit)
        return $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCondition)
    } catch { return @() }
}

function Ensure-TerminalOpen {
    $edits = Get-TerminalEdits
    $open = $false
    foreach ($edit in $edits) {
        if ($edit.Current.Name -match '终端') { $open = $true; break }
    }
    if (-not $open) {
        Focus-VSCode
        [System.Windows.Forms.SendKeys]::SendWait('^`')
        Start-Sleep -Milliseconds 800
    }
}

function Find-Terminal12 {
    $edits = Get-TerminalEdits
    foreach ($edit in $edits) {
        if ($edit.Current.Name -match '终端 14') { return $edit }
    }
    return $null
}

function Send-EnterToTerminal {
    $term = Find-Terminal12
    if ($term) {
        Focus-VSCode
        $term.SetFocus()
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        return $true
    }
    return $false
}

function Send-TextToTerminal($text) {
    $term = Find-Terminal12
    if ($term) {
        Focus-VSCode
        $term.SetFocus()
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.Clipboard]::SetText($text)
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('^v')
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        return $true
    }
    return $false
}

function Get-ResultsHash {
    if (!(Test-Path $ResultsDir)) { return '' }
    $files = Get-ChildItem $ResultsDir -File | Sort-Object Name | ForEach-Object { "$($_.Name):$($_.LastWriteTime.Ticks)" }
    return ($files -join '|')
}

# Ensure terminal is open at start
Ensure-TerminalOpen
Write-Host "Monitor started. Check every $CheckIntervalSeconds sec. NO toggle on send."

while ($true) {
  try {
    # Ensure terminal is visible (but don't toggle if already open)
    Ensure-TerminalOpen

    # Rule 1: Check for confirmation button
    $btn = $null
    try {
      $root = [System.Windows.Automation.AutomationElement]::FromHandle($vscodeHandle)
      $btnCondition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Button)
      $buttons = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCondition)
      foreach ($b in $buttons) {
        if ($b.Current.Name -match '(?i)^(yes|allow|approve|continue|ok|run|accept|confirm)$') {
          $btn = $b; break
        }
      }
    } catch {}

    if ($btn) {
      Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Button '$($btn.Current.Name)' -> Enter"
      Send-EnterToTerminal | Out-Null
      Start-Sleep -Seconds $CheckIntervalSeconds
      continue
    }

    # Rule 2: Results changed
    $currentHash = Get-ResultsHash
    if ($currentHash -ne $script:lastResultHash -and $script:lastResultHash -ne '') {
      Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Results changed, reviewing..."
      $script:lastResultHash = $currentHash
      $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"D:\ZYC\A-gas\automation\monitor\run.ps1`" -Mode all" -PassThru -NoNewWindow -Wait
      if ($proc.ExitCode -ne 0) {
        $latest = Get-ChildItem 'D:\ZYC\A-gas\automation\reviews\auto_instruction_*.md' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
          Write-Host "  -> Sending instruction: $($latest.Name)"
          Send-TextToTerminal (Get-Content $latest.FullName -Raw)
        }
      } else {
        Write-Host "  -> All checks passed."
      }
    } else {
      $script:lastResultHash = $currentHash
    }

  } catch {
    Write-Host "Error: $($_.Exception.Message)"
  }

  Start-Sleep -Seconds $CheckIntervalSeconds
}

