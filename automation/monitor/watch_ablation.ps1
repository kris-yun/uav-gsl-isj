# Monitor script for Claude Code ablation experiments
# Checks every 60 seconds for new results

$watchDir = "D:\ZYC\A-gas\experiments\official_baselines\ablation"
$lastCount = 0
$checkCount = 0

while ($true) {
    $checkCount++
    $files = @()
    if (Test-Path $watchDir) {
        $files = Get-ChildItem $watchDir -Filter "*.csv" -ErrorAction SilentlyContinue
    }
    
    $currentCount = $files.Count
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    if ($currentCount -ne $lastCount) {
        Write-Host "[$timestamp] NEW FILES: $currentCount CSV files (was $lastCount)"
        foreach ($f in $files | Sort-Object LastWriteTime -Descending | Select-Object -First 5) {
            Write-Host "  - $($f.Name) ($($f.Length) bytes, $($f.LastWriteTime))"
        }
        $lastCount = $currentCount
    } else {
        Write-Host "[$timestamp] Check #$checkCount : $currentCount CSV files (no change)"
    }
    
    # Also check if Claude process is still running
    $claudeProc = Get-Process claude -ErrorAction SilentlyContinue
    if (-not $claudeProc) {
        Write-Host "[$timestamp] WARNING: Claude process not found! May have finished or crashed."
    }
    
    # Check for ablation analysis report
    $reportPath = Join-Path $watchDir "ablation_analysis.md"
    if (Test-Path $reportPath) {
        $reportAge = (Get-Date) - (Get-Item $reportPath).LastWriteTime
        if ($reportAge.TotalMinutes -lt 2) {
            Write-Host "[$timestamp] ANALYSIS REPORT FOUND: $reportPath"
        }
    }
    
    Start-Sleep -Seconds 60
}
