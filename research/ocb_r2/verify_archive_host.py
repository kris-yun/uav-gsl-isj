#!/usr/bin/env python3
"""Verify a Windows qualification archive against VM-side full SHA inventory."""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import sys


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit('usage: verify_archive_host.py ARCHIVE_ROOT VM_INVENTORY OUTPUT_TSV')
    root, inventory, output = map(Path, sys.argv[1:])
    assert root.resolve().is_dir()
    lines = inventory.read_text().splitlines()
    counts = Counter()
    checked = set()
    for line in lines:
        digest, rel = line.split('  ', 1)
        assert rel.startswith(('RUN_A/', 'RUN_B/', 'RUN_C/'))
        path = root / rel
        assert path.resolve().is_relative_to(root.resolve())
        assert path.is_file(), f'missing: {path}'
        assert sha(path) == digest, f'hash mismatch: {path}'
        checked.add(rel)
        counts[rel.split('/', 1)[0]] += 1
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == checked, f'file-set difference: {len(actual)} vs {len(checked)}'
    assert sum(counts.values()) == len(lines) == 5451
    for arm in 'ABC':
        assert counts[f'RUN_{arm}'] == 1817
    inventory_sha = sha(inventory)
    with output.open('w', newline='') as f:
        f.write('arm\tvm_source\tarchive_path\tfile_count\tfull_copy_inventory_sha256\tresult\n')
        for arm in 'ABC':
            f.write(f'RUN_{arm}\t/home/zyc/ocb_r2_validation/RUN_{arm}\t{root / f"RUN_{arm}"}\t{counts[f"RUN_{arm}"]}\t{inventory_sha}\tHASH_AFTER_COPY_PASS\n')
    print(f'archive verified: {len(lines)} files; inventory_sha256={inventory_sha}')


if __name__ == '__main__':
    main()
