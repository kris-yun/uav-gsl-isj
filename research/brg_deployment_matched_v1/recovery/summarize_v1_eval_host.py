"""Summarize the frozen 8-plume x 4-arm VGR campaign from verified raw archives."""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import subprocess

import numpy as np

from collect_native_host import ROOT, ZSTD, sha
from evaluate_v1_host import ARCHIVE, RECEIPTS, ARMS


def archived_result(archive: Path, member: str) -> dict:
    decoder = subprocess.Popen([str(ZSTD), '-dc', str(archive)], stdout=subprocess.PIPE)
    assert decoder.stdout is not None
    extracted = subprocess.run(['tar', '-xOf', '-', member], stdin=decoder.stdout,
                               capture_output=True)
    decoder.stdout.close()
    if decoder.wait() or extracted.returncode:
        raise RuntimeError(f'failed reading archived result {archive.name}')
    return json.loads(extracted.stdout)


def summarize(rows: list[dict]) -> dict:
    errors = [r['final_source_error_m'] for r in rows
              if r['final_source_error_m'] is not None]
    return {
        'runs': len(rows),
        'geometric_success': sum(r['geometric_success'] for r in rows),
        'geometric_success_rate': float(np.mean([r['geometric_success'] for r in rows])),
        'finite_estimate_count': len(errors),
        'final_source_error_m_median_finite': float(np.median(errors)) if errors else None,
        'final_source_error_m_mean_finite': float(np.mean(errors)) if errors else None,
        'path_length_m_mean': float(np.mean([r['path_length_m'] for r in rows])),
        'path_length_m_median': float(np.median([r['path_length_m'] for r in rows])),
        'algorithm_declared_success': sum(r['algorithm_declared_success'] for r in rows),
        'timeout': sum(r['timeout'] for r in rows),
        'wrong_declaration': sum(r['wrong_declaration'] for r in rows),
        'failure_reasons': dict(sorted(Counter(r['failure_reason'] for r in rows).items())),
    }


def main() -> None:
    freeze_path = ROOT / 'V1_EVAL8_FROZEN_MANIFEST.json'
    freeze = json.loads(freeze_path.read_text())
    rows = []
    for case in freeze['cases']:
        ordinal, case_id = case['ordinal'], case['case_id']
        for arm in ARMS:
            stem = f'eval_{arm}_{ordinal:03d}_{case_id}'
            receipt_path = RECEIPTS / f'{stem}.json'
            archive = ARCHIVE / f'{stem}.tar.zst'
            if not receipt_path.is_file() or not archive.is_file():
                raise RuntimeError(f'frozen 32-run campaign incomplete at {stem}')
            receipt = json.loads(receipt_path.read_text())
            if sha(archive) != receipt['archive_sha256']:
                raise RuntimeError(f'eval archive checksum drift at {stem}')
            result = archived_result(archive, f'{stem}.json')
            if (result['case_id'] != case_id or result['arm'] != arm or
                    result['budget_s'] != 300 or
                    result['geometric_success'] != receipt['geometric_success'] or
                    result['final_source_error_m'] != receipt['final_source_error_m']):
                raise RuntimeError(f'eval receipt/result disagreement at {stem}')
            rows.append({'ordinal': ordinal, 'house': case['house'],
                         'wind': case['wind'], 'source_id': case['source_id'],
                         'archive_sha256': receipt['archive_sha256'], **result})
    if len(rows) != 32:
        raise RuntimeError('not exactly 32 frozen evaluation runs')
    by_arm = {arm: summarize([r for r in rows if r['arm'] == arm]) for arm in ARMS}
    by_house = {house: {arm: summarize([r for r in rows if r['house'] == house and r['arm'] == arm])
                        for arm in ARMS} for house in sorted({r['house'] for r in rows})}
    paired = {}
    for arm in ARMS[1:]:
        differences = []
        for case in freeze['cases']:
            ordinal = case['ordinal']
            current = next(r for r in rows if r['ordinal'] == ordinal and r['arm'] == arm)
            native = next(r for r in rows if r['ordinal'] == ordinal and r['arm'] == 'native_pmfs')
            differences.append(current['geometric_success'] - native['geometric_success'])
        paired[arm] = {'net_successes_vs_native': sum(differences),
                       'improved_cases': differences.count(1),
                       'harmed_cases': differences.count(-1),
                       'tied_cases': differences.count(0)}
    summary = {'status': 'BRG_V1_32_RUN_VGR_DEVELOPMENT_CAMPAIGN_COMPLETE',
               'frozen_eval_manifest_sha256': sha(freeze_path),
               'scope': '8 fixed OPEN plumes x 4 arms; VGR interactive loop, not Gazebo',
               'by_arm': by_arm, 'by_house': by_house, 'paired_vs_native': paired}
    out_dir = ARCHIVE / 'summary'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'BRG_V1_EVAL32_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
    columns = ['ordinal', 'case_id', 'house', 'wind', 'source_id', 'arm', 'status',
               'geometric_success', 'final_source_error_m', 'estimate_xy',
               'algorithm_declared_success', 'timeout', 'wrong_declaration',
               'declaration_time_s', 'first_navigation_within_0_5m_time_s',
               'path_length_m', 'measurement_count', 'hit_count',
               'navigation_failure_count', 'failure_reason', 'archive_sha256']
    with (out_dir / 'BRG_V1_EVAL32_RUNS.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in columns})
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
