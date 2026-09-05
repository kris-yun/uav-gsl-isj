param([switch]$Stage, [switch]$Verify)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repo
$manifestRel = 'evidence/ctpi_v2_archive_20260906/MANIFEST.json'
$manifestPath = Join-Path $repo $manifestRel

if ($Verify) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.included) {
        $actual = (Get-FileHash -LiteralPath (Join-Path $repo $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $entry.sha256) { throw "HASH_MISMATCH: $($entry.path)" }
    }
    Write-Output "ARCHIVE_HASH_VERIFY_PASS count=$($manifest.included.Count)"
    exit 0
}

function Is-InScope([string]$p) {
    return ($p -eq '.gitattributes' -or
        $p -match '^docs/CTPI_(V2_|M12_|ONLINE_CORE_V2_|R4_FAILURE_ATTRIBUTION_)' -or
        $p -match '^closed_loop/ctpi/ctpi_v2_' -or
        $p -match '^experiments/cg_pc_ctt/ctpi_v2_' -or
        $p -match '^ros2_package/src/gsl_server/algorithms/PMFS/CTPI.*V2\.hpp$' -or
        $p -match '^tools/.*ctpi_(v2|online_core_v2|r4)' -or
        $p -eq 'tools/probe_ctpi_m2_step_contract.py' -or
        $p -match '^evidence/ctpi_(v2_.*_2026090[56]|online_core_v2_20260905|r4_failure_attribution_20260905)/' -or
        $p -match '^ideaspark_run/(causal-source-identifiability-v2|ctpi-m3-after-h2-nogo(_2)?)/')
}
function Exclusion([string]$p) {
    if ($p -match '\.bundle$') { return 'Duplicate git transport bundle; original retained locally' }
    if ($p -match '^ideaspark_run/') {
        if ($p -match '/fulltext/' -or $p -match '/fulltext_cache\.json$') {
            return 'Third-party full-text cache; no redistribution clearance'
        }
        if ($p -match '/closest_abstracts\.json$' -or
            ($p -match '/phase0/.*\.json$') -or
            ($p -match '/phase3_collision/.*(hits|collision)(\.full)?\.json$')) {
            return 'Raw retrieval or abstract cache; authored decisions and citations published instead'
        }
    }
    return ''
}

# Include already committed paths when the manifest is regenerated later.
$candidates = @(& git -c core.quotepath=false ls-files --cached --others --exclude-standard) | Sort-Object -Unique
if ($LASTEXITCODE -ne 0) { throw 'git inventory failed' }
$included = @()
$excluded = @()
foreach ($p in $candidates) {
    if ($p -eq $manifestRel) { continue }
    if (-not (Is-InScope $p) -and $p -notmatch '^ctpi_g2_m12_seed12_.*\.bundle$') { continue }
    $reason = Exclusion $p
    $file = Get-Item -LiteralPath (Join-Path $repo $p)
    $entry = [ordered]@{path=$p; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    if ($reason) { $entry.reason=$reason; $excluded += [pscustomobject]$entry; continue }
    if ($file.Length -ge 100MB) { throw "GITHUB_OVERSIZE: $p" }
    $included += [pscustomobject]$entry
}
$manifest = [ordered]@{
    schema='ctpi-exploration-archive-v1'
    scope_dates=@('2026-09-05','2026-09-06')
    base_head='46b33b66f884baa4fb6cacc75429f233852fd58f'
    branch='g2-bankfree-closedloop-20260904'
    status='ARCHIVED_EXPLORATION_NOT_M1_M2_CLOSED_LOOP_PASS'
    hash_semantics='SHA256 of exact payload bytes; scoped -text attributes preserve these on checkout; manifest excludes itself'
    included=$included
    retained_locally_not_published=$excluded
}
New-Item -ItemType Directory -Path (Split-Path $manifestPath) -Force | Out-Null
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
Write-Output "ARCHIVE_MANIFEST included=$($included.Count) excluded=$($excluded.Count) bytes=$(($included | Measure-Object bytes -Sum).Sum)"
if ($Stage) {
    foreach ($entry in $included) {
        & git add -- $entry.path
        if ($LASTEXITCODE -ne 0) { throw "STAGE_FAILED: $($entry.path)" }
    }
    & git add -- $manifestRel
    if ($LASTEXITCODE -ne 0) { throw 'MANIFEST_STAGE_FAILED' }
}
