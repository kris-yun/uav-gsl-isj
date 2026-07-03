param(
  [Parameter(Mandatory=$true)]
  [string]$InstructionFile,
  [string]$WindowTitleFragment = 'Claude Code'
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinApi {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

if (!(Test-Path $InstructionFile)) {
  Write-Error "Instruction file not found: $InstructionFile"
  exit 1
}

$content = Get-Content $InstructionFile -Raw
$task = 'unknown'
if ($content -match 'Task:\s*(.+?)\r?\n') { $task = $matches[1].Trim() }

$vscode = Get-Process -Name 'Code' -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$WindowTitleFragment*" } |
  Select-Object -First 1

if (-not $vscode) {
  $vscode = Get-Process -Name 'Code' -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object -First 1
}

if (-not $vscode) {
  Start-Process 'code' -ArgumentList '"' + 'D:\ZYC\A-gas' + '"' | Out-Null
  Start-Sleep -Seconds 5
  $vscode = Get-Process -Name 'Code' -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$WindowTitleFragment*" } |
    Select-Object -First 1
  if (-not $vscode) {
    $vscode = Get-Process -Name 'Code' -ErrorAction SilentlyContinue |
      Where-Object { $_.MainWindowHandle -ne 0 } |
      Select-Object -First 1
  }
}

if (-not $vscode) {
  Write-Error "VS Code main window not found."
  exit 1
}

$hwnd = $vscode.MainWindowHandle
[WinApi]::ShowWindow($hwnd, 9) | Out-Null
[WinApi]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 350

# Open Chat and focus input (VS Code default shortcuts)
[System.Windows.Forms.SendKeys]::SendWait('^%c')
Start-Sleep -Milliseconds 450
[System.Windows.Forms.SendKeys]::SendWait('^l')
Start-Sleep -Milliseconds 250

# Paste instruction
Set-Clipboard -Value $content
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')

Write-Host "Handoff sent to VS Code for task: $task"
