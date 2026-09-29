#!/usr/bin/env python3
"""Run one precommitted OCB-R2 discovery seed and qualify its raw output."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, '/home/zyc/ocb_r2_s1_tools')
import run_s1_vm as s1

TOOLS = Path('/home/zyc/ocb_r2_s2_tools')
ROOT = Path('/home/zyc/ocb_r2_s2_discovery')
RUNLIST = TOOLS / 'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
CONFIGS = TOOLS / 'OCB_R2_S2_FROZEN_CONFIGS.json'
RUNLIST_SHA = 'f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974'
CONFIGS_SHA = '72969373811ace0d30ba64d9227d429136680ce2d34449c4cc3bbd7f868eaa47'
FREEZE_COMMIT = '63935e8090b694851b899e468c2987fd793e2301'


def main(run_id: str) -> None:
    assert s1.sha(RUNLIST) == RUNLIST_SHA
    assert s1.sha(CONFIGS) == CONFIGS_SHA
    assert s1.sha(s1.BINARY) == s1.EXPECTED_BINARY_SHA
    with RUNLIST.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    configs = json.loads(CONFIGS.read_text(encoding='utf-8'))
    assert len(rows) == len(configs) == 32
    assert [r['run_id'] for r in rows] == [f'ocb_r2_cfg{c:02d}_r{r:02d}' for c in range(8) for r in range(1, 5)]
    row = next(r for r in rows if r['run_id'] == run_id)
    config = configs[run_id]
    assert row['phase'] == 'DISCOVERY' and row['house'] in ('House01', 'House02')
    assert config['config_index'] == int(row['config_index'])
    assert int(row['master_seed']) == int(config['master_seed'])
    assert int(row['master_seed']) == 2026900000 + 100 * int(row['config_index']) + int(row['replicate_index'])
    params = config['parameters']
    assert params['results_location'] == str(ROOT / run_id)
    assert params['pre_calculate_concentrations'] == 'false'
    assert params['writeConcentrations'] == 'false'
    audit = json.loads((s1.TOOLS / 'static_asset_audit/S1_STATIC_ASSET_AUDIT.json').read_text())
    entry = audit[int(row['config_index'])]
    assert row['house'] == entry['house'] and row['original_launch_sha256'] == entry['launch_sha256']
    assets = s1.verify_assets(entry, config)
    assert ROOT.resolve() == ROOT
    ROOT.mkdir(exist_ok=True)
    leaf = ROOT / run_id
    assert not leaf.exists(), f'refusing overwrite: {leaf}'
    assert shutil.disk_usage(ROOT).free >= s1.MIN_START_FREE
    argv = [str(s1.BINARY), '--ros-args']
    for key, value in params.items():
        argv.extend(['-p', f'{key}:={value}'])
    env = os.environ.copy()
    env.update(GADEN_RNG_SEED=str(config['master_seed']), OMP_NUM_THREADS='1',
               OMP_DYNAMIC='FALSE', OMP_PROC_BIND='TRUE')
    prefix = ('source /opt/ros/humble/setup.bash; '
              f'source {s1.BUILD}/install/setup.bash; '
              f'export LD_LIBRARY_PATH={s1.BUILD}/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; '
              'exec "$@"')
    log = ROOT / f'{run_id}.stdout.log'
    with log.open('wb') as f:
        returncode = subprocess.run(['bash', '-lc', prefix, 'ocb-r2-s2', *argv],
                                    env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    assert returncode == 0, f'simulator exit {returncode}; see {log}'
    qc = s1.validate_output(leaf, params)
    manifest = {
        'benchmark_version': 'OCB_R2', 'phase': 'S2_H12_DISCOVERY',
        'run_id': run_id, 'house': row['house'], 'source_id': row['source_id'],
        'wind_id': row['wind_id'], 'master_seed': int(row['master_seed']),
        'generator_binary_sha256': s1.sha(s1.BINARY),
        'frozen_config_sha256': s1.sha(CONFIGS),
        'frozen_runlist_sha256': s1.sha(RUNLIST),
        'freeze_commit': FREEZE_COMMIT,
        'simulation_parameters': params, 'asset_checks': assets,
        'qualification_standard': qc, 'omp_num_threads': 1,
    }
    (leaf / 'RUN_MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    with (leaf / 'OUTPUT_SHA256SUMS.tsv').open('w') as f:
        f.write('name\tsize_bytes\tsha256\n')
        for i in range(1803):
            file = leaf / f'iteration_{i}'
            f.write(f'{file.name}\t{file.stat().st_size}\t{s1.sha(file)}\n')
    result = {'run_id': run_id, 'decision': 'PASS', 'binary_sha256': s1.sha(s1.BINARY),
              'master_seed': int(row['master_seed']), **assets, **qc}
    (ROOT / f'{run_id}.QC.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
