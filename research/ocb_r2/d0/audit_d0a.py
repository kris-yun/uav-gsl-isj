#!/usr/bin/env python3
"""Metadata-only D0A test of source comparability in the qualified S2 bank."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / 'evidence/ocb_r2'
RUNLIST = BASE / 'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
RUNS = BASE / 's2_runs'
OUT = BASE / 'd0'
EXPECTED_RUNLIST = 'f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974'
EXPECTED_BINARY = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_tsv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    assert sha(RUNLIST) == EXPECTED_RUNLIST
    with RUNLIST.open(newline='', encoding='utf-8') as f:
        runlist = list(csv.DictReader(f, delimiter='\t'))
    assert len(runlist) == 32
    strata: dict[tuple, dict] = defaultdict(lambda: {'sources': set(), 'runs': []})
    configs = []
    for row in runlist:
        run_id = row['run_id']
        manifest = read_json(RUNS / f'{run_id}.RUN_MANIFEST.json')
        qc = read_json(RUNS / f'{run_id}.QC.json')
        assert manifest['generator_binary_sha256'] == qc['binary_sha256'] == EXPECTED_BINARY
        assert manifest['phase'] == 'S2_H12_DISCOVERY' and row['phase'] == 'DISCOVERY'
        assert manifest['master_seed'] == int(row['master_seed'])
        assert manifest['house'] == row['house'] and manifest['source_id'] == row['source_id']
        assert manifest['wind_id'] == row['wind_id']
        assert qc['record_count'] == 1803 and qc['first_time_s'] == 0.0 and qc['last_time_s'] == 999.502991
        p = manifest['simulation_parameters']
        source_xyz = (float(p['source_position_x']), float(p['source_position_y']), float(p['source_position_z']))
        assert source_xyz == (float(row['source_x']), float(row['source_y']), float(row['source_z']))
        asset = manifest['asset_checks']
        key = (
            row['house'], asset['occupancy_sha256'], asset['wind_bundle_sha256'],
            int(p['gas_type']), qc['timeline_sha256'], qc['wind_index_sequence_sha256'],
            manifest['generator_binary_sha256'],
        )
        strata[key]['sources'].add(source_xyz)
        strata[key]['runs'].append(run_id)
        if int(row['replicate_index']) == 1:
            configs.append({
                'config_index': row['config_index'], 'house': row['house'],
                'source_id': row['source_id'], 'source_xyz': ','.join(map(str, source_xyz)),
                'wind_id': row['wind_id'], 'gas_type': str(p['gas_type']),
                'occupancy_sha256': asset['occupancy_sha256'],
                'wind_bundle_sha256': asset['wind_bundle_sha256'],
                'timeline_sha256': qc['timeline_sha256'],
                'wind_index_sequence_sha256': qc['wind_index_sequence_sha256'],
                'generator_binary_sha256': manifest['generator_binary_sha256'],
                'candidate_sources_under_same_conditions': len(strata[key]['sources']),
            })
    assert len(configs) == len(strata) == 8
    assert all(len(s['sources']) == 1 and len(s['runs']) == 4 for s in strata.values())
    assert len({(c['house'], c['source_xyz']) for c in configs}) == 4
    OUT.mkdir(parents=True, exist_ok=True)
    write_tsv(OUT / 'D0A_CONFIG_CONTRACTS.tsv', configs, list(configs[0]))
    observation = {
        'decision': 'OCB_R2_D0A_SOURCE_COMPARABILITY_HOLD',
        'source_material': 'metadata_only_no_scientific_output_read',
        'runlist_sha256': EXPECTED_RUNLIST,
        'generator_binary_sha256': EXPECTED_BINARY,
        'discovery_run_count': 32,
        'non_source_strata': 8,
        'sources_per_stratum': [len(s['sources']) for s in strata.values()],
        'replicates_per_stratum': [len(s['runs']) for s in strata.values()],
        'observation_coordinates': None,
        'observation_times': None,
        'readout_definition': None,
        'reason': 'No same-condition source pair; observation operator and D0 scores intentionally not opened.',
    }
    (OUT / 'D0_OBSERVATION_CONTRACT.json').write_text(json.dumps(observation, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'decision': observation['decision'], 'strata': len(strata),
                      'sources_per_stratum': observation['sources_per_stratum'],
                      'audit_sha256': sha(OUT / 'D0A_CONFIG_CONTRACTS.tsv')}))


if __name__ == '__main__':
    main()
