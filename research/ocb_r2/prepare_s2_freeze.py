#!/usr/bin/env python3
"""Freeze the 32 inherited discovery seeds and their runtime output paths."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / 'evidence/ocb_r2'
MASTER = EVIDENCE / 'OCB_R2_MASTER_MANIFEST_96.tsv'
S1_CONFIGS = REPO / 'research/ocb_r2/OCB_R2_S1_FROZEN_CONFIGS.json'
RUNLIST = EVIDENCE / 'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
CONFIGS = REPO / 'research/ocb_r2/OCB_R2_S2_FROZEN_CONFIGS.json'
ROOT = Path('/home/zyc/ocb_r2_s2_discovery')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with MASTER.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        columns = reader.fieldnames
        assert columns is not None
        master = list(reader)
    assert len(master) == 96 and len({int(r['master_seed']) for r in master}) == 96
    source = json.loads(S1_CONFIGS.read_text(encoding='utf-8'))
    assert len(source) == 8
    selected = [r for r in master if r['phase'] == 'DISCOVERY']
    assert len(selected) == 32
    assert [(int(r['config_index']), int(r['replicate_index'])) for r in selected] == [
        (cfg, rep) for cfg in range(8) for rep in range(1, 5)
    ]
    assert all(r['house'] in ('House01', 'House02') and r['status'] == 'FROZEN_NOT_RUN' for r in selected)
    assert len({r['run_id'] for r in selected}) == 32
    configs = {}
    for row in selected:
        cfg = int(row['config_index'])
        run_id = row['run_id']
        base = source[f'ocb_r2_cfg{cfg:02d}_r01']
        assert base['original_launch_sha256'] == row['original_launch_sha256']
        assert base['source_wind_prefix'] == row['wind_asset']
        params = dict(base['parameters'])
        params['results_location'] = str(ROOT / run_id)
        assert int(row['master_seed']) == 2026900000 + 100 * cfg + int(row['replicate_index'])
        configs[run_id] = {
            **{k: v for k, v in base.items() if k != 'parameters'},
            'master_seed': int(row['master_seed']),
            'parameters': params,
        }
        assert configs[run_id]['config_index'] == cfg
        assert configs[run_id]['runtime_changed_parameter_keys'] == [
            'results_location', 'wind_data', 'pre_calculate_concentrations'
        ]
    with RUNLIST.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(selected)
    CONFIGS.write_text(json.dumps(configs, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'master_sha256': sha(MASTER), 's1_config_sha256': sha(S1_CONFIGS),
        'runlist_sha256': sha(RUNLIST), 's2_config_sha256': sha(CONFIGS),
        'run_count': len(selected),
        'house_counts': {house: sum(r['house'] == house for r in selected) for house in ('House01', 'House02')},
        'seed_count': len({r['master_seed'] for r in selected}),
    }, sort_keys=True))


if __name__ == '__main__':
    main()
