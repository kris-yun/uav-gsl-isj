#!/usr/bin/env python3
"""Extract 64 frozen OCB-R2 native targets with the historical GADEN extractor."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np


ROOT = Path('/home/zyc/aod_r2_f0')
STAGE = ROOT/'snapshots'
TOOLS = ROOT/'tools'
OUT = ROOT/'targets'
EXTRACTOR = Path('/home/zyc/rmfe_filament_extractor_omp')
PROBES = TOOLS/'E1_HOUSE_PROBE_CONTRACTS.tsv'
TIME = TOOLS/'AOD_R2_F0_TIME_MAPPING.tsv'
MANIFEST = STAGE/'FROZEN_INPUT_MANIFEST.json'
OCC = Path('/mnt/hgfs/workspace/GADEN_files/scenarios')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    assert EXTRACTOR.is_file() and OUT.exists() is False
    time = rows(TIME)
    assert len(time) == 640
    by_run = {}
    for r in time:
        by_run.setdefault(r['run_id'], []).append(r)
    assert len(by_run) == 64
    manifest = json.loads(MANIFEST.read_text())
    assert len(manifest) == 640
    by_house = {}
    for p in rows(PROBES):
        if p['house'] in {'House01', 'House02'}:
            by_house.setdefault(p['house'], []).append(p)
    assert set(by_house) == {'House01', 'House02'}
    assert all(len(v) == 30 for v in by_house.values())
    for house in by_house:
        by_house[house].sort(key=lambda p: int(p['probe_rank']))
    for rec in manifest:
        path = STAGE/rec['run_id']/rec['name']
        assert sha(path) == rec['sha256']
    OUT.mkdir()
    records = []
    for run_id in sorted(by_run):
        slots = sorted(by_run[run_id], key=lambda r: int(r['slot']))
        houses = {r['house'] for r in manifest if r['run_id'] == run_id}
        assert len(houses) == 1
        house = houses.pop()
        occ = OCC/house/'OccupancyGrid3D.csv'
        assert occ.is_file()
        run_dir = STAGE/run_id
        os.symlink(occ, run_dir/'OccupancyGrid3D.csv')
        header = occ.read_text().splitlines()[:4]
        origin = [float(x) for x in header[0].split()[1:]]
        dims = [int(x) for x in header[2].split()[1:]]
        assert len(dims) == 3
        prefix = OUT/run_id
        cmd = [str(EXTRACTOR), str(run_dir), str(run_dir),
               str(prefix.with_suffix('.cube.npy')), str(prefix.with_suffix('.meta.json')),
               repr(origin[0]), repr(origin[1]), '0.1', '1', '0.20',
               str(dims[0]), str(dims[1]),
               *[str(int(r['record_index'])) for r in slots]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (run_id, result.stdout[-1000:], result.stderr[-1000:])
        cube = np.load(prefix.with_suffix('.cube.npy'), allow_pickle=False)
        assert cube.shape == (10, dims[0], dims[1]) and np.isfinite(cube).all() and (cube >= 0).all()
        pooled = np.stack([cube[:, int(p['native_x0']):int(p['native_x1_exclusive']),
                                 int(p['native_y0']):int(p['native_y1_exclusive'])].mean(axis=(1, 2), dtype=np.float64)
                           for p in by_house[house]], axis=1)
        assert pooled.shape == (10, 30)
        np.save(prefix.with_suffix('.pooled.npy'), pooled, allow_pickle=False)
        records.append(dict(run_id=run_id, house=house, records=[int(r['record_index']) for r in slots],
                            cube_sha256=sha(prefix.with_suffix('.cube.npy')),
                            pooled_sha256=sha(prefix.with_suffix('.pooled.npy')),
                            pooled_zero=bool(np.all(pooled == 0)), extractor_sha256=sha(EXTRACTOR),
                            occupancy_sha256=sha(occ)))
        if len(records) % 8 == 0:
            print(f'F0_TARGETS {len(records)}/64', flush=True)
    (OUT/'AOD_R2_F0_TARGET_EXTRACTION.json').write_text(json.dumps(dict(decision='AOD_R2_F0_TARGETS_EXTRACTED',
                                                                     runs=records), indent=2, sort_keys=True)+'\n')
    print('AOD_R2_F0_TARGETS_EXTRACTED 64', flush=True)


if __name__ == '__main__':
    main()
