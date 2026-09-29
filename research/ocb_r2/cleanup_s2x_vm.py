#!/usr/bin/env python3
"""Remove one S2X raw leaf only after complete host copy and hash proof."""
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, '/home/zyc/ocb_r2_s1_tools')
import run_s1_vm as s1

ROOT = Path('/home/zyc/ocb_r2_s2x_matched_source')

def main(run_id):
    assert run_id in {f'ocb_r2_s2x_x{c:02d}_r{r:02d}' for c in range(8) for r in range(1, 5)}
    assert ROOT.resolve() == ROOT
    leaf = ROOT / run_id
    assert leaf.parent.resolve() == ROOT and leaf.is_dir() and not leaf.is_symlink()
    proof = json.loads((ROOT / f'{run_id}.ARCHIVE_PROOF.json').read_text(encoding='utf-8-sig'))
    assert proof['run_id'] == run_id and proof['result'] == 'HASH_AFTER_COPY_PASS'
    assert proof['file_count'] == 1817
    assert proof['archive_path'] == f'C:\\GADEN_OCB_R2_ARCHIVE\\s2x_matched_source\\{run_id}'
    inventory = ROOT / f'{run_id}.FULL_SHA256SUMS.txt'
    assert s1.sha(inventory) == proof['inventory_sha256']
    files = [p for p in leaf.rglob('*') if p.is_file()]
    assert len(files) == 1817 and not any(p.is_symlink() for p in leaf.rglob('*'))
    before = shutil.disk_usage(ROOT).free
    shutil.rmtree(leaf)
    after = shutil.disk_usage(ROOT).free
    report = {'run_id': run_id, 'deleted_raw_leaf': str(leaf), 'archive_path': proof['archive_path'],
              'archive_inventory_sha256': proof['inventory_sha256'], 'file_count': len(files),
              'free_before_bytes': before, 'free_after_bytes': after, 'freed_bytes': after - before}
    (ROOT / f'{run_id}.VM_CLEANUP.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
