#!/usr/bin/env python3
"""Read-only formal preflight for one frozen CPIR House bank.

It never opens world payloads beyond the already-produced integrity report.
It binds the bank summary/cell-manifest hashes to a House and records the
runtime cadence that must already have been recovered from the authoritative
paired PMFS parameter manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--house', choices=('H01', 'H02', 'H03'), required=True)
    parser.add_argument('--bank-root', type=Path, required=True)
    parser.add_argument('--integrity-report', type=Path, required=True)
    parser.add_argument('--steps-source-update', type=int, required=True,
                        help='Recover from the frozen paired PMFS parameter manifest; do not guess.')
    parser.add_argument('--max-warmup-iterations', type=int, required=True,
                        help='Recover from the frozen paired PMFS parameter manifest; do not guess.')
    parser.add_argument('--min-warmup-iterations', type=int, required=True,
                        help='Recover from the frozen paired PMFS parameter manifest; do not guess.')
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args()
    if args.steps_source_update < 0 or args.max_warmup_iterations <= 0 or args.min_warmup_iterations < 0:
        fail('CPIR_PREFLIGHT_RUNTIME_CADENCE_INVALID')
    if args.min_warmup_iterations > args.max_warmup_iterations:
        fail('CPIR_PREFLIGHT_WARMUP_ORDER')

    root = args.bank_root.resolve()
    report_path = args.integrity_report.resolve()
    summary_path = root / 'bank_summary.json'
    cell_path = root / 'cell_manifest.csv'
    if not root.is_dir() or not summary_path.is_file() or not cell_path.is_file():
        fail('CPIR_PREFLIGHT_BANK_FILES')
    if (root / 'IN_PROGRESS').exists():
        fail('CPIR_PREFLIGHT_IN_PROGRESS')
    if not report_path.is_file():
        fail('CPIR_PREFLIGHT_REPORT_MISSING')

    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    report = json.loads(report_path.read_text(encoding='utf-8'))
    summary_sha = sha256_file(summary_path)
    cell_sha = sha256_file(cell_path)

    if summary.get('contract') != 'CPIR_FULLGRID_LOOKUP_V1':
        fail('CPIR_PREFLIGHT_CONTRACT')
    if summary.get('verdict') != 'CPIR_FULLGRID_LOOKUP_PASS':
        fail('CPIR_PREFLIGHT_BANK_VERDICT')
    if summary.get('house') != args.house:
        fail('CPIR_PREFLIGHT_HOUSE')
    if int(summary.get('member_count', -1)) != 8 or int(summary.get('time_count', -1)) != 1500:
        fail('CPIR_PREFLIGHT_DIMENSIONS')
    keys = summary.get('prediction_transport_keys')
    if not isinstance(keys, list) or len(keys) != 8 or len(set(keys)) != 8:
        fail('CPIR_PREFLIGHT_PREDICTION_KEYS')
    if summary.get('prediction_rng_domain') != 'PF_DEI_V3_REGION_PLACEMENT_V1/train':
        fail('CPIR_PREFLIGHT_PREDICTION_DOMAIN')
    if summary.get('observation_rng_domain') != 'immutable_external_GADEN_dataset_world':
        fail('CPIR_PREFLIGHT_OBSERVATION_DOMAIN')
    if summary.get('cell_manifest_sha256') != cell_sha:
        fail('CPIR_PREFLIGHT_CELL_SHA_SUMMARY')

    if report.get('verdict') != 'CPIR_LOOKUP_INTEGRITY_PASS':
        fail('CPIR_PREFLIGHT_INTEGRITY_VERDICT')
    if report.get('house') != args.house:
        fail('CPIR_PREFLIGHT_INTEGRITY_HOUSE')
    if report.get('bank_summary_sha256') != summary_sha:
        fail('CPIR_PREFLIGHT_INTEGRITY_SUMMARY_SHA')
    if report.get('cell_manifest_sha256') != cell_sha:
        fail('CPIR_PREFLIGHT_INTEGRITY_CELL_SHA')

    house_contract = {
        'H01': {
            'environment_id': 'VGR_House01', 'dataset': 'VGR_House01',
            'config_id': '2,4-1_fast', 'source': (-0.40, -2.90, -0.30),
        },
        'H02': {
            'environment_id': 'VGR_House02', 'dataset': 'VGR_House02',
            'config_id': '3,5-1_fast', 'source': (0.00, -1.00, 0.20),
        },
        'H03': {
            'environment_id': 'VGR_House03', 'dataset': 'VGR_House03',
            'config_id': '1-2,5_fast', 'source': (-0.45, 1.90, -0.10),
        },
    }[args.house]

    result = {
        'verdict': 'CPIR_FORMAL_PREFLIGHT_PASS',
        'house': args.house,
        'bank_root': str(root),
        'integrity_report': str(report_path),
        'bank_summary_sha256': summary_sha,
        'cell_manifest_sha256': cell_sha,
        'prediction_transport_keys': keys,
        'prediction_rng_domain': summary['prediction_rng_domain'],
        'observation_rng_domain': summary['observation_rng_domain'],
        'observation_realization_sha256': summary.get('observation_realization_sha256'),
        'runtime_contract': {
            **house_contract,
            'stepsSourceUpdate': args.steps_source_update,
            'maxWarmupIterations': args.max_warmup_iterations,
            'minWarmupIterations': args.min_warmup_iterations,
            'deltaTime': 0.2,
            'maxUpdatesPerStop': 8,
            'measurement_block_samples': 10,
            'measurement_settle_samples': 0,
            'measurement_deduplicate_sim_timestamps': True,
            'th_gas_present': 0.1,
            'sensor_config': 'fopdt_tau1p2_dead0p4_noise0',
            'sensor_model_mode': 'dynamic',
        },
        'launch_args': {
            'cpir_lookup_root': str(root),
            'cpir_integrity_report': str(report_path),
            'cpir_expected_house': args.house,
            'cpir_expected_bank_summary_sha256': summary_sha,
            'cpir_expected_cell_manifest_sha256': cell_sha,
            'cpir_expected_steps_source_update': args.steps_source_update,
            'cpir_expected_max_warmup_iterations': args.max_warmup_iterations,
            'cpir_expected_min_warmup_iterations': args.min_warmup_iterations,
            'stepsSourceUpdate': args.steps_source_update,
            'maxWarmupIterations': args.max_warmup_iterations,
            'minWarmupIterations': args.min_warmup_iterations,
            'environment_id': house_contract['environment_id'],
            'dataset': house_contract['dataset'],
            'config_id': house_contract['config_id'],
            'source_x': house_contract['source'][0],
            'source_y': house_contract['source'][1],
            'source_z': house_contract['source'][2],
        },
        'claim_boundary': (
            'This proves file/domain provenance only. The source-update and '
            'warmup values are user-supplied recovered contract values; this '
            'script deliberately does not infer them from development replays. '
            'It also does not prove numerical identity separation between an '
            'external immutable GADEN observation realization and every '
            'synthetic prediction draw because no hidden observation member id '
            'is available to runtime.'
        ),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
