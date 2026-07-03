$outDir = "D:\ZYC\A-gas\experiments\official_baselines\ablation"
$statusFile = "D:\ZYC\A-gas\automation\results\ablation_status.txt"

while ($true) {
    $ts = Get-Date -Format "HH:mm:ss"
    $claudeProc = Get-Process claude -ErrorAction SilentlyContinue
    
    $csvs = Get-ChildItem $outDir -Filter "ablation_*.csv" -ErrorAction SilentlyContinue
    $alphas = Get-ChildItem $outDir -Filter "alpha_*.csv" -ErrorAction SilentlyContinue
    $report = Test-Path "$outDir\ablation_analysis.md"
    
    $status = @"
[$ts] Claude: $(if($claudeProc){'running'}else{'STOPPED'})
Ablation: $($csvs.Count)/24 | Alpha: $($alphas.Count)/10 | Report: $report
Latest: $(($csvs + $alphas | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name)
"@
    
    $status | Out-File $statusFile -Encoding utf8
    
    # If Claude stopped or all done, write DONE marker
    if (-not $claudeProc -or ($csvs.Count -ge 24 -and $alphas.Count -ge 10) -or $report) {
        "DONE at $ts" | Out-File "$outDir\._watchdog_done" -Encoding utf8
        break
    }
    
    Start-Sleep -Seconds 180
}
