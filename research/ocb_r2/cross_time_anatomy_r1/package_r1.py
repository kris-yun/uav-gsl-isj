#!/usr/bin/env python3
"""Create a compact independently reviewable R1 archive with SHA256 inventory."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / '_staging/OCB_R2_R1_CROSS_TIME_MEMORY_ANATOMY_REVIEW_20260930.zip'
R0 = ROOT / 'evidence/ocb_r2/mechanism_census_r0'
R1 = ROOT / 'evidence/ocb_r2/cross_time_anatomy_r1'
files = [
    ROOT/'research/ocb_r2/OCB_R2_CROSS_TIME_MEMORY_ANATOMY_R1.md',
    ROOT/'research/ocb_r2/cross_time_anatomy_r1/R1_PROTOCOL_FROZEN.md',
    ROOT/'research/ocb_r2/cross_time_anatomy_r1/R1_DECISION_REPORT.md',
    ROOT/'research/ocb_r2/cross_time_anatomy_r1/run_r1.py',
    ROOT/'research/ocb_r2/cross_time_anatomy_r1/finalize_r1.py',
    ROOT/'research/ocb_r2/mechanism_census_r0/run_census.py',
    R0/'R0_INPUT_HASHES.json', R0/'R0_DETERMINISTIC_REPEAT.json',
    R0/'R0_MECHANISM_SUMMARY.json', R0/'R0_TARGET_EFFECTS.tsv',
]
files += sorted((R0/'inputs').glob('*.pooled.npy'))
files += sorted(p for p in R1.iterdir() if p.is_file())
assert len([p for p in files if p.name.endswith('.pooled.npy')]) == 64
assert len(files) == len(set(files))
DEST.parent.mkdir(parents=True, exist_ok=True)
lines = []
with zipfile.ZipFile(DEST, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        assert p.is_file()
        name = p.relative_to(ROOT).as_posix()
        data = p.read_bytes()
        lines.append(f'{hashlib.sha256(data).hexdigest()}  {name}')
        zi = zipfile.ZipInfo(name, (2026, 9, 30, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    zi = zipfile.ZipInfo('SHA256SUMS', (2026, 9, 30, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zi, ('\n'.join(lines)+'\n').encode(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
with zipfile.ZipFile(DEST) as z:
    for line in z.read('SHA256SUMS').decode().splitlines():
        digest, name = line.split('  ', 1)
        assert hashlib.sha256(z.read(name)).hexdigest() == digest
print(f'{DEST}\nbytes={DEST.stat().st_size}\nsha256={hashlib.sha256(DEST.read_bytes()).hexdigest()}')
