#!/usr/bin/env python3
"""Inherit the audited OCB-R1 seed matrix into an OCB-R2 master-seed freeze."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OLD = REPO / 'evidence/ocb_r1/SEED_MANIFEST_96.tsv'
COMMANDS = REPO / 'evidence/ocb_r1/RUNNER_COMMAND_CONTRACT.json'
OUT = REPO / 'evidence/ocb_r2'
CONFIG = REPO / 'research/ocb_r2/OCB_R2_S1_FROZEN_CONFIGS.json'
ROLE = {'DISCOVERY': 'DISCOVERY',
        'SEALED_STOCHASTIC_CONFIRMATION': 'CONFIRMATION',
        'SEALED_EXTERNAL_HOUSE_CONFIRMATION': 'SEALED_CONFIRMATION'}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_tsv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with OLD.open(newline='', encoding='utf-8') as fh:
        original = list(csv.DictReader(fh, delimiter='\t'))
    contract = json.loads(COMMANDS.read_text(encoding='utf-8'))
    assert len(original) == len(contract['intended_commands']) == 96
    assert len({int(row['requested_seed']) for row in original}) == 96
    by_key = {(int(x['config_index']), int(x['requested_seed'])): x for x in contract['intended_commands']}
    master, runlist, configs = [], [], {}
    for old in original:
        cfg = int(old['config_index'])
        rep = int(old['replicate_index'])
        seed = int(old['requested_seed'])
        cmd = by_key[(cfg, seed)]
        params = cmd['effective_parameter_map']
        assert params['source_position_x'] == f"{float(old['x_m']):.2f}" or float(params['source_position_x']) == float(old['x_m'])
        assert float(params['source_position_y']) == float(old['y_m'])
        assert float(params['source_position_z']) == float(old['z_m'])
        assert int(params['gas_type']) == int(old['gas_type'])
        assert cmd['environment_override']['GADEN_RNG_SEED'] == str(seed)
        house = old['house']
        wind = old['wind_config']
        if house == 'House02':
            source_prefix = f'/home/zyc/ocb_r1_assets/h02_wind_reconstructed/{wind}/{wind}'
        else:
            source_prefix = params['wind_data'].rstrip('_')
        phase = ROLE[old['role']]
        if house == 'House03':
            assert phase == 'SEALED_CONFIRMATION'
        else:
            assert phase in ('DISCOVERY', 'CONFIRMATION')
        run_id = f'ocb_r2_cfg{cfg:02d}_r{rep:02d}'
        row = {
            'run_id': run_id, 'config_index': cfg, 'replicate_index': rep,
            'house': house, 'source_id': old['source_id'], 'wind_id': wind,
            'source_x': old['x_m'], 'source_y': old['y_m'], 'source_z': old['z_m'],
            'wind_asset': source_prefix, 'occupancy': params['occupancy3D_data'],
            'gas_type': old['gas_type'], 'master_seed': seed,
            'phase': phase, 'status': 'SEALED_NOT_RUN' if house == 'House03' else 'FROZEN_NOT_RUN',
            'original_launch_sha256': cmd['original_launch_sha256'],
        }
        master.append(row)
        if house != 'House03' and rep == 1:
            runlist.append(row.copy())
            if cfg == 5:
                runtime_wind = '/home/zyc/ocb_r2_seeded_gaden/wind_compat/3,5-1_slow'
            else:
                runtime_wind = f'/home/zyc/ocb_r2_seeded_gaden/wind_compat_s1/cfg{cfg:02d}/{wind}'
            runtime_params = dict(params)
            runtime_params['wind_data'] = runtime_wind
            runtime_params['results_location'] = f'/home/zyc/ocb_r2_s1/{run_id}'
            assert 'pre_calculate_concentrations' not in params
            runtime_params['pre_calculate_concentrations'] = 'false'  # frozen simulator default, made explicit
            configs[run_id] = {'config_index': cfg, 'master_seed': seed,
                               'source_wind_prefix': source_prefix,
                               'original_launch_sha256': cmd['original_launch_sha256'],
                               'original_parameter_map_sha256': hashlib.sha256(json.dumps(params, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                               'runtime_changed_parameter_keys': ['results_location', 'wind_data', 'pre_calculate_concentrations'],
                               'parameters': runtime_params}
    assert len(master) == 96 and len(runlist) == 8
    assert [r['config_index'] for r in runlist] == list(range(8))
    columns = list(master[0])
    write_tsv(OUT / 'OCB_R2_MASTER_MANIFEST_96.tsv', master, columns)
    write_tsv(OUT / 'OCB_R2_S1_RUNLIST_8.tsv', runlist, columns)
    CONFIG.write_text(json.dumps(configs, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    lineage = f'''# OCB-R2 master-seed lineage

Source: `evidence/ocb_r1/SEED_MANIFEST_96.tsv`, SHA256 `{sha(OLD)}`.
Audited command contract: `evidence/ocb_r1/RUNNER_COMMAND_CONTRACT.json`, SHA256 `{sha(COMMANDS)}`.

All 96 `requested_seed` integers were copied one-to-one into `master_seed`.
No seed was drawn, replaced, or selected from plume outcomes. The S1 rule is
replicate index 1 (the first frozen seed) for each H01/H02 configuration
index 0 through 7. Replicates 1-4 retain DISCOVERY status; replicates 5-8
remain CONFIRMATION for H01/H02. All H03 rows remain SEALED_CONFIRMATION and
SEALED_NOT_RUN. No H03 simulation is authorized in S1.

The master manifest hashes are frozen separately; `run_id` is a deterministic
identifier only. House02 wind_asset points to the approved reconstructed
staging (not the conflicted raw copy). Runtime uses a layout-only conversion
of these frozen wind values for the current GADEN v3 loader.
'''
    (OUT / 'SEED_MANIFEST_LINEAGE.md').write_text(lineage, encoding='utf-8')
    print(json.dumps({'master_count': len(master), 'runlist_count': len(runlist),
                      'old_sha256': sha(OLD), 'master_sha256': sha(OUT / 'OCB_R2_MASTER_MANIFEST_96.tsv'),
                      'runlist_sha256': sha(OUT / 'OCB_R2_S1_RUNLIST_8.tsv')}))


if __name__ == '__main__':
    main()
