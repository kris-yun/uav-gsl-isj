param(
  [string]$TaskName = 'A-gas Automation Monitor',
  [int]$RepeatMinutes = 15
)

$ErrorActionPreference = 'Stop'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"D:\ZYC\A-gas\automation\monitor\run.ps1`" -Mode all"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes $RepeatMinutes)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Monitors automation results and emits corrective instructions.' -Force
Write-Host "Scheduled task '$TaskName' registered (every $RepeatMinutes minutes)."
