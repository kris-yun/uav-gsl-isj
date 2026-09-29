#!/usr/bin/env python3
"""Remove exactly three VM qualification raw directories after C: hash proof."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('/home/zyc/ocb_r2_validation')
EXPECTED_INVENTORY_SHA = '70a1bb8b9fb9c5ed3f2af831ecee8b695922525ad3530698b5000208136320e0'


def main():
    assert ROOT.resolve() == ROOT
    proof = ROOT / 'QUALIFICATION_ARCHIVE_TRANSFER.tsv'
    with proof.open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(rows) == 3
    assert {row['arm'] for row in rows} == {'RUN_A', 'RUN_B', 'RUN_C'}
    inventory = ROOT / 'QUALIFICATION_FULL_COPY_SHA256SUMS.txt'
    assert hashlib.sha256(inventory.read_bytes()).hexdigest() == EXPECTED_INVENTORY_SHA
    for row in rows:
        assert row['result'] == 'HASH_AFTER_COPY_PASS'
        assert row['full_copy_inventory_sha256'] == EXPECTED_INVENTORY_SHA
        assert int(row['file_count']) == 1817
        assert row['vm_source'] == str(ROOT / row['arm'])
        assert row['archive_path'].startswith('C:\\GADEN_OCB_R2_ARCHIVE\\qualification\\RUN_')
    paths = [ROOT / f'RUN_{arm}' for arm in 'ABC']
    for p in paths:
        assert p.parent.resolve() == ROOT and p.is_dir() and not p.is_symlink()
        assert len([f for f in p.rglob('*') if f.is_file()]) == 1817
    before = shutil.disk_usage(ROOT).free
    for p in paths:
        shutil.rmtree(p)
    after = shutil.disk_usage(ROOT).free
    result = {'deleted_paths': [str(p) for p in paths], 'archive_proof_inventory_sha256': EXPECTED_INVENTORY_SHA,
              'free_before_bytes': before, 'free_after_bytes': after, 'freed_bytes': after-before}
    (ROOT / 'QUALIFICATION_VM_CLEANUP.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
