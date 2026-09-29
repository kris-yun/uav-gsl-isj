#!/usr/bin/env python3
"""Aggregate S2 structural qualification without scoring source inference."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / 'evidence/ocb_r2'
RUNLIST = EVIDENCE / 'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
CONFIGS = REPO / 'research/ocb_r2/OCB_R2_S2_FROZEN_CONFIGS.json'
RUNS = EVIDENCE / 's2_runs'
ARCHIVE = Path('C:/GADEN_OCB_R2_ARCHIVE/s2_discovery')
S1_RUNS = EVIDENCE / 's1_runs'
EXPECTED_BINARY = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
EXPECTED_RUNLIST = 'f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974'
EXPECTED_CONFIGS = '72969373811ace0d30ba64d9227d429136680ce2d34449c4cc3bbd7f868eaa47'
FREEZE_COMMIT = '63935e8090b694851b899e468c2987fd793e2301'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> None:
    assert sha(RUNLIST) == EXPECTED_RUNLIST and sha(CONFIGS) == EXPECTED_CONFIGS
    with RUNLIST.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(rows) == 32
    assert [(int(r['config_index']), int(r['replicate_index'])) for r in rows] == [
        (c, r) for c in range(8) for r in range(1, 5)
    ]
    summary = []
    parity_configs = 0
    for row in rows:
        run_id = row['run_id']
        qc = read_json(RUNS / f'{run_id}.QC.json')
        manifest = read_json(RUNS / f'{run_id}.RUN_MANIFEST.json')
        proof = read_json(RUNS / f'{run_id}.ARCHIVE_PROOF.json')
        cleanup = read_json(RUNS / f'{run_id}.VM_CLEANUP.json')
        timeline = RUNS / f'{run_id}.RECORD_TIMELINE.tsv'
        output = RUNS / f'{run_id}.OUTPUT_SHA256SUMS.tsv'
        inventory = RUNS / f'{run_id}.FULL_SHA256SUMS.txt'
        assert qc['decision'] == 'PASS' and qc['scientific_sanity_pass']
        assert qc['binary_sha256'] == manifest['generator_binary_sha256'] == EXPECTED_BINARY
        assert manifest['benchmark_version'] == 'OCB_R2' and manifest['phase'] == 'S2_H12_DISCOVERY'
        assert manifest['freeze_commit'] == FREEZE_COMMIT
        assert manifest['frozen_runlist_sha256'] == EXPECTED_RUNLIST
        assert manifest['frozen_config_sha256'] == EXPECTED_CONFIGS
        assert manifest['master_seed'] == qc['master_seed'] == int(row['master_seed'])
        assert manifest['house'] == row['house'] and manifest['wind_id'] == row['wind_id']
        assert manifest['asset_checks']['launch_sha256'] == row['original_launch_sha256']
        assert manifest['omp_num_threads'] == 1
        assert qc['record_count'] == qc['output_file_count'] == 1803
        assert qc['first_time_s'] == 0.0 and qc['last_time_s'] == 999.502991
        assert qc['wind_states_used'] == list(range(11))
        assert qc['nonempty_filament_records'] == 1802
        assert qc['max_finite_filament_center_ppm'] > 0
        assert sha(timeline) == qc['timeline_sha256']
        assert sum(1 for _ in output.open('r', encoding='utf-8')) == 1804
        assert sum(1 for _ in inventory.open('r', encoding='utf-8')) == 1817
        assert proof['result'] == 'HASH_AFTER_COPY_PASS' and proof['file_count'] == 1817
        assert proof['inventory_sha256'] == sha(inventory)
        assert cleanup['archive_inventory_sha256'] == proof['inventory_sha256']
        assert cleanup['file_count'] == 1817
        assert cleanup['deleted_raw_leaf'] == f'/home/zyc/ocb_r2_s2_discovery/{run_id}'
        archive = ARCHIVE / run_id
        assert archive.is_dir()
        archive_files = [p for p in archive.rglob('*') if p.is_file()]
        assert len(archive_files) == 1817 and all(p.stat().st_size > 0 for p in archive_files)
        if int(row['replicate_index']) == 1:
            s1_output = S1_RUNS / f'{run_id}.OUTPUT_SHA256SUMS.tsv'
            with s1_output.open(newline='', encoding='utf-8') as f:
                s1_hashes = [r['sha256'] for r in csv.DictReader(f, delimiter='\t')]
            with output.open(newline='', encoding='utf-8') as f:
                s2_hashes = [r['sha256'] for r in csv.DictReader(f, delimiter='\t')]
            assert len(s1_hashes) == len(s2_hashes) == 1803 and s1_hashes == s2_hashes
            parity_configs += 1
        summary.append({
            'run_id': run_id, 'house': row['house'], 'source_id': row['source_id'],
            'wind_id': row['wind_id'], 'master_seed': row['master_seed'],
            'record_count': qc['record_count'], 'first_time_s': qc['first_time_s'],
            'last_time_s': qc['last_time_s'], 'nonempty_filament_records': qc['nonempty_filament_records'],
            'archive_file_count': proof['file_count'], 'archive_inventory_sha256': proof['inventory_sha256'],
            'decision': 'PASS',
        })
    assert len({r['master_seed'] for r in summary}) == 32
    assert sum(r['house'] == 'House01' for r in summary) == 16
    assert sum(r['house'] == 'House02' for r in summary) == 16
    assert parity_configs == 8
    with (EVIDENCE / 'H03_SEALED_STATIC_READINESS.tsv').open(newline='', encoding='utf-8') as f:
        h03 = list(csv.DictReader(f, delimiter='\t'))
    assert len(h03) == 4 and all(r['status'] == 'SEALED_NOT_RUN' for r in h03)
    assert len(list(ARCHIVE.glob('ocb_r2_cfg0[89]*'))) == 0
    assert len(list(ARCHIVE.glob('ocb_r2_cfg*_r0[5-8]'))) == 0
    result = EVIDENCE / 'OCB_R2_S2_DISCOVERY_RESULTS.tsv'
    with result.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(summary)
    report = REPO / 'research/ocb_r2/OCB_R2_S2_DISCOVERY_DATASET_REPORT.md'
    report.write_text(
        '# OCB-R2 S2 discovery dataset qualification\n\n'
        '**Decision: OCB_R2_S2_DISCOVERY_DATASET_PASS.**\n\n'
        f'- Runlist: 32 rows, frozen before S2 plume generation in commit `{FREEZE_COMMIT}`; SHA256 `{EXPECTED_RUNLIST}`.\n'
        f'- Frozen configuration SHA256: `{EXPECTED_CONFIGS}`.\n'
        f'- Generator binary SHA256: `{EXPECTED_BINARY}`.\n'
        '- House01 16/16 and House02 16/16 discovery runs passed. Eight original source/wind configurations have four frozen seeds each.\n'
        '- Every run has 1803 native records from 0 to 999.502991 s, 1802 nonempty filament records, all 11 legal wind states, finite parsed filament values, and complete asset/seed provenance.\n'
        '- The eight replicate-1 scientific output hash lists exactly match their S1 runs, 1803/1803 records for every configuration.\n'
        '- Each 1817-file raw run was archived at `C:\\GADEN_OCB_R2_ARCHIVE\\s2_discovery` and SHA256-verified after copy before deleting its VM raw leaf. Small evidence and inventories remain in Git.\n'
        '- House01/House02 confirmation replicates 5-8 were not generated or opened. House03 remains `SEALED_NOT_RUN`.\n\n'
        'This is dataset qualification only. No PMFS, localization rank, dependence score, method evaluation, or main-innovation result was computed.\n'
        'The 32 discovery runs may be used in a separate, explicitly scoped discovery analysis; confirmation and H03 remain sealed.\n',
        encoding='utf-8',
    )
    print(json.dumps({'decision': 'OCB_R2_S2_DISCOVERY_DATASET_PASS', 'run_count': 32,
                      'results_sha256': sha(result), 'report_sha256': sha(report)}))


if __name__ == '__main__':
    main()
