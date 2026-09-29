#!/usr/bin/env python3
"""Qualify S2X metadata and host-archive evidence without reading plume payloads."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EV = REPO / 'evidence/ocb_r2'
X = EV / 's2x'
RUNS = X / 'runs'
GENERATOR = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
RUNLIST_SHA = 'f89dbd78e56f8d564947bc0af24ddd647a0c31994a86c670e2bf0d166917700c'
INPUT_SHA = '7dceb7ba29723c605714980f4bec979f4d4b7a82e8c7557846b95f389fe9f9ce'
CONFIG_SHA = 'd0a65940cb0f90b86eacc90e70aaea2e048cbf54a9a2366db322c3cb5e570837'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def tsv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def main():
    runlist = X / 'OCB_R2_S2X_RUNLIST_32.tsv'
    inputs = X / 'OCB_R2_S2X_INPUT_SHA256.tsv'
    configs_path = REPO / 'research/ocb_r2/OCB_R2_S2X_FROZEN_CONFIGS.json'
    assert sha(runlist) == RUNLIST_SHA and sha(inputs) == INPUT_SHA and sha(configs_path) == CONFIG_SHA
    with runlist.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    configs = load(configs_path)
    assert len(rows) == len(configs) == 32
    assert len({int(r['master_seed']) for r in rows}) == 32
    strata = defaultdict(lambda: defaultdict(list))
    results, proofs = [], []
    for row in rows:
        id = row['run_id']
        c = int(row['parent_s2_config_index'])
        rep = int(id[-2:])
        assert id == f'ocb_r2_s2x_x{c:02d}_r{rep:02d}'
        assert row['house'] in ('House01', 'House02') and row['status'] == 'FROZEN_NOT_RUN'
        manifest = load(RUNS / f'{id}.RUN_MANIFEST.json')
        qc = load(RUNS / f'{id}.QC.json')
        proof = load(RUNS / f'{id}.ARCHIVE_PROOF.json')
        cleanup = load(RUNS / f'{id}.VM_CLEANUP.json')
        inventory = RUNS / f'{id}.FULL_SHA256SUMS.txt'
        timeline = RUNS / f'{id}.RECORD_TIMELINE.tsv'
        assert inventory.is_file() and timeline.is_file()
        assert manifest['run_id'] == qc['run_id'] == proof['run_id'] == cleanup['run_id'] == id
        assert manifest['generator_binary_sha256'] == qc['binary_sha256'] == GENERATOR
        assert manifest['frozen_runlist_sha256'] == RUNLIST_SHA
        assert manifest['frozen_input_sha256'] == INPUT_SHA
        assert manifest['frozen_config_sha256'] == CONFIG_SHA
        assert manifest['master_seed'] == qc['master_seed'] == int(row['master_seed'])
        assert manifest['source_id'] == qc['source_id'] == row['source_id']
        p = manifest['simulation_parameters']
        assert [float(p[f'source_position_{k}']) for k in 'xyz'] == [float(row[f'source_{k}']) for k in 'xyz']
        assert p['gas_type'] == row['gas_type'] and p['occupancy3D_data'] == row['occupancy']
        assert p['results_location'] == row['output_path']
        assert manifest['parent_s2_contract_sha256'] == qc['parent_s2_contract_sha256'] == row['parent_s2_contract_sha256']
        assert qc['decision'] == 'PASS' and qc['manifest_pass'] and qc['scientific_sanity_pass']
        assert qc['record_count'] == qc['output_file_count'] == 1803
        assert qc['first_time_s'] == 0.0 and qc['last_time_s'] == 999.502991
        assert qc['timeline_sha256'] == sha(timeline)
        parent_id = f'ocb_r2_cfg{c:02d}_r{rep:02d}'
        parent = load(EV / 's2_runs' / f'{parent_id}.RUN_MANIFEST.json')
        assert parent['house'] == row['house'] and parent['wind_id'] == row['wind_id']
        assert parent['source_id'] != row['source_id']
        assert parent['simulation_parameters']['gas_type'] == row['gas_type']
        assert parent['asset_checks'] == manifest['asset_checks']
        assert parent['qualification_standard']['wind_index_sequence_sha256'] == qc['wind_index_sequence_sha256']
        assert {k for k in p if p[k] != parent['simulation_parameters'][k]} == {'source_position_x', 'source_position_y', 'source_position_z', 'results_location'}
        assert proof['result'] == 'HASH_AFTER_COPY_PASS' and proof['file_count'] == 1817
        assert cleanup['archive_inventory_sha256'] == proof['inventory_sha256'] == sha(inventory)
        assert cleanup['file_count'] == 1817 and cleanup['archive_path'] == proof['archive_path']
        assert cleanup['deleted_raw_leaf'] == row['output_path']
        archive = Path(proof['archive_path'])
        assert archive.is_dir() and archive.name == id
        assert sum(path.is_file() for path in archive.rglob('*')) == 1817
        assert (archive / 'RUN_MANIFEST.json').read_bytes() == (RUNS / f'{id}.RUN_MANIFEST.json').read_bytes()
        source_key = (row['source_id'], tuple(float(row[f'source_{k}']) for k in 'xyz'))
        strata[c][source_key].append(id)
        results.append({'run_id': id, 'context': row['crossover_context'], 'house': row['house'],
                        'source_id': row['source_id'], 'wind_id': row['wind_id'], 'gas_type': row['gas_type'],
                        'master_seed': row['master_seed'], 'record_count': qc['record_count'],
                        'first_time_s': qc['first_time_s'], 'last_time_s': qc['last_time_s'],
                        'wind_index_sequence_sha256': qc['wind_index_sequence_sha256'],
                        'archive_file_count': proof['file_count'], 'archive_inventory_sha256': proof['inventory_sha256'],
                        'decision': 'STRUCTURAL_PASS'})
        proofs.append({'run_id': id, 'archive_path': proof['archive_path'],
                       'inventory_sha256': proof['inventory_sha256'], 'file_count': 1817,
                       'vm_raw_deleted_after_hash_pass': True})
    assert len(strata) == 8
    for c in range(8):
        for rep in range(1, 5):
            parent_id = f'ocb_r2_cfg{c:02d}_r{rep:02d}'
            parent = load(EV / 's2_runs' / f'{parent_id}.RUN_MANIFEST.json')
            pp = parent['simulation_parameters']
            key = (parent['source_id'], tuple(float(pp[f'source_position_{k}']) for k in 'xyz'))
            strata[c][key].append(parent_id)
        assert len(strata[c]) == 2 and sorted(len(v) for v in strata[c].values()) == [4,4]
        assert all(len(set(ids)) == 4 for ids in strata[c].values())
    tsv(X / 'OCB_R2_S2X_RESULTS.tsv', results)
    decision = 'OCB_R2_S2X_MATCHED_SOURCE_DATASET_PASS'
    aggregate = {'decision': decision, 'crossed_run_count': 32, 'parent_s2_run_count': 32,
                 'matched_strata_count': 8, 'source_count_per_stratum': 2, 'realizations_per_source': 4,
                 'archive_proofs': proofs}
    (X / 'OCB_R2_S2X_ARCHIVE_PROOF.json').write_text(json.dumps(aggregate, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    report = (f'# OCB-R2 S2X matched-source dataset qualification\n\n'
              f'Decision: **{decision}**\n\n'
              f'- Frozen runlist SHA256: `{RUNLIST_SHA}`\n'
              f'- Frozen input manifest SHA256: `{INPUT_SHA}`\n'
              f'- Frozen config SHA256: `{CONFIG_SHA}`\n'
              f'- Generator SHA256: `{GENERATOR}`\n'
              f'- Crossed runs: 32/32; archived with 1817/1817 files per run and host SHA after copy before VM cleanup.\n'
              f'- Structural smoke: X00r1, X02r1, X04r1, X06r1 passed before the remaining 28 runs.\n'
              f'- Archive: `C:\\GADEN_OCB_R2_ARCHIVE\\s2x_matched_source`, 32 leaves, 58,144 files, 3,875,258,707 bytes.\n'
              f'- Combined S2+S2X: 8/8 matched non-source strata, each 2 configured source positions × 4 independent realizations.\n'
              f'- Timebase: 1803 records/run, 0 to 999.502991 s; wind-index sequence matches parent S2.\n'
              f'- Pre-run infrastructure event: the first smoke attempt stopped before simulator launch because VM free space fell below the inherited 1.30 GB guard. The existing system journal was rotated and vacuumed to 200 MB, freeing 96 MB. The same frozen run was then executed. No ROS build/install or experiment asset was removed.\n'
              f'- VM raw S2X leaves after verified archival: 0; root available after campaign: 1,359,310,848 bytes.\n'
              f'- House01/House02 confirmation and House03 were not accessed by this execution.\n'
              f'- Structural QC checked finite simulator output; no concentration maps, PMFS, source rank, M0, P/Q-time, or dependency score was calculated.\n'
              f'- D0A source-comparability audit is the next separate gate; this report makes no method claim.\n')
    (REPO / 'research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_REPORT.md').write_text(report, encoding='utf-8')
    print(json.dumps({k: aggregate[k] for k in ('decision','crossed_run_count','matched_strata_count','source_count_per_stratum','realizations_per_source')}))

if __name__ == '__main__':
    main()
