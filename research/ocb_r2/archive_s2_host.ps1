param(
    [Parameter(Mandatory=$true)][ValidatePattern('^ocb_r2_cfg0[0-7]_r0[1-4]$')][string]$RunId,
    [switch]$RunSimulator
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$evidence = Join-Path $repo 'evidence/ocb_r2/s2_runs'
$archiveRoot = 'C:\GADEN_OCB_R2_ARCHIVE\s2_discovery'
$archiveLeaf = Join-Path $archiveRoot $RunId
$remoteRoot = '/home/zyc/ocb_r2_s2_discovery'
New-Item -ItemType Directory -Force -Path $evidence,$archiveRoot | Out-Null
if (Test-Path -LiteralPath $archiveLeaf) { throw "Archive leaf exists: $archiveLeaf" }

if ($RunSimulator) {
    & ssh -o BatchMode=yes zyc@192.168.111.128 "python3 /home/zyc/ocb_r2_s2_tools/run_s2_vm.py $RunId"
    if ($LASTEXITCODE -ne 0) { throw "S2 simulator/structural QC failed: $RunId" }
}
& ssh -o BatchMode=yes zyc@192.168.111.128 "cd $remoteRoot; find $RunId -type f -print0 | sort -z | xargs -0 sha256sum > $RunId.FULL_SHA256SUMS.txt"
if ($LASTEXITCODE -ne 0) { throw "Remote inventory failed: $RunId" }
$inventory = Join-Path $evidence "$RunId.FULL_SHA256SUMS.txt"
& scp -q "zyc@192.168.111.128:$remoteRoot/$RunId.FULL_SHA256SUMS.txt" $inventory
if ($LASTEXITCODE -ne 0) { throw "Inventory transfer failed: $RunId" }
& scp -q -r "zyc@192.168.111.128:$remoteRoot/$RunId" "$archiveRoot\"
if ($LASTEXITCODE -ne 0) { throw "Raw archive transfer failed: $RunId" }
$lines = Get-Content -LiteralPath $inventory
if ($lines.Count -ne 1817) { throw "Unexpected file count for $RunId : $($lines.Count)" }
$n = 0
foreach ($line in $lines) {
    $parts = $line -split '  ', 2
    if ($parts.Count -ne 2 -or -not $parts[1].StartsWith("$RunId/")) { throw "Bad inventory path: $line" }
    $relative = $parts[1] -replace '/', '\'
    $path = Join-Path $archiveRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing archive file: $path" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw "Archive hash mismatch: $path" }
    $n++
}
$actualCount = @(Get-ChildItem -LiteralPath $archiveLeaf -File -Recurse).Count
if ($actualCount -ne $n) { throw "Archive file-set mismatch: $actualCount / $n" }
$inventorySha = (Get-FileHash -Algorithm SHA256 -LiteralPath $inventory).Hash.ToLowerInvariant()
$proof = [ordered]@{
    run_id = $RunId
    result = 'HASH_AFTER_COPY_PASS'
    file_count = $n
    archive_path = $archiveLeaf
    inventory_sha256 = $inventorySha
}
$proofPath = Join-Path $evidence "$RunId.ARCHIVE_PROOF.json"
$proof | ConvertTo-Json | Set-Content -LiteralPath $proofPath -Encoding utf8
& scp -q $proofPath "zyc@192.168.111.128:$remoteRoot/"
if ($LASTEXITCODE -ne 0) { throw "Proof transfer failed: $RunId" }
foreach ($name in @('RUN_MANIFEST.json','RECORD_TIMELINE.tsv','OUTPUT_SHA256SUMS.tsv')) {
    Copy-Item -LiteralPath (Join-Path $archiveLeaf $name) -Destination (Join-Path $evidence "$RunId.$name")
}
& scp -q "zyc@192.168.111.128:$remoteRoot/$RunId.QC.json" "zyc@192.168.111.128:$remoteRoot/$RunId.stdout.log" "$evidence\"
if ($LASTEXITCODE -ne 0) { throw "Small evidence transfer failed: $RunId" }
& ssh -o BatchMode=yes zyc@192.168.111.128 "python3 /home/zyc/ocb_r2_s2_tools/cleanup_s2_vm.py $RunId"
if ($LASTEXITCODE -ne 0) { throw "VM cleanup refused: $RunId" }
& scp -q "zyc@192.168.111.128:$remoteRoot/$RunId.VM_CLEANUP.json" "$evidence\"
if ($LASTEXITCODE -ne 0) { throw "Cleanup evidence transfer failed: $RunId" }
Write-Output "ARCHIVED_AND_VERIFIED $RunId files=$n inventory_sha256=$inventorySha"
