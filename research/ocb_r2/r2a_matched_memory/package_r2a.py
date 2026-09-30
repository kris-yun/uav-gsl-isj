#!/usr/bin/env python3
"""Package R2A common-window evidence and frozen input tensors."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
R0 = ROOT/'evidence/ocb_r2/mechanism_census_r0'
R2 = ROOT/'evidence/ocb_r2/r2_broad_memory_path'
R2A = ROOT/'evidence/ocb_r2/r2a_matched_memory'
DEST = ROOT/'_staging/OCB_R2_R2A_MATCHED_WINDOW_REVIEW_20260930.zip'
files = [ROOT/'research/ocb_r2/R2A_MATCHED_WINDOW_MEMORY_AUDIT_20260930.md',
         ROOT/'research/ocb_r2/r2a_matched_memory/R2A_PROTOCOL_FROZEN.md',
         ROOT/'research/ocb_r2/r2a_matched_memory/R2A_DECISION_REPORT.md',
         ROOT/'research/ocb_r2/r2a_matched_memory/run_r2a.py',
         ROOT/'research/ocb_r2/r2a_matched_memory/finalize_r2a.py',
         ROOT/'research/ocb_r2/mz_memory_probe_20260930/run_mz_exploratory_probe.py',
         ROOT/'research/ocb_r2/mechanism_census_r0/run_census.py',
         ROOT/'research/ocb_r2/r2_broad_memory_path/run_r2.py',
         R0/'R0_INPUT_HASHES.json', R0/'R0_TARGET_EFFECTS.tsv',
         R2/'R2_INPUT_PARITY.json', R2/'R2_DETERMINISTIC_REPEAT.json',
         R2/'R2_GATE_RESULTS.json']
files += sorted((R0/'inputs').glob('*.pooled.npy'))
files += sorted(p for p in R2A.iterdir() if p.is_file())
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
