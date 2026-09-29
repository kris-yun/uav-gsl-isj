#!/usr/bin/env python3
"""Run only the frozen OCB-R2 A/B/C generator qualification on the VM.

The simulator erases its results_location on startup. This wrapper refuses an
existing output leaf and confines all outputs to a fixed, dedicated root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/home/zyc/ocb_r2_validation')
BUILD = pathlib.Path('/home/zyc/ocb_r2_seeded_gaden')
BINARY = BUILD / 'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'
CONFIG = pathlib.Path(__file__).with_name('VALIDATION_CONFIG.json')
SOURCE = BUILD / 'src/GADEN'
EXPECTED_STAGING_PLAN_SHA = '102ff41a87b0af5efcb369f5d60a64eb2e4a97aefc312617b7f395dd1eb3990a'
MIN_FREE_BYTES = 700_000_000


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('arm', choices=('A', 'B', 'C'))
    args = p.parse_args()
    config = json.loads(CONFIG.read_text())
    assert config['benchmark_version'] == 'OCB_R2'
    assert config['h02_staging_plan_sha256'] == EXPECTED_STAGING_PLAN_SHA
    assert config['params']['pre_calculate_concentrations'] == 'false'
    assert config['params']['writeConcentrations'] == 'false'
    seed = int(config['master_seeds'][args.arm])
    assert 0 <= seed <= 0xFFFFFFFF
    assert BINARY.is_file()
    assert sha256(pathlib.Path(config['params']['occupancy3D_data'])) == config['occupancy_sha256']
    wind_prefix = pathlib.Path(config['params']['wind_data'])
    assert wind_prefix.parent.is_dir()
    # The frozen legacy launch uses a trailing underscore. The ROS adapter
    # strips it on fallback, then opens each triple as stem_i.csv_{U,V,W}.
    wind_stem = str(wind_prefix).rstrip('_')
    for idx in range(11):
        for axis in 'UVW':
            assert pathlib.Path(f'{wind_stem}_{idx}.csv_{axis}').is_file(), f'missing wind state {idx}/{axis}'
    assert ROOT.resolve() == pathlib.Path('/home/zyc/ocb_r2_validation')
    ROOT.mkdir(exist_ok=True)
    leaf = ROOT / f'RUN_{args.arm}'
    if leaf.exists():
        raise RuntimeError(f'output already exists; refusing overwrite: {leaf}')
    import shutil
    if shutil.disk_usage(ROOT).free < MIN_FREE_BYTES:
        raise RuntimeError('insufficient local free disk; refusing run')

    params = dict(config['params'])
    params['results_location'] = str(leaf)
    argv = [str(BINARY), '--ros-args']
    for key, value in params.items():
        argv += ['-p', f'{key}:={value}']
    env = os.environ.copy()
    env['GADEN_RNG_SEED'] = str(seed)
    env['OMP_NUM_THREADS'] = '1'
    env['OMP_DYNAMIC'] = 'FALSE'
    env['OMP_PROC_BIND'] = 'TRUE'
    # A single stable worker owns each thread-local stream. The existing
    # Gaussian and uniform engines/distributions remain unchanged.
    prefix = (
        'source /opt/ros/humble/setup.bash; '
        f'source {BUILD}/install/setup.bash; '
        f'export LD_LIBRARY_PATH={BUILD}/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; '
        'exec "$@"'
    )
    command = ['bash', '-lc', prefix, 'ocb-r2', *argv]
    log_path = ROOT / f'RUN_{args.arm}.stdout.log'
    with log_path.open('wb') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'simulator exited {result.returncode}; see {log_path}')
    timeline = leaf / 'RECORD_TIMELINE.tsv'
    if not timeline.is_file():
        raise RuntimeError('missing provenance timeline')
    lines = timeline.read_text().splitlines()
    if lines[0] != 'record_index\tinternal_simulation_time_s\twind_index':
        raise RuntimeError('bad timeline header')
    records = [x for x in leaf.glob('iteration_*') if x.is_file()]
    if len(records) != len(lines) - 1:
        raise RuntimeError(f'output count {len(records)} != timeline count {len(lines)-1}')
    manifest = {
        'benchmark_version': 'OCB_R2',
        'arm': args.arm,
        'master_seed': seed,
        'generator_source_commit': '17adaf650a4f11d29aa049cf0661e9f9ea2e636f',
        'generator_core_commit': '9e93c36ae1af74f6a62c42f1c9d7b813153222ed',
        'generator_binary_sha256': sha256(BINARY),
        'timeline_patch_sha256': sha256(BUILD / 'READONLY_TIMELINE.patch'),
        'source_mathutils_sha256': sha256(SOURCE / 'gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp'),
        'source_running_simulation_sha256': sha256(SOURCE / 'gaden_common/third_party/gaden_core/src/RunningSimulation.cpp'),
        'occupancy_sha256': config['occupancy_sha256'],
        'h02_staging_plan_sha256': config['h02_staging_plan_sha256'],
        'wind_prefix': str(wind_prefix),
        'source_xyz': [params['source_position_x'], params['source_position_y'], params['source_position_z']],
        'gas_type': params['gas_type'],
        'simulation_parameters': {k: v for k, v in params.items() if k != 'results_location'},
        'omp_num_threads': 1,
        'record_count': len(records),
        'first_record_internal_simulation_time_s': lines[1].split('\t')[1],
        'last_record_internal_simulation_time_s': lines[-1].split('\t')[1],
        'record_timeline_sha256': sha256(timeline),
        'stdout_sha256': sha256(log_path),
    }
    (leaf / 'RUN_MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    inventory = leaf / 'OUTPUT_SHA256SUMS.tsv'
    with inventory.open('w') as fh:
        fh.write('name\tsize_bytes\tsha256\n')
        for file in sorted(records, key=lambda x: x.name):
            fh.write(f'{file.name}\t{file.stat().st_size}\t{sha256(file)}\n')
    print(json.dumps({'arm': args.arm, 'seed': seed, 'record_count': len(records), 'first': manifest['first_record_internal_simulation_time_s'], 'last': manifest['last_record_internal_simulation_time_s'], 'manifest': str(leaf / 'RUN_MANIFEST.json')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
