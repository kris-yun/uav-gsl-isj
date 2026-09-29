#!/usr/bin/env python3
"""Freeze the 32 matched-source discovery runs before any S2X simulation."""
import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EV = REPO / 'evidence/ocb_r2'
OUT = EV / 's2x'
ROOT = '/home/zyc/ocb_r2_s2x_matched_source'
GENERATOR = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
CROSSED = {
    0: ('House01_configured_2', ('-0.40', '-2.90', '-0.30')),
    1: ('House01_configured_2', ('-0.40', '-2.90', '-0.30')),
    2: ('House01_configured_1', ('-0.60', '1.95', '0.40')),
    3: ('House01_configured_1', ('-0.60', '1.95', '0.40')),
    4: ('House02_configured_2', ('1.00', '-2.30', '-0.10')),
    5: ('House02_configured_2', ('1.00', '-2.30', '-0.10')),
    6: ('House02_configured_1', ('0.00', '-1.00', '0.20')),
    7: ('House02_configured_1', ('0.00', '-1.00', '0.20')),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tsv(path, rows, columns):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parent_path = REPO / 'research/ocb_r2/OCB_R2_S2_FROZEN_CONFIGS.json'
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    audit_path = EV / 'S1_STATIC_ASSET_AUDIT.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    conversion = json.loads((EV / 'S1_WIND_LAYOUT_CONVERSION_SUMMARY.json').read_text(encoding='utf-8'))
    old_seeds = {int(r['master_seed']) for r in csv.DictReader((EV / 'OCB_R2_MASTER_MANIFEST_96.tsv').open(encoding='utf-8'), delimiter='\t')}
    rows, inputs, configs = [], [], {}
    for c in range(8):
        parent_id = f'ocb_r2_cfg{c:02d}_r01'
        p = parent[parent_id]
        a = audit[c]
        source_id, xyz = CROSSED[c]
        assert p['config_index'] == a['config_index'] == c
        assert p['source_wind_prefix'] == a['wind_prefix']
        assert p['parameters']['gas_type'] == a['gas_type']
        assert p['parameters']['occupancy3D_data'] == a['occupancy_path']
        assert a['house'] in ('House01', 'House02') and a['source_id'] != source_id
        assert tuple(float(z) for z in xyz) != tuple(float(z) for z in a['source_xyz'])
        pm = EV / 's2_runs' / f'{parent_id}.RUN_MANIFEST.json'
        m = json.loads(pm.read_text(encoding='utf-8'))
        assert m['generator_binary_sha256'] == GENERATOR
        assert m['asset_checks']['occupancy_sha256'] == a['occupancy_sha256']
        assert m['asset_checks']['wind_bundle_sha256'] == a['wind_bundle_sha256']
        base_inputs = {
            'parent_s2_config_json': (str(parent_path.relative_to(REPO)), sha(parent_path)),
            'parent_s2_run_manifest': (str(pm.relative_to(REPO)), sha(pm)),
            's1_static_asset_audit': (str(audit_path.relative_to(REPO)), sha(audit_path)),
            'generator_binary': ('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator', GENERATOR),
            'occupancy3d': (a['occupancy_path'], a['occupancy_sha256']),
            'original_wind_bundle': (a['wind_prefix'], a['wind_bundle_sha256']),
            'original_launch': (a['launch_path'], a['launch_sha256']),
            'converted_wind_manifest': (conversion[c]['conversion_manifest'], m['asset_checks']['wind_conversion_manifest_sha256']),
        }
        for kind, (path, digest) in base_inputs.items():
            inputs.append({'crossover_context': f'X{c:02d}', 'kind': kind, 'path': path, 'sha256': digest})
        for wf in a['wind_files']:
            inputs.append({'crossover_context': f'X{c:02d}', 'kind': 'original_wind_state', 'path': wf['path'], 'sha256': wf['sha256']})
        for r in range(1, 5):
            run_id = f'ocb_r2_s2x_x{c:02d}_r{r:02d}'
            seed = 2026910000 + 100*c + r
            assert seed not in old_seeds
            params = dict(p['parameters'])
            for axis, val in zip('xyz', xyz):
                params[f'source_position_{axis}'] = val
            params['results_location'] = f'{ROOT}/{run_id}'
            assert {k for k in params if params[k] != p['parameters'][k]} == {'source_position_x', 'source_position_y', 'source_position_z', 'results_location'}
            configs[run_id] = {'config_index': c, 'master_seed': seed, 'parent_s2_run_id': parent_id,
                               'parent_s2_contract_sha256': sha(pm), 'parameters': params}
            rows.append({'run_id': run_id, 'crossover_context': f'X{c:02d}', 'house': a['house'],
                         'source_id': source_id, 'source_x': xyz[0], 'source_y': xyz[1], 'source_z': xyz[2],
                         'wind_id': a['wind_id'], 'wind_asset': a['wind_prefix'], 'occupancy': a['occupancy_path'],
                         'gas_type': a['gas_type'], 'master_seed': seed, 'frozen_generator_sha256': GENERATOR,
                         'parent_s2_config_index': c, 'parent_s2_contract_sha256': sha(pm),
                         'output_path': f'{ROOT}/{run_id}', 'status': 'FROZEN_NOT_RUN'})
    assert len(rows) == len(configs) == 32 and len({r['master_seed'] for r in rows}) == 32
    tsv(OUT / 'OCB_R2_S2X_RUNLIST_32.tsv', rows, list(rows[0]))
    tsv(OUT / 'OCB_R2_S2X_INPUT_SHA256.tsv', inputs, list(inputs[0]))
    (REPO / 'research/ocb_r2/OCB_R2_S2X_FROZEN_CONFIGS.json').write_text(json.dumps(configs, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({name: sha(OUT / name) for name in ('OCB_R2_S2X_RUNLIST_32.tsv', 'OCB_R2_S2X_INPUT_SHA256.tsv')}, sort_keys=True))

if __name__ == '__main__':
    main()
