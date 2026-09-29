$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$runlist = @(Import-Csv -Delimiter "`t" -LiteralPath (Join-Path $repo 'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'))
if ($runlist.Count -ne 32) { throw 'Frozen runlist is not 32 rows' }
$archiveScript = Join-Path $PSScriptRoot 'archive_s2_host.ps1'
$evidence = Join-Path $repo 'evidence/ocb_r2/s2_runs'
foreach ($row in $runlist) {
    $id = $row.run_id
    if ($row.phase -ne 'DISCOVERY' -or $row.house -notin @('House01','House02')) {
        throw "Unauthorized runlist row: $id"
    }
    $proofPath = Join-Path $evidence "$id.ARCHIVE_PROOF.json"
    $cleanupPath = Join-Path $evidence "$id.VM_CLEANUP.json"
    if ((Test-Path -LiteralPath $proofPath) -and (Test-Path -LiteralPath $cleanupPath)) {
        $proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
        $cleanup = Get-Content -LiteralPath $cleanupPath -Raw | ConvertFrom-Json
        if ($proof.result -ne 'HASH_AFTER_COPY_PASS' -or $proof.file_count -ne 1817 -or
            $cleanup.archive_inventory_sha256 -ne $proof.inventory_sha256) {
            throw "Invalid completed-run proof: $id"
        }
        Write-Output "ALREADY_ARCHIVED $id"
        continue
    }
    if ((Test-Path -LiteralPath $proofPath) -or (Test-Path -LiteralPath $cleanupPath)) {
        throw "Partial archive/cleanup state needs audit: $id"
    }
    & $archiveScript -RunId $id -RunSimulator
    if ($LASTEXITCODE -ne 0) { throw "Archive script failed: $id" }
}
Write-Output 'S2_DISCOVERY_CAMPAIGN_ARCHIVE_COMPLETE 32/32'
