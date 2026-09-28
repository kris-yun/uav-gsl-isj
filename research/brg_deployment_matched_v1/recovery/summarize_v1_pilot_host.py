"""Summarize complete four-arm case blocks from the Native-only VGR pilot."""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import subprocess

import numpy as np

from collect_native_host import ROOT, ZSTD, sha
from evaluate_v1_pilot_host import ARCHIVE, RECEIPTS, ARMS


def archived_result(archive: Path, member: str) -> dict:
    decoder = subprocess.Popen([str(ZSTD), '-dc', str(archive)], stdout=subprocess.PIPE)
    assert decoder.stdout is not None
    extracted = subprocess.run(['tar', '-xOf', '-', member], stdin=decoder.stdout,
                               capture_output=True)
    decoder.stdout.close()
    if decoder.wait() or extracted.returncode:
        raise RuntimeError(f'failed reading archived pilot result {archive.name}')
    return json.loads(extracted.stdout)


def arm_summary(rows: list[dict]) -> dict:
    errors = [r['final_source_error_m'] for r in rows
              if r['final_source_error_m'] is not None]
    return {
        'runs': len(rows),
        'geometric_success': sum(r['geometric_success'] for r in rows),
        'finite_estimate_count': len(errors),
        'final_source_error_m_median_finite': float(np.median(errors)) if errors else None,
        'path_length_m_mean': float(np.mean([r['path_length_m'] for r in rows])),
        'algorithm_declared_success': sum(r['algorithm_declared_success'] for r in rows),
        'timeout': sum(r['timeout'] for r in rows),
        'wrong_declaration': sum(r['wrong_declaration'] for r in rows),
        'failure_reasons': dict(sorted(Counter(r['failure_reason'] for r in rows).items())),
    }


def main() -> None:
    freeze_path = ROOT / 'PILOT_EVAL_FREEZE.json'
    freeze = json.loads(freeze_path.read_text())
    model_freeze = ARCHIVE.parent / 'BRG_V1_MODELS_20260928' / 'PILOT_CHECKPOINT_FREEZE.json'
    if (freeze['status'] != 'BRG_V1_NATIVE_ONLY_THREE_CASE_PILOT_FROZEN' or
            [x['ordinal'] for x in freeze['cases']] != [9, 21, 65] or
            not model_freeze.is_file()):
        raise RuntimeError('pilot freeze missing')
    rows = []
    completed = []
    for case in freeze['cases']:
        ordinal, case_id = case['ordinal'], case['case_id']
        case_rows = []
        for arm in ARMS:
            stem = f'pilot_{arm}_{ordinal:03d}_{case_id}'
            receipt_path = RECEIPTS / f'{stem}.json'
            archive = ARCHIVE / f'{stem}.tar.zst'
            if not receipt_path.is_file() and not archive.is_file():
                continue
            if not receipt_path.is_file() or not archive.is_file():
                raise RuntimeError(f'pilot archive/receipt incomplete at {stem}')
            receipt = json.loads(receipt_path.read_text())
            if sha(archive) != receipt['archive_sha256']:
                raise RuntimeError(f'pilot archive checksum drift at {stem}')
            result = archived_result(archive, f'{stem}.json')
            if (result['case_id'] != case_id or result['arm'] != arm or
                    result['budget_s'] != 300 or
                    result['geometric_success'] != receipt['geometric_success'] or
                    result['final_source_error_m'] != receipt['final_source_error_m']):
                raise RuntimeError(f'pilot receipt/result disagreement at {stem}')
            case_rows.append({'ordinal': ordinal, 'house': case['house'],
                              'wind': case['wind'], 'source_id': case['source_id'],
                              'archive_sha256': receipt['archive_sha256'], **result})
        if case_rows:
            if len(case_rows) != 4:
                raise RuntimeError(f'pilot case {ordinal} has {len(case_rows)}/4 arms')
            completed.append(ordinal)
            rows.extend(case_rows)
    if completed not in ([9], [9, 21], [9, 21, 65]):
        raise RuntimeError(f'pilot case order or completeness changed: {completed}')
    by_arm = {arm: arm_summary([r for r in rows if r['arm'] == arm]) for arm in ARMS}
    paired = {}
    for arm in ARMS[1:]:
        differences = []
        for ordinal in completed:
            current = next(r for r in rows if r['ordinal'] == ordinal and r['arm'] == arm)
            native = next(r for r in rows if r['ordinal'] == ordinal and r['arm'] == 'native_pmfs')
            differences.append(current['geometric_success'] - native['geometric_success'])
        paired[arm] = {'net_successes_vs_native': sum(differences),
                       'improved_cases': differences.count(1),
                       'harmed_cases': differences.count(-1),
                       'tied_cases': differences.count(0)}
    summary = {
        'status': 'BRG_V1_NATIVE_ONLY_THREE_CASE_DEVELOPMENT_PILOT_PARTIAL' if len(completed) < 3
                  else 'BRG_V1_NATIVE_ONLY_THREE_CASE_DEVELOPMENT_PILOT_COMPLETE',
        'frozen_pilot_manifest_sha256': sha(freeze_path),
        'pilot_checkpoint_freeze_sha256': sha(model_freeze),
        'scope': 'fixed OPEN plumes x four arms; interactive VGR, not Gazebo',
        'interpretation': 'development examples only, not a scientific significance gate',
        'completed_ordinals': completed,
        'by_arm': by_arm,
        'paired_vs_native': paired,
    }
    out_dir = ARCHIVE / 'summary'
    out_dir.mkdir(exist_ok=True)
    tag = f'{len(completed)}CASE'
    summary_path = out_dir / f'BRG_V1_PILOT_{tag}_SUMMARY.json'
    runs_path = out_dir / f'BRG_V1_PILOT_{tag}_RUNS.csv'
    if summary_path.exists() or runs_path.exists():
        raise RuntimeError('refuse to overwrite existing pilot summary')
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    columns = ['ordinal', 'case_id', 'house', 'wind', 'source_id', 'arm', 'status',
               'geometric_success', 'final_source_error_m', 'estimate_xy',
               'algorithm_declared_success', 'timeout', 'wrong_declaration',
               'declaration_time_s', 'first_navigation_within_0_5m_time_s',
               'path_length_m', 'measurement_count', 'hit_count',
               'navigation_failure_count', 'failure_reason', 'archive_sha256']
    with runs_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in columns})
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
