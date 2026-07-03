param(
  [ValidateSet('audit','all')]
  [string]$Mode = 'audit'
)

$ErrorActionPreference = 'Stop'
$automationRoot = 'D:\ZYC\A-gas\automation'
$results = Join-Path $automationRoot 'results'
$reviews = Join-Path $automationRoot 'reviews'
$manifest = Join-Path $automationRoot 'monitor\manifest.json'

if (!(Test-Path $manifest)) {
  Write-Error "Manifest not found: $manifest"
  exit 1
}

$cfg = Get-Content $manifest -Raw | ConvertFrom-Json

function Assert-Contains {
  param([string]$Path,[string[]]$Patterns,[string]$Task)
  if (!(Test-Path $Path)) { throw "$Task failed: missing $Path" }
  $content = Get-Content $Path -Raw
  foreach ($p in $Patterns) {
    if ($content -notmatch $p) { throw "$Task failed: missing pattern '$p' in $Path" }
  }
}

function Run-Task {
  param($Task)
  $out = Join-Path $automationRoot $Task.output
  if (!(Test-Path $out)) { throw "$($Task.name) failed: missing $out" }
  if ($Task.required_patterns) {
    Assert-Contains -Path $out -Patterns $Task.required_patterns -Task $Task.name
  }
  foreach ($rel in $Task.required_files) {
    $full = Join-Path $automationRoot $rel
    if (!(Test-Path $full)) { throw "$($Task.name) failed: missing $full" }
  }
  Write-Host "[PASS] $($Task.name)"
}

function Run-FinalGate {
  $gate = $cfg.final_gate
  $csv = Join-Path $automationRoot $gate.comparison_csv
  if (!(Test-Path $csv)) { throw "final_gate failed: missing $csv" }
  $summary = Join-Path $automationRoot $gate.summary_output
  if (!(Test-Path $summary)) { throw "final_gate failed: missing $summary" }
  $content = Get-Content $summary -Raw
  if ($content -notmatch 'PASS') { throw "final_gate failed: summary not marked PASS in $summary" }
  Write-Host "[PASS] final_gate"
}

if ($Mode -eq 'audit') {
  try {
    $task = $cfg.tasks | Where-Object { $_.name -eq 'audit' }
    Run-Task -Task $task
  } catch {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $file = Join-Path $reviews "auto_instruction_$ts.md"
    $instruction = @"
# Auto Instruction

Task: audit
Status: FAIL
Reason: $($_.Exception.Message)

## Required fixes
- Ensure official baselines are used where appropriate.
- Verify SurgeCast, Infotaxis, and KLD alignment with official/paper logic.
- Re-run baseline audit and overwrite automation/results/iter1_baseline_audit.md.

## Acceptance criteria
- File exists: automation/results/iter1_baseline_audit.md
- Contains sections: SurgeCast, Infotaxis, KLD
- Contains official repo references for comparison
"@
    Set-Content $file $instruction -Encoding UTF8
    Write-Host "[FAIL] audit -> $file"
    exit 2
  }
}

if ($Mode -eq 'all') {
  foreach ($task in $cfg.tasks) {
    try {
      Run-Task -Task $task
    } catch {
      $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
      $file = Join-Path $reviews "auto_instruction_$ts.md"
      $instruction = @"
# Auto Instruction

Task: $($task.name)
Status: FAIL
Reason: $($_.Exception.Message)

## Required fixes
- Complete this task exactly to the acceptance criteria before moving to the next task.
- Provide clear evidence in the task output file.
- Ensure required code files exist and tests pass.

## Acceptance criteria
- Output file exists: $($task.output)
- Required patterns: $($task.required_patterns -join ', ')
- Required files: $($task.required_files -join ', ')
"@
      Set-Content $file $instruction -Encoding UTF8
      Write-Host "[FAIL] $($task.name) -> $file"
      exit 2
    }
  }

  try {
    Run-FinalGate
  } catch {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $file = Join-Path $reviews "auto_instruction_$ts.md"
    $instruction = @"
# Auto Instruction

Task: final_gate
Status: FAIL
Reason: $($_.Exception.Message)

## Required fixes
- Ensure 3 cross-domain innovations are implemented and documented.
- Provide comparison CSV with metrics.
- Provide final_gate summary that explicitly shows PASS and improvement analysis.

## Acceptance criteria
- File exists: automation/results/iter6_comparison.csv
- File exists: automation/results/final_gate.md
- final_gate.md contains the word PASS
"@
    Set-Content $file $instruction -Encoding UTF8
    Write-Host "[FAIL] final_gate -> $file"
    exit 2
  }
}
