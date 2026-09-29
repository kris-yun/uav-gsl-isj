#!/usr/bin/env python3
"""Frozen E2C acquisition: call the original E2 simulator/extractor for 144 rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

E2_CODE = Path('/home/zyc/e2_repo_20260925/research/environment_level_benchmark_v0/acquire_e2_vm.py')
E2_CHARTER = Path('/home/zyc/e2_repo_20260925/research/environment_level_benchmark_v0/E2_MINIMAL_FILLIN_CHARTER_20260925.md')
DATA = Path('/home/zyc/ros2_ws/e2c_r1_144_runs_20260929')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_e2():
    spec = importlib.util.spec_from_file_location('e2_acquisition_for_e2c', E2_CODE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed-manifest', type=Path, required=True)
    ap.add_argument('--source-panel', type=Path, required=True)
    ap.add_argument('--exposure-union', type=Path, required=True)
    ap.add_argument('--asset-manifest', type=Path, required=True)
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--pre-run-commit', required=True)
    ap.add_argument('--preflight-only', action='store_true')
    args = ap.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding='utf-8'))
    if freeze['new_run_count'] != 144 or sha(args.seed_manifest) != freeze['seed_manifest_sha256']:
        raise RuntimeError('pre-run seed freeze mismatch')
    if sha(args.source_panel) != freeze['source_panel_sha256']:
        raise RuntimeError('pre-run source panel freeze mismatch')
    if sha(args.exposure_union) != freeze['exposure_union_sha256']:
        raise RuntimeError('pre-run source-exposure union freeze mismatch')
    with args.asset_manifest.open(encoding='utf-8', newline='') as f:
        assets = {r['asset']: r for r in csv.DictReader(f, delimiter='\t')}
    if sha(E2_CODE) != assets['e2_original_acquisition_code']['sha256']:
        raise RuntimeError('original E2 acquisition code drift')
    if freeze['data_root'] != str(DATA):
        raise RuntimeError('frozen data root mismatch')
    with args.seed_manifest.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    with args.exposure_union.open(encoding='utf-8', newline='') as f:
        exposed = {(r['house'], r['source_id']) for r in csv.DictReader(f, delimiter='\t')}
    if len(rows) != 144 or len({r['requested_seed'] for r in rows}) != 144:
        raise RuntimeError('run count or seed uniqueness mismatch')
    if any((r['house'], r['source_id']) in exposed for r in rows if r['panel_role'] != 'DISCOVERY'):
        raise RuntimeError('confirmation source overlaps historical exposure union')
    e2 = load_e2()
    _, _, inputs = e2.build_plan()  # Verifies original E1/occupancy/wind/binary/extractor hashes.
    inputs['e2_charter_sha256'] = e2.digest(E2_CHARTER)
    if args.preflight_only:
        print('E2C_R1_PREFLIGHT_PASS', 'runs=144', 'seeds_unique=144',
              'data_root=' + str(DATA), flush=True)
        return
    DATA.mkdir(parents=True, exist_ok=True)
    inventory_path = DATA / 'E2C_RUN_MANIFEST.tsv'
    status_path = DATA / 'E2C_PROGRESS.json'
    done = []
    for n, r in enumerate(rows, 1):
        free_bytes = shutil.disk_usage(DATA).free
        if free_bytes < 100 * 1024 * 1024:
            raise RuntimeError(f'infrastructure stop: <100 MiB free before run {n}: {free_bytes}')
        item = dict(environment_index=int(r['environment_index']), role=r['panel_role'],
                    house=r['house'], wind=r['wind'], source_index=int(r['source_index']),
                    source_id=r['source_id'], source_xyz=[float(r[k]) for k in ('x_m', 'y_m', 'z_m')],
                    replicate_index=int(r['replicate_index']), requested_seed=int(r['requested_seed']),
                    run_dir=r['run_dir'])
        if not Path(item['run_dir']).is_relative_to(DATA):
            raise RuntimeError('run path escaped frozen data root')
        meta = e2.run_one(item, inputs)
        cube = Path(item['run_dir']) / 'concentration.npy'
        metadata = Path(item['run_dir']) / 'run_metadata.json'
        # E2 run_one already checked shape, finite/nonnegative values and the
        # science-neutral cube hash; sealed values are never printed here.
        done.append(dict(run_index=n, environment_index=item['environment_index'],
                         role=item['role'], house=item['house'], wind=item['wind'],
                         source_index=item['source_index'], source_id=item['source_id'],
                         replicate_index=item['replicate_index'], requested_seed=item['requested_seed'],
                         cube_path=str(cube), cube_bytes=meta['cube_bytes'],
                         cube_sha256=meta['cube_sha256'], run_metadata_path=str(metadata),
                         run_metadata_sha256=sha(metadata), qc='PASS'))
        with inventory_path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(done[0]), delimiter='\t', lineterminator='\n')
            w.writeheader()
            w.writerows(done)
        status_path.write_text(json.dumps(dict(completed=len(done), total=144,
                                                pre_run_commit=args.pre_run_commit,
                                                sealed_scientific_values_exposed=False,
                                                scientific_method_evaluated=False),
                                          indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print('E2C_QC_PASS', n, item['role'], item['house'], item['source_id'],
              item['requested_seed'], meta['cube_sha256'], flush=True)
    print('E2C_R1_ACQUISITION_144_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
