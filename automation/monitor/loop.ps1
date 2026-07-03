param(
  [int]$IntervalSeconds = 900
)

$ErrorActionPreference = 'Stop'
$monitor = 'D:\ZYC\A-gas\automation\monitor'
$run = Join-Path $monitor 'run.ps1'
$handoff = Join-Path $monitor 'computer_handoff.ps1'

Write-Host "Automation loop started (every $IntervalSeconds seconds)."

while ($true) {
  $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  Write-Host "`n[$ts] Running task checks..."
  $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$run`" -Mode all" -PassThru -NoNewWindow -Wait
  $exit = $proc.ExitCode
  Write-Host "Check exit code: $exit"

  if ($exit -ne 0) {
    $latest = Get-ChildItem 'D:\ZYC\A-gas\automation\reviews\auto_instruction_*.md' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
      Write-Host "Handoff to VS Code right-side Claude Code..."
      Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$handoff`" -InstructionFile `"$($latest.FullName)`"" -NoNewWindow -Wait
    } else {
      Write-Host "No instruction file found for handoff."
    }
  } else {
    Write-Host "All current gates passed."
  }

  Start-Sleep -Seconds $IntervalSeconds
}
