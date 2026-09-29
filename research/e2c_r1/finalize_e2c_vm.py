#!/usr/bin/env python3
"""Extract frozen E1 probes from 48 reused and 144 new cubes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

E2_REPO = Path('/home/zyc/e2_repo_20260925')
E2_EVIDENCE = E2_REPO / 'evidence/environment_level_benchmark_v0/e2'
E1_EVIDENCE = E2_REPO / 'evidence/environment_level_benchmark_v0/e1'
DATA = Path('/home/zyc/ros2_ws/e2c_r1_144_runs_20260929')
CANONICAL = {0: ('House01', '1,3-2,4_fast'),
             1: ('House02', '3,5-1_slow'),
             5: ('House03', '1-2,5_fast')}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-panel', type=Path, required=True)
    ap.add_argument('--seed-manifest', type=Path, required=True)
    ap.add_argument('--pre-run-commit', required=True)
    args = ap.parse_args()
    panel = read_tsv(args.source_panel)
    seed_rows = read_tsv(args.seed_manifest)
    if len(panel) != 24 or len(seed_rows) != 120:
        raise RuntimeError('panel or seed count mismatch')
    source_by_key = {(r['house'], r['source_id']): r for r in panel}
    probes = read_tsv(E1_EVIDENCE / 'E1_HOUSE_PROBE_CONTRACTS.tsv')
    probe_by_house = {h: sorted((p for p in probes if p['house'] == h), key=lambda x: int(x['probe_rank']))
                      for h in ('House01', 'House02', 'House03')}
    old = [r for r in read_tsv(E2_EVIDENCE / 'E2_RUN_MANIFEST.tsv')
           if int(r['environment_index']) in (0, 1)]
    new = read_tsv(DATA / 'E2C_RUN_MANIFEST.tsv')
    if len(old) != 48 or len(new) != 144:
        raise RuntimeError('expected 48 original discovery and 144 new runs')
    rows = []
    open_cube = np.empty((2, 6, 8, 10, 30), dtype=np.float32)
    original_open = np.load(E2_EVIDENCE / 'E2_OPEN_DISCOVERY_10x30.npy', allow_pickle=False)
    for phase, family in (('E2_ORIGINAL', old), ('E2C_NEW', new)):
        for r in family:
            ei = int(r['environment_index'])
            house, wind = CANONICAL[ei]
            if r['house'] != house or r['wind'] != wind:
                raise RuntimeError('canonical environment drift')
            cube_path = Path(r['cube_path'])
            if not cube_path.is_file() or sha(cube_path) != r['cube_sha256']:
                raise RuntimeError(f'cube hash mismatch: {cube_path}')
            source = source_by_key[(house, r['source_id'])]
            si, rep = int(source['source_index']), int(r['replicate_index'])
            if phase == 'E2_ORIGINAL' and (si >= 6 or rep >= 4):
                raise RuntimeError('original E2 source/replicate drift')
            if phase == 'E2C_NEW' and ((ei in (0, 1) and si < 6 and rep < 4) or rep >= 8):
                raise RuntimeError('new source/replicate drift')
            cube = np.load(cube_path, allow_pickle=False)
            if cube.shape != (10, *{'House01': (87, 114), 'House02': (83, 119), 'House03': (138, 83)}[house]):
                raise RuntimeError('cube shape drift')
            values = []
            for p in probe_by_house[house]:
                x0, x1 = int(p['native_x0']), int(p['native_x1_exclusive'])
                y0, y1 = int(p['native_y0']), int(p['native_y1_exclusive'])
                if (x1 - x0, y1 - y0) != (2, 2):
                    raise RuntimeError('E1 footprint drift')
                values.append(cube[:, x0:x1, y0:y1].mean(axis=(1, 2)))
            pooled = np.stack(values, axis=1).astype(np.float32)
            if pooled.shape != (10, 30) or not np.isfinite(pooled).all() or (pooled < 0).any():
                raise RuntimeError('pooled QC failure')
            if phase == 'E2_ORIGINAL' and ei in (0, 1):
                if not np.array_equal(pooled, original_open[ei, si, rep]):
                    raise RuntimeError('E2 open extraction parity mismatch')
            if ei in (0, 1) and si < 6:
                open_cube[ei, si, rep] = pooled
            pooled_path = DATA / 'pooled_10x30' / house / r['source_id'] / f'r{rep}_seed{r["requested_seed"]}.npy'
            pooled_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(pooled_path, pooled, allow_pickle=False)
            rows.append(dict(phase=phase, environment_index=ei, house=house, wind=wind,
                             source_index=si, source_id=r['source_id'], replicate_index=rep,
                             requested_seed=r['requested_seed'], panel_role=source['panel_role'],
                             cube_path=str(cube_path), cube_sha256=r['cube_sha256'],
                             pooled_path=str(pooled_path), pooled_sha256=sha(pooled_path), qc='PASS'))
    keys = {(r['house'], r['source_id'], r['replicate_index']) for r in rows}
    if len(rows) != 192 or len(keys) != 192:
        raise RuntimeError('combined benchmark count drift')
    if Counter(r['panel_role'] for r in rows) != Counter(dict(DISCOVERY=96,
                                                            SEALED_WITHIN_HOUSE_CONFIRMATION=32,
                                                            SEALED_H03_SOURCE_UNSEEN_CONFIRMATION=64)):
        raise RuntimeError('role split drift')
    write_tsv(DATA / 'E2C_ALL192_HASH_MANIFEST.tsv', rows)
    open_path = DATA / 'E2C_OPEN_DISCOVERY_2H_6S_8R_10x30.npy'
    np.save(open_path, open_cube, allow_pickle=False)
    report = dict(decision='E2C_R1_BENCHMARK_COMPLETE_SEALED',
                  original_runs=48, new_runs=144, total_runs=192,
                  sources_per_house=8, realizations_per_source=8,
                  discovery_runs=96, within_house_confirmation_runs=32,
                  house03_source_unseen_confirmation_runs=64,
                  house03_environment_historically_untouched=False,
                  all_cube_and_pooled_hashes_verified=True,
                  e2_open_extractor_exact_parity=True,
                  open_array_sha256=sha(open_path),
                  all192_manifest_sha256=sha(DATA / 'E2C_ALL192_HASH_MANIFEST.tsv'),
                  pre_run_commit=args.pre_run_commit,
                  sealed_scientific_values_exposed=False,
                  scientific_method_evaluated=False)
    (DATA / 'E2C_QC_SUMMARY.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
