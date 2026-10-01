"""Geometry/metadata-only input preparation. Does not run or rank any arm."""
import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--audit', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--canonical', type=Path, default=Path('/mnt/hgfs/workspace/GADEN_files/scenarios'))
a = p.parse_args()
audit = json.loads(a.audit.read_text())
assets = []
for case in audit['cases']:
    house = case['runtime']['house']
    selected = a.audit.parent / 'frozen_inputs' / case['case']
    original = selected / 'context_bank' / f"source_update_{int(case['terminal']['source_update_id']):04d}"
    config_ids = set()
    for f in (selected / 'resolved_runtime').glob('launch_params_*'):
        config_ids.update(re.findall(r'^\s+config_id:\s*(\S+)\s*$', f.read_text(), re.M))
    assert len(config_ids) == 1
    config_id = next(iter(config_ids))
    wind_dir = a.canonical / house / 'wind_simulations' / config_id
    # Exact historical /wind_value contract: minimum CSV iteration, static.
    winds = [(int(m[1]), f) for f in wind_dir.iterdir()
             if (m := re.fullmatch(re.escape(config_id) + r'_(\d+)\.csv', f.name))]
    state_id, wind = min(winds)
    occ = a.canonical / house / 'OccupancyGrid3D.csv'
    for file in (wind, occ):
        assets.append(dict(case=case['case'], path=str(file), bytes=file.stat().st_size,
                           sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    out = a.out / case['case']
    out.mkdir(parents=True, exist_ok=True)
    for filename in ('measured_hit_probability.csv', 'estimated_wind.csv'):
        shutil.copyfile(original / filename, out / filename)
    leaves = sorted(case['active_candidates'], key=lambda r: r['candidate_id'])
    fields = ['candidate_id', 'origin_i', 'origin_j', 'size_i', 'size_j']
    with (out / 'active_candidates.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fields, lineterminator='\n'); w.writeheader()
        w.writerows([{key: r[key] for key in fields} for r in leaves])
    t, par = case['terminal'], case['resolved_parameters']
    config = dict(width=t['grid_width'], height=t['grid_height'], cell=t['cell_size'],
                  origin_x=t['origin_x'], origin_y=t['origin_y'], update_id=t['source_update_id'],
                  # The frozen PMFS launcher declares random_seed, not seed;
                  # configureNativeDeterminism reads seed with default 0.
                  # The first sampled point agrees across seed0/seed1 logs.
                  native_rng_seed=0,
                  source_z=par['ground_truth_z'], sensor_z=t['robot_z'],
                  dt=par['deltaTime'], noise=par['noiseSTDev'], record_steps=par['iterationsToRecord'],
                  min_warmup=par['minWarmupIterations'], max_warmup=par['maxWarmupIterations'],
                  power=par['sourceDiscriminationPower'], cfd_csv=str(wind), occupancy3d=str(occ),
                  cfd_state_id=state_id)
    with (out / 'config.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, list(config), lineterminator='\n'); w.writeheader(); w.writerow(config)
    # No source xy/label, historical posterior, candidate score or truth rank in forward inputs.
    assert not any(key in config for key in ('source_x', 'source_y', 'truth_id', 'truth_rank'))
    print(case['case'], 'leaves', len(leaves), 'CFD state', state_id)
(a.out / 'ORACLE_ASSET_HASHES.json').write_text(json.dumps(assets, indent=2, sort_keys=True) + '\n')
