#!/usr/bin/env python3
"""Stage only pre-frozen OCB-R2 native snapshots for VM concentration extraction.

This script checks each native file against its original archive inventory. It
does not decode filament or concentration values. H01/H02 S2/S2X only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile


REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / 'evidence/ocb_r2/aod_r2_f0/AOD_R2_F0_TIME_MAPPING.tsv'
S2 = REPO / 'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
S2X = REPO / 'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv'
ARCHIVE = Path('C:/GADEN_OCB_R2_ARCHIVE')
OUT = REPO / '_staging/AOD_R2_F0_FROZEN_SNAPSHOTS.tar'
INVENTORY = REPO / 'evidence/ocb_r2/aod_r2_f0/AOD_R2_F0_STAGED_SNAPSHOTS.json'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    rows = read(FROZEN)
    assert len(rows) == 640 and len({r['run_id'] for r in rows}) == 64
    runs = {r['run_id']: ('s2_discovery', r['house']) for r in read(S2)}
    runs.update({r['run_id']: ('s2x_matched_source', r['house']) for r in read(S2X)})
    assert len(runs) == 64 and set(runs) == {r['run_id'] for r in rows}
    by_run = {}
    for r in rows:
        by_run.setdefault(r['run_id'], []).append(r)
    OUT.parent.mkdir(exist_ok=True)
    manifest = []
    with tarfile.open(OUT, 'w') as tar:
        for run_id in sorted(by_run):
            phase, house = runs[run_id]
            assert house in {'House01', 'House02'}
            root = ARCHIVE / phase / run_id
            hashes = {r['name']: r['sha256'] for r in read(root/'OUTPUT_SHA256SUMS.tsv')}
            records = sorted(by_run[run_id], key=lambda r: int(r['slot']))
            assert [int(r['slot']) for r in records] == list(range(1, 11))
            for r in records:
                name = f"iteration_{int(r['record_index'])}"
                path = root/name
                digest = sha(path)
                assert digest == hashes[name], (run_id, name)
                tar.add(path, arcname=f'{run_id}/{name}', recursive=False)
                manifest.append(dict(run_id=run_id, house=house, slot=int(r['slot']),
                                     record_index=int(r['record_index']), name=name,
                                     size_bytes=path.stat().st_size, sha256=digest))
        payload = (json.dumps(manifest, sort_keys=True, separators=(',', ':'))+'\n').encode()
        info = tarfile.TarInfo('FROZEN_INPUT_MANIFEST.json')
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    INVENTORY.write_text(json.dumps(dict(rows=len(manifest), runs=len(by_run),
                                          staged_tar_sha256=sha(OUT), files=manifest),
                                    indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(rows=len(manifest), runs=len(by_run), bytes=OUT.stat().st_size,
                          sha256=sha(OUT), tar=str(OUT)), sort_keys=True))


if __name__ == '__main__':
    main()
