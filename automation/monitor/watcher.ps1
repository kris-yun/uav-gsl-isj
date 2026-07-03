param(
  [string]$Path = 'D:\ZYC\A-gas\automation\results',
  [int]$DebounceSeconds = 5
)

$ErrorActionPreference = 'Stop'
$lastRun = Get-Date '1900-01-01'
$run = Join-Path $PSScriptRoot 'run.ps1'

$fsw = New-Object System.IO.FileSystemWatcher
$fsw.Path = $Path
$fsw.Filter = '*.*'
$fsw.IncludeSubdirectories = $false
$fsw.EnableRaisingEvents = $false

Write-Host "Watching $Path ..."

while ($true) {
  $result = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::All, 1000)
  if ($result.TimedOut) { continue }
  if ((Get-Date) - $lastRun -lt [TimeSpan]::FromSeconds($DebounceSeconds)) { continue }
  $lastRun = Get-Date
  Write-Host ("Change detected: {0}" -f $result.Name)
  & powershell -NoProfile -ExecutionPolicy Bypass -File $run -Mode all
}
