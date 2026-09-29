#!/usr/bin/env python3
"""Run one frozen S2X crossed-source realization and check structural parity."""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, '/home/zyc/ocb_r2_s1_tools')
import run_s1_vm as s1

TOOLS = Path('/home/zyc/ocb_r2_s2x_tools')
ROOT = Path('/home/zyc/ocb_r2_s2x_matched_source')
RUNLIST = TOOLS / 'OCB_R2_S2X_RUNLIST_32.tsv'
CONFIGS = TOOLS / 'OCB_R2_S2X_FROZEN_CONFIGS.json'
INPUTS = TOOLS / 'OCB_R2_S2X_INPUT_SHA256.tsv'
PARENT_CONFIGS = TOOLS / 'OCB_R2_S2_FROZEN_CONFIGS.json'
RUNLIST_SHA = 'f89dbd78e56f8d564947bc0af24ddd647a0c31994a86c670e2bf0d166917700c'
INPUTS_SHA = '7dceb7ba29723c605714980f4bec979f4d4b7a82e8c7557846b95f389fe9f9ce'
CONFIGS_SHA = 'd0a65940cb0f90b86eacc90e70aaea2e048cbf54a9a2366db322c3cb5e570837'
PARENT_CONFIGS_SHA = '72969373811ace0d30ba64d9227d429136680ce2d34449c4cc3bbd7f868eaa47'
FREEZE_COMMIT = '3d3b955b'

def main(run_id: str) -> None:
    assert s1.sha(RUNLIST) == RUNLIST_SHA
    assert s1.sha(INPUTS) == INPUTS_SHA
    assert s1.sha(CONFIGS) == CONFIGS_SHA
    assert s1.sha(PARENT_CONFIGS) == PARENT_CONFIGS_SHA
    assert s1.sha(s1.BINARY) == s1.EXPECTED_BINARY_SHA
    with RUNLIST.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    configs = json.loads(CONFIGS.read_text(encoding='utf-8'))
    parents = json.loads(PARENT_CONFIGS.read_text(encoding='utf-8'))
    assert len(rows) == len(configs) == 32
    assert [r['run_id'] for r in rows] == [f'ocb_r2_s2x_x{c:02d}_r{rep:02d}' for c in range(8) for rep in range(1,5)]
    row = next(r for r in rows if r['run_id'] == run_id)
    c = int(row['parent_s2_config_index'])
    rep = int(run_id[-2:])
    config = configs[run_id]
    assert row['crossover_context'] == f'X{c:02d}'
    assert row['status'] == 'FROZEN_NOT_RUN'
    assert row['house'] in ('House01', 'House02')
    assert int(row['master_seed']) == int(config['master_seed']) == 2026910000 + 100*c + rep
    assert row['frozen_generator_sha256'] == s1.EXPECTED_BINARY_SHA
    parent_id = config['parent_s2_run_id']
    parent = parents[parent_id]
    assert parent['config_index'] == config['config_index'] == c
    pm_path = TOOLS / 'parent_manifests' / f'{parent_id}.RUN_MANIFEST.json'
    assert s1.sha(pm_path) == row['parent_s2_contract_sha256'] == config['parent_s2_contract_sha256']
    pm = json.loads(pm_path.read_text(encoding='utf-8'))
    assert pm['generator_binary_sha256'] == s1.EXPECTED_BINARY_SHA
    assert pm['simulation_parameters'] == parent['parameters']
    params = config['parameters']
    assert set(params) == set(parent['parameters'])
    assert {k for k in params if params[k] != parent['parameters'][k]} == {
        'source_position_x', 'source_position_y', 'source_position_z', 'results_location'}
    assert [float(params[f'source_position_{k}']) for k in 'xyz'] == [float(row[f'source_{k}']) for k in 'xyz']
    assert params['results_location'] == row['output_path'] == str(ROOT / run_id)
    assert params['gas_type'] == row['gas_type']
    audit = json.loads((s1.TOOLS / 'static_asset_audit/S1_STATIC_ASSET_AUDIT.json').read_text())
    entry = audit[c]
    assert entry['house'] == row['house'] and entry['wind_id'] == row['wind_id']
    assert entry['wind_prefix'] == row['wind_asset'] and entry['occupancy_path'] == row['occupancy']
    assert entry['source_id'] != row['source_id']
    assets = s1.verify_assets(entry, parent)
    assert assets == pm['asset_checks']
    ROOT.mkdir(exist_ok=True)
    assert ROOT.resolve() == ROOT
    leaf = ROOT / run_id
    assert not leaf.exists(), f'refusing overwrite: {leaf}'
    assert shutil.disk_usage(ROOT).free >= s1.MIN_START_FREE
    argv = [str(s1.BINARY), '--ros-args']
    for key, value in params.items():
        argv.extend(['-p', f'{key}:={value}'])
    env = os.environ.copy()
    env.update(GADEN_RNG_SEED=str(config['master_seed']), OMP_NUM_THREADS='1', OMP_DYNAMIC='FALSE', OMP_PROC_BIND='TRUE')
    prefix = ('source /opt/ros/humble/setup.bash; '
              f'source {s1.BUILD}/install/setup.bash; '
              f'export LD_LIBRARY_PATH={s1.BUILD}/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; '
              'exec "$@"')
    log = ROOT / f'{run_id}.stdout.log'
    with log.open('wb') as f:
        code = subprocess.run(['bash', '-lc', prefix, 'ocb-r2-s2x', *argv], env=env,
                              stdout=f, stderr=subprocess.STDOUT).returncode
    assert code == 0, f'simulator exit {code}; see {log}'
    qc = s1.validate_output(leaf, params)
    assert qc['record_count'] == 1803 and qc['first_time_s'] == 0.0 and qc['last_time_s'] == 999.502991
    assert qc['wind_index_sequence_sha256'] == pm['qualification_standard']['wind_index_sequence_sha256']
    manifest = {
        'benchmark_version': 'OCB_R2', 'phase': 'S2X_MATCHED_SOURCE_DISCOVERY',
        'run_id': run_id, 'house': row['house'], 'source_id': row['source_id'],
        'wind_id': row['wind_id'], 'gas_type': row['gas_type'], 'master_seed': int(row['master_seed']),
        'generator_binary_sha256': s1.sha(s1.BINARY), 'frozen_config_sha256': s1.sha(CONFIGS),
        'frozen_runlist_sha256': s1.sha(RUNLIST), 'frozen_input_sha256': s1.sha(INPUTS),
        'freeze_commit': FREEZE_COMMIT, 'parent_s2_run_id': parent_id,
        'parent_s2_contract_sha256': s1.sha(pm_path), 'simulation_parameters': params,
        'asset_checks': assets, 'qualification_standard': qc, 'omp_num_threads': 1,
    }
    (leaf / 'RUN_MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    with (leaf / 'OUTPUT_SHA256SUMS.tsv').open('w') as f:
        f.write('name\tsize_bytes\tsha256\n')
        for i in range(1803):
            file = leaf / f'iteration_{i}'
            f.write(f'{file.name}\t{file.stat().st_size}\t{s1.sha(file)}\n')
    result = {'run_id': run_id, 'decision': 'PASS', 'binary_sha256': s1.sha(s1.BINARY),
              'master_seed': int(row['master_seed']), 'source_id': row['source_id'],
              'source_xyz': [float(row[f'source_{k}']) for k in 'xyz'],
              'parent_s2_run_id': parent_id, 'parent_s2_contract_sha256': s1.sha(pm_path), **assets, **qc}
    (ROOT / f'{run_id}.QC.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
