# Smart terminal interaction: check first, only toggle if needed
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinSmart {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$handle = [IntPtr]2497872

function Get-TerminalEdits {
    $root = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
    $editCondition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Edit)
    return $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCondition)
}

function Focus-VSCode {
    [WinSmart]::ShowWindow($handle, 9) | Out-Null
    [WinSmart]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Milliseconds 400
}

# Step 1: Focus VS Code
Focus-VSCode

# Step 2: Check if terminal is ALREADY open
$edits = Get-TerminalEdits
$terminalOpen = $false
foreach ($edit in $edits) {
    if ($edit.Current.Name -match '终端') { $terminalOpen = $true; break }
}

# Step 3: Only toggle if NOT open
if (-not $terminalOpen) {
    Write-Host "Terminal closed, opening with Ctrl+`..."
    [System.Windows.Forms.SendKeys]::SendWait('^`')
    Start-Sleep -Milliseconds 800
} else {
    Write-Host "Terminal already open, skipping toggle."
}

# Step 4: Find terminal 12 and send Enter
$edits = Get-TerminalEdits
$sent = $false
foreach ($edit in $edits) {
    if ($edit.Current.Name -match '终端 14') {
        $edit.SetFocus()
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        $sent = $true
        Write-Host "OK: Enter sent to terminal 12"
        break
    }
}

if (-not $sent) { Write-Host "FAIL: terminal 12 not found" }

