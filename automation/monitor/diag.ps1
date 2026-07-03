$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$automationRoot = Join-Path $projectRoot 'automation'
$taskOut = 'automation/results/iter1_baseline_audit.md'
Write-Host (Join-Path $automationRoot $taskOut)
