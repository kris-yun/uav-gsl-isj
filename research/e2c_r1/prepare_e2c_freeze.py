#!/usr/bin/env python3
"""Create E2C source-role and 120-seed manifests before any new GADEN run."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = Path('D:/ZYC/A-gas/_staging')
E2_TAR = STAGING / 'E2_CROSS_ENVIRONMENT_REVIEW_20260925.tar.gz'
JTD_TAR = STAGING / 'JTD_E2_RAW_180_20260925.tar.gz'
E2C = ROOT / 'evidence/e2c_r1'
PANEL = E2C / 'SOURCE_PANEL_8x3.tsv'
DATA_ROOT = '/home/zyc/ros2_ws/e2c_r1_120_runs_20260929'
WINDS = {'House01': ('1,3-2,4_fast', 0),
         'House02': ('3,5-1_slow', 1),
         'House03': ('1-2,5_fast', 5)}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def member(t: tarfile.TarFile, suffix: str) -> bytes:
    names = [n for n in t.getnames() if n.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(f'ambiguous archive member: {suffix}: {names}')
    return t.extractfile(names[0]).read()


def read_tsv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode('utf-8')), delimiter='\t'))


def write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    panel = read_tsv_bytes(PANEL.read_bytes())
    if len(panel) != 24:
        raise RuntimeError('expected 8 source cells per House')
    with tarfile.open(E2_TAR) as t:
        original = read_tsv_bytes(member(t, 'E2_RUN_MANIFEST.tsv'))
        e2_prov = json.loads(member(t, 'E2_INPUT_PROVENANCE.json'))
        e2_manifest_hash = sha_bytes(member(t, 'E2_RUN_MANIFEST.tsv'))
        e1_probe_hash = sha_bytes(member(t, '/repo/evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv'))
        e2_acquisition_code_hash = sha_bytes(member(t, 'acquire_e2_vm.py'))
    known_seeds = {int(r['requested_seed']) for r in original}
    # Existing JTD E2 bank is another independent campaign; ensure the new
    # deterministic namespace does not reuse those existing seed integers.
    with tarfile.open(JTD_TAR) as t:
        import re
        known_seeds.update(int(re.search(r'seed_(\d+)', n).group(1))
                           for n in t.getnames() if n.endswith('concentration.npy'))
    old_by_key = defaultdict(list)
    for r in original:
        if int(r['environment_index']) in (0, 1, 5):
            old_by_key[(r['house'], r['source_id'])].append(r)
    runs = []
    splits = []
    for house_index, house in enumerate(('House01', 'House02', 'House03')):
        wind, env_index = WINDS[house]
        rows = sorted((r for r in panel if r['house'] == house), key=lambda r: int(r['source_index']))
        if [int(r['source_index']) for r in rows] != list(range(8)):
            raise RuntimeError(f'panel ordering drift: {house}')
        for r in rows:
            si = int(r['source_index'])
            old = old_by_key.get((house, r['source_id']), [])
            if (si < 6 and (len(old) != 4 or {int(x['replicate_index']) for x in old} != set(range(4))
                            or {x['wind'] for x in old} != {wind})):
                raise RuntimeError(f'old E2 coverage mismatch: {house} {r["source_id"]}')
            if si >= 6 and old:
                raise RuntimeError(f'new source already appears in canonical E2: {house} {r["source_id"]}')
            split = dict(house=house, wind=wind, environment_index=env_index,
                         source_index=si, source_id=r['source_id'],
                         panel_role=r['panel_role'], panel_origin=r['panel_origin'],
                         old_realizations=len(old), new_realizations=4 if si < 6 else 8,
                         total_realizations=8)
            splits.append(split)
            for rep in (range(4, 8) if si < 6 else range(8)):
                seed = 2026290000 + 10000 * house_index + 100 * si + rep
                runs.append(dict(house=house, wind=wind, environment_index=env_index,
                                 source_index=si, source_id=r['source_id'],
                                 x_m=r['x_m'], y_m=r['y_m'], z_m=r['z_m'],
                                 replicate_index=rep, requested_seed=seed,
                                 panel_role=r['panel_role'], panel_origin=r['panel_origin'],
                                 run_dir=f'{DATA_ROOT}/{r["panel_role"]}/{house}/{wind}/{r["source_id"]}/r{rep}_seed{seed}'))
    if len(runs) != 120 or len({r['requested_seed'] for r in runs}) != 120:
        raise RuntimeError('120 unique seeds not achieved')
    if known_seeds & {r['requested_seed'] for r in runs}:
        raise RuntimeError('new seed overlaps E2 or JTD E2')
    if Counter(r['house'] for r in runs) != Counter({'House01': 40, 'House02': 40, 'House03': 40}):
        raise RuntimeError('per-House run arithmetic drift')
    E2C.mkdir(parents=True, exist_ok=True)
    write_tsv(E2C / 'SEED_MANIFEST_120.tsv', runs)
    write_tsv(E2C / 'SPLIT_MANIFEST.tsv', splits)
    assets = []
    for label, path in [('timebase_map', E2C / 'TIMEBASE_MAP.csv'),
                        ('source_panel', PANEL),
                        ('source_selection_audit', E2C / 'SOURCE_PANEL_SELECTION_AUDIT.json'),
                        ('prior_source_identity_exposure_audit', E2C / 'PRIOR_EXPOSURE_AUDIT.json'),
                        ('timebase_audit_code', ROOT / 'research/e2c_r1/audit_e2_timebase.py'),
                        ('source_selector_code', ROOT / 'research/e2c_r1/select_e2c_sources_vm.py'),
                        ('freeze_builder_code', ROOT / 'research/e2c_r1/prepare_e2c_freeze.py'),
                        ('e2c_acquisition_code', ROOT / 'research/e2c_r1/run_e2c_vm.py'),
                        ('e2c_finalization_code', ROOT / 'research/e2c_r1/finalize_e2c_vm.py'),
                        ('e2c_review_packager_code', ROOT / 'research/e2c_r1/package_e2c_vm.py'),
                        ('e2_review_archive', E2_TAR)]:
        assets.append(dict(asset=label, path=str(path), sha256=sha(path)))
    assets.append(dict(asset='e2_run_manifest', path='E2 review archive member E2_RUN_MANIFEST.tsv', sha256=e2_manifest_hash))
    assets.append(dict(asset='e2_original_acquisition_code', path='E2 review archive member acquire_e2_vm.py', sha256=e2_acquisition_code_hash))
    assets.append(dict(asset='e1_probe_contract', path='E2 archive E1_HOUSE_PROBE_CONTRACTS.tsv', sha256=e1_probe_hash))
    assets.append(dict(asset='e2_binary', path=e2_prov['binary_path'], sha256=e2_prov['binary_sha256']))
    assets.append(dict(asset='e2_extractor', path=e2_prov['extractor_path'], sha256=e2_prov['extractor_sha256']))
    for house in WINDS:
        assets.append(dict(asset=f'{house}_occupancy', path=f'canonical/{house}/OccupancyGrid3D.csv',
                           sha256=e2_prov['occupancy_sha256'][house]))
        env_index = WINDS[house][1]
        for name, digest in sorted(e2_prov['wind_meta'][str(env_index)]['iteration_hashes'].items()):
            assets.append(dict(asset=f'{house}_{name}', path=f'{e2_prov["wind_meta"][str(env_index)]["path"]}/{name}',
                               sha256=digest))
    write_tsv(E2C / 'PRE_RUN_ASSET_SHA256.tsv', assets)
    result = dict(new_run_count=len(runs), per_house_new=40, panel_sources_per_house=8,
                  realizations_per_source=8, existing_e2_reused=72,
                  known_e2_and_jtd_seed_overlap=0, sealed_h03_sources=8,
                  h01_h02_new_source_confirmation=2, geometry_only=True,
                  scientific_concentration_values_read=False,
                  house03_dataset_can_remain_sealed_but_house_identity_historically_untouched=False,
                  h02_new_source_identity_all_historically_untouched=False,
                  data_root=DATA_ROOT, e2_run_manifest_sha256=e2_manifest_hash,
                  source_panel_sha256=sha(PANEL), seed_manifest_sha256=sha(E2C / 'SEED_MANIFEST_120.tsv'),
                  split_manifest_sha256=sha(E2C / 'SPLIT_MANIFEST.tsv'))
    (E2C / 'PRE_RUN_FREEZE.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
