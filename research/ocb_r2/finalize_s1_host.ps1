$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$base = Join-Path $repo 'evidence/ocb_r2'
$runEvidence = Join-Path $base 's1_runs'
$runlist = @(Import-Csv -Delimiter "`t" -LiteralPath (Join-Path $base 'OCB_R2_S1_RUNLIST_8.tsv'))
$h03 = @(Import-Csv -Delimiter "`t" -LiteralPath (Join-Path $base 'H03_SEALED_STATIC_READINESS.tsv'))
$expectedBinary = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
if ($runlist.Count -ne 8 -or $h03.Count -ne 4) { throw 'Runlist or H03 static audit count differs' }
if (@($h03 | Where-Object status -ne 'SEALED_NOT_RUN').Count) { throw 'H03 seal status differs' }
$out = @()
foreach ($run in $runlist) {
    $id = $run.run_id
    $qc = Get-Content -LiteralPath (Join-Path $runEvidence "$id.QC.json") -Raw | ConvertFrom-Json
    $manifest = Get-Content -LiteralPath (Join-Path $runEvidence "$id.RUN_MANIFEST.json") -Raw | ConvertFrom-Json
    $proof = Get-Content -LiteralPath (Join-Path $runEvidence "$id.ARCHIVE_PROOF.json") -Raw | ConvertFrom-Json
    $cleanup = Get-Content -LiteralPath (Join-Path $runEvidence "$id.VM_CLEANUP.json") -Raw | ConvertFrom-Json
    $inventoryPath = Join-Path $runEvidence "$id.FULL_SHA256SUMS.txt"
    $inventoryLines = @(Get-Content -LiteralPath $inventoryPath)
    $inventorySha = (Get-FileHash -Algorithm SHA256 -LiteralPath $inventoryPath).Hash.ToLowerInvariant()
    $archive = "C:\GADEN_OCB_R2_ARCHIVE\s1\$id"
    $archiveCount = @(Get-ChildItem -LiteralPath $archive -File -Recurse).Count
    $timeline = Join-Path $runEvidence "$id.RECORD_TIMELINE.tsv"
    $timelineSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $timeline).Hash.ToLowerInvariant()
    $sourceRunCount = @(Import-Csv -Delimiter "`t" -LiteralPath (Join-Path $runEvidence "$id.OUTPUT_SHA256SUMS.tsv")).Count
    $binaryPass = $qc.binary_sha256 -eq $expectedBinary -and $manifest.generator_binary_sha256 -eq $expectedBinary
    $recordPass = $qc.record_count -eq 1803 -and $qc.output_file_count -eq 1803 -and $sourceRunCount -eq 1803 -and $qc.first_time_s -eq 0 -and $qc.last_time_s -eq 999.502991 -and $qc.timeline_sha256 -eq $timelineSha
    $assetPass = $qc.launch_sha256 -eq $run.original_launch_sha256 -and $qc.occupancy_sha256 -eq $manifest.asset_checks.occupancy_sha256 -and $qc.wind_bundle_sha256 -eq $manifest.asset_checks.wind_bundle_sha256 -and $qc.wind_conversion_manifest_sha256 -eq $manifest.asset_checks.wind_conversion_manifest_sha256
    $provenancePass = $manifest.master_seed -eq [int]$run.master_seed -and $manifest.run_id -eq $id -and $manifest.house -eq $run.house -and $manifest.omp_num_threads -eq 1 -and $manifest.frozen_runlist_sha256 -eq '772317518c0ceb5736417cd66b34825ab255f4c689d1a724c1254fc8a4bd8b56'
    $archivePass = $proof.result -eq 'HASH_AFTER_COPY_PASS' -and $proof.file_count -eq 1817 -and $proof.inventory_sha256 -eq $inventorySha -and $proof.archive_path -eq $archive -and $cleanup.archive_inventory_sha256 -eq $inventorySha -and $archiveCount -eq 1817 -and $inventoryLines.Count -eq 1817
    $sanityPass = $qc.scientific_sanity_pass -and $qc.nonempty_filament_records -gt 0 -and $qc.max_finite_filament_center_ppm -gt 0
    $allPass = $qc.decision -eq 'PASS' -and $binaryPass -and $recordPass -and $assetPass -and $provenancePass -and $archivePass -and $sanityPass
    if (-not $allPass) { throw "Final gate failed for $id binary=$binaryPass record=$recordPass asset=$assetPass provenance=$provenancePass archive=$archivePass sanity=$sanityPass" }
    $out += [pscustomobject][ordered]@{
        run_id = $id
        house = $run.house
        source_id = $run.source_id
        wind_id = $run.wind_id
        master_seed = $run.master_seed
        record_count = $qc.record_count
        first_time_s = $qc.first_time_s
        last_time_s = $qc.last_time_s
        wind_states_used = ($qc.wind_states_used -join ',')
        output_file_count = $qc.output_file_count
        frozen_binary = if($binaryPass){'PASS'}else{'FAIL'}
        record_contract = if($recordPass){'PASS'}else{'FAIL'}
        asset_contract = if($assetPass){'PASS'}else{'FAIL'}
        provenance_contract = if($provenancePass){'PASS'}else{'FAIL'}
        scientific_sanity = if($sanityPass){'PASS'}else{'FAIL'}
        archive_hash_after_copy = if($archivePass){'PASS'}else{'FAIL'}
        decision = 'PASS'
    }
}
$out | Export-Csv -Delimiter "`t" -NoTypeInformation -LiteralPath (Join-Path $base 'OCB_R2_S1_STRUCTURAL_SMOKE_RESULTS.tsv')
$report = @"
# OCB-R2 S1 H01/H02 structural smoke result

Decision: **OCB_R2_S1_H12_STRUCTURAL_PASS**.

- Frozen generator binary SHA256: $expectedBinary
- S1 runlist frozen in commit `2e4c8b7a4bcb82db66fd5361a80015c1858a68ff` before the first S1 plume.
- H01 4/4, H02 4/4 configurations passed; all 8/8 passed record, asset, provenance and minimal scientific sanity checks.
- Each configuration produced 1803 native records, from 0 to 999.502991 s, with all 11 wind states represented. Wind transition sequence was checked independently for each configuration; no cross-House equality assumption was used.
- The first native record is empty; the remaining 1802 have parseable, finite, nonempty filament states and finite positive filament-center concentration values. This is only a structural output sanity check, not a localization or method result.
- Each 1817-file raw run was copied to C:\GADEN_OCB_R2_ARCHIVE\s1, all copied files were checked against its VM SHA256 inventory, and only then was the VM raw leaf removed. VM logs, manifests, timelines, QC and inventories remain in the evidence directory.
- House03 status: **SEALED_NOT_RUN**. Its four configurations received static launch/input/hash auditing only. No House03 prospective plume was generated or opened.

This phase does not authorize remaining H01/H02 seeds, House03, PMFS, source ranking, or any main-innovation analysis. The generator remains benchmark-frozen; binary changes require new A(S1) -> B(S2) -> C(S1) qualification.

Detailed per-run checks are in evidence/ocb_r2/OCB_R2_S1_STRUCTURAL_SMOKE_RESULTS.tsv and the eight QC/manifests in evidence/ocb_r2/s1_runs/.
"@
$report | Set-Content -LiteralPath (Join-Path $repo 'research/ocb_r2/OCB_R2_S1_STRUCTURAL_SMOKE_REPORT.md') -Encoding utf8
Write-Output "OCB_R2_S1_H12_STRUCTURAL_PASS 8/8"
