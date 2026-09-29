#!/usr/bin/env python3
"""Run one frozen H01/H02 S1 configuration, then perform structural QC."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

import numpy as np

TOOLS = Path('/home/zyc/ocb_r2_s1_tools')
ROOT = Path('/home/zyc/ocb_r2_s1')
BUILD = Path('/home/zyc/ocb_r2_seeded_gaden')
BINARY = BUILD / 'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'
EXPECTED_BINARY_SHA = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
MIN_START_FREE = 1_300_000_000


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def parse_record(path: Path) -> np.ndarray:
    blob = path.read_bytes()
    assert blob[:13] == b'GADEN_RESULT\x00'
    assert blob[13] == 1
    expected = struct.unpack_from('<Q', blob, 14)[0]
    raw = zlib.decompress(blob[22:])
    assert len(raw) == expected
    marker = raw.find(b'filaments')
    assert marker >= 8 and raw.find(b'filaments', marker + 1) < 0
    assert struct.unpack_from('<Q', raw, marker - 8)[0] == 9
    count = struct.unpack_from('<Q', raw, marker + 9)[0]
    start = marker + 17
    assert len(raw) - start == 16 * count
    return np.frombuffer(raw, dtype='<f4', count=4*count, offset=start).reshape(count, 4)


def verify_assets(entry: dict, config: dict) -> dict:
    params = config['parameters']
    assert sha(BINARY) == EXPECTED_BINARY_SHA
    assert sha(Path(entry['occupancy_path'])) == entry['occupancy_sha256']
    assert sha(Path(entry['launch_path'])) == entry['launch_sha256'] == config['original_launch_sha256']
    assert [float(params[f'source_position_{k}']) for k in 'xyz'] == [float(x) for x in entry['source_xyz']]
    assert int(params['gas_type']) == int(entry['gas_type'])
    assert params['pre_calculate_concentrations'] == 'false'
    assert params['writeConcentrations'] == 'false'
    for file in entry['wind_files']:
        assert sha(Path(file['path'])) == file['sha256']
    summary = json.loads((TOOLS / 'static_asset_audit/S1_WIND_LAYOUT_CONVERSION_SUMMARY.json').read_text())
    conv = summary[entry['config_index']]
    manifest_path = Path(conv['conversion_manifest'])
    assert sha(manifest_path) == conv['sha256']
    converted = json.loads(manifest_path.read_text())
    assert len(converted) == 11
    by_key = {(x['state'], x['axis']): x for x in entry['wind_files']}
    for state in converted:
        i = state.get('state', state.get('index'))
        assert i is not None
        assert int(state['cells']) == int(entry['wind_cells_per_state'])
        assert state['input_sha256'] == [by_key[i, axis]['sha256'] for axis in 'UVW']
        assert sha(Path(state['output_path'])) == state['output_sha256']
    return {'occupancy_sha256': entry['occupancy_sha256'], 'wind_bundle_sha256': entry['wind_bundle_sha256'],
            'wind_conversion_manifest_sha256': conv['sha256'], 'launch_sha256': entry['launch_sha256']}


def validate_output(leaf: Path, params: dict) -> dict:
    timeline = leaf / 'RECORD_TIMELINE.tsv'
    assert timeline.is_file()
    with timeline.open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(rows) == 1803
    assert list(rows[0]) == ['record_index','internal_simulation_time_s','wind_index']
    times = [float(x['internal_simulation_time_s']) for x in rows]
    winds = [int(x['wind_index']) for x in rows]
    assert all(int(row['record_index']) == i for i, row in enumerate(rows))
    assert times[0] == 0.0 and times[-1] == 999.502991
    assert all(math.isfinite(x) for x in times)
    assert all(b > a for a, b in zip(times, times[1:]))
    assert winds[0] == 0 and all(0 <= x <= 10 for x in winds)
    assert all(b == a or b == a+1 or (a == 10 and b == 1) for a,b in zip(winds, winds[1:]))
    files = [leaf / f'iteration_{i}' for i in range(1803)]
    assert all(p.is_file() and p.stat().st_size > 0 for p in files)
    counts, max_center_ppm = [], 0.0
    sigma0 = float(params['filament_initial_std'])
    ppm0 = float(params['ppm_filament_center'])
    for file in files:
        fil = parse_record(file)
        assert np.isfinite(fil).all()
        if len(fil):
            assert (fil[:, 3] > 0).all()
            # Native Gaussian amplitude at each filament's own center.
            center_ppm = ppm0 * np.power(sigma0 / fil[:, 3].astype(np.float64), 3)
            assert np.isfinite(center_ppm).all() and (center_ppm > 0).all()
            max_center_ppm = max(max_center_ppm, float(center_ppm.max()))
        counts.append(len(fil))
    assert counts[0] == 0 and any(n > 0 for n in counts[1:])
    assert len(list(leaf.glob('iteration_*'))) == 1803
    assert len(list((leaf / 'wind').glob('wind_iteration_*'))) == 11
    return {'record_count': 1803, 'first_time_s': times[0], 'last_time_s': times[-1],
            'timeline_sha256': sha(timeline), 'wind_states_used': sorted(set(winds)),
            'wind_index_sequence_sha256': hashlib.sha256(bytes(winds)).hexdigest(),
            'output_file_count': len(files), 'nonempty_filament_records': sum(n > 0 for n in counts),
            'max_finite_filament_center_ppm': max_center_ppm,
            'manifest_pass': True, 'scientific_sanity_pass': True}


def main(run_id: str):
    assert run_id.startswith('ocb_r2_cfg') and run_id.endswith('_r01')
    configs = json.loads((TOOLS / 'OCB_R2_S1_FROZEN_CONFIGS.json').read_text())
    assert run_id in configs and len(configs) == 8
    with (TOOLS / 'OCB_R2_S1_RUNLIST_8.tsv').open(newline='') as f:
        runlist = {x['run_id']: x for x in csv.DictReader(f, delimiter='\t')}
    assert run_id in runlist and len(runlist) == 8
    config, row = configs[run_id], runlist[run_id]
    seed = int(row['master_seed'])
    assert seed == int(config['master_seed']) and 0 <= seed <= 0xFFFFFFFF
    audit = json.loads((TOOLS / 'static_asset_audit/S1_STATIC_ASSET_AUDIT.json').read_text())
    entry = audit[int(config['config_index'])]
    assert row['house'] == entry['house'] and row['house'] in ('House01','House02')
    assets = verify_assets(entry, config)
    params = config['parameters']
    assert ROOT.resolve() == ROOT and params['results_location'] == str(ROOT / run_id)
    ROOT.mkdir(exist_ok=True)
    leaf = ROOT / run_id
    assert not leaf.exists(), f'refusing overwrite: {leaf}'
    assert shutil.disk_usage(ROOT).free >= MIN_START_FREE
    argv = [str(BINARY), '--ros-args']
    for key, value in params.items():
        argv.extend(['-p', f'{key}:={value}'])
    env = os.environ.copy()
    env.update(GADEN_RNG_SEED=str(seed), OMP_NUM_THREADS='1', OMP_DYNAMIC='FALSE', OMP_PROC_BIND='TRUE')
    prefix = ('source /opt/ros/humble/setup.bash; '
              f'source {BUILD}/install/setup.bash; '
              f'export LD_LIBRARY_PATH={BUILD}/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; '
              'exec "$@"')
    log = ROOT / f'{run_id}.stdout.log'
    with log.open('wb') as f:
        returncode = subprocess.run(['bash','-lc',prefix,'ocb-r2-s1',*argv], env=env,
                                    stdout=f, stderr=subprocess.STDOUT).returncode
    assert returncode == 0, f'simulator exit {returncode}; see {log}'
    qc = validate_output(leaf, params)
    manifest = {'benchmark_version':'OCB_R2', 'phase':'S1_H12_STRUCTURAL_SMOKE',
                'run_id':run_id, 'house':row['house'], 'source_id':row['source_id'],
                'wind_id':row['wind_id'], 'master_seed':seed,
                'generator_binary_sha256':sha(BINARY), 'frozen_config_sha256':sha(TOOLS / 'OCB_R2_S1_FROZEN_CONFIGS.json'),
                'frozen_runlist_sha256':sha(TOOLS / 'OCB_R2_S1_RUNLIST_8.tsv'),
                'simulation_parameters':params, 'asset_checks':assets, 'qualification_standard':qc,
                'omp_num_threads':1}
    (leaf / 'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    with (leaf / 'OUTPUT_SHA256SUMS.tsv').open('w') as f:
        f.write('name\tsize_bytes\tsha256\n')
        for i in range(1803):
            file = leaf / f'iteration_{i}'
            f.write(f'{file.name}\t{file.stat().st_size}\t{sha(file)}\n')
    result = {'run_id':run_id, 'decision':'PASS', 'binary_sha256':sha(BINARY), **assets, **qc}
    (ROOT / f'{run_id}.QC.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
