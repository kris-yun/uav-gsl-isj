param(
  [string[]]$Paths = @('D:\ZYC\A-gas\workspace\uav_diagsense\src','D:\ZYC\A-gas\workspace\uav_diagsense\automation\results'),
  [int]$DebounceSeconds = 5
)

$ErrorActionPreference = 'Stop'
$lastRun = Get-Date '1900-01-01'
$run = Join-Path $PSScriptRoot 'run.ps1'

$watchers = @()
foreach ($p in $Paths) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
  $fsw = New-Object System.IO.FileSystemWatcher
  $fsw.Path = $p
  $fsw.IncludeSubdirectories = $true
  $fsw.EnableRaisingEvents = $false
  $watchers += $fsw
  Write-Host "Watching $p ..."
}

while ($true) {
  $changed = $false
  foreach ($fsw in $watchers) {
    $res = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::All, 500)
    if (!$res.TimedOut) { $changed = $true; break }
  }
  if (!$changed) { continue }
  if ((Get-Date) - $lastRun -lt [TimeSpan]::FromSeconds($DebounceSeconds)) { continue }
  $lastRun = Get-Date
  Write-Host 'Change detected, running checks...'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $run -Mode all
}
