#!/usr/bin/env python3
"""Build the explicitly approved House02 wind staging tree without touching A/B."""

import csv
import hashlib
import json
import os
import shutil
from pathlib import Path

PLAN = Path('/home/zyc/RECONSTRUCTED_H02_WIND_STAGING_PLAN.tsv')
PARENT = Path('/home/zyc/ocb_r1_assets')
TEMP = PARENT / 'h02_wind_reconstructed.incomplete'
DEST = PARENT / 'h02_wind_reconstructed'
REPORT = PARENT / 'RECONSTRUCTED_H02_WIND_STAGING_SHA256.tsv'
A = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/wind_simulations')
B = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02/wind_simulations')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    if DEST.exists() or TEMP.exists():
        raise RuntimeError('Refusing to overwrite an existing staging directory')
    with PLAN.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    if len(rows) != 176 or {r['source_tree'] for r in rows} != {'A', 'B'}:
        raise RuntimeError('Staging plan has wrong cardinality/source set')
    if sum(r['source_tree'] == 'A' for r in rows) != 112 or sum(r['source_tree'] == 'B' for r in rows) != 64:
        raise RuntimeError('Staging plan has wrong source counts')
    if len({r['relative_path'] for r in rows}) != 176:
        raise RuntimeError('Duplicate relative path')
    PARENT.mkdir(exist_ok=True)
    TEMP.mkdir()
    verified = []
    for row in rows:
        relative = Path(row['relative_path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('Unsafe relative path')
        root = A if row['source_tree'] == 'A' else B
        source = root / relative
        if str(source) != row['source_path'] or source.is_symlink() or not source.is_file():
            raise RuntimeError(f'Source path invalid: {source}')
        if sha(source) != row['sha256']:
            raise RuntimeError(f'Source hash mismatch: {source}')
        target = TEMP / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = sha(target)
        if digest != row['sha256']:
            raise RuntimeError(f'Staging hash mismatch: {target}')
        verified.append((row['relative_path'], str(DEST / relative), target.stat().st_size,
                         digest, row['source_tree'], str(source), 'PASS'))
    os.rename(TEMP, DEST)
    with REPORT.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(('relative_path', 'staging_path', 'size_bytes', 'sha256',
                         'source_tree', 'source_path', 'verification'))
        writer.writerows(verified)
    print(json.dumps({'staging': str(DEST), 'count': len(verified),
                      'source_A': 112, 'source_B': 64,
                      'bytes': sum(row[2] for row in verified), 'report': str(REPORT)}))


if __name__ == '__main__':
    main()
