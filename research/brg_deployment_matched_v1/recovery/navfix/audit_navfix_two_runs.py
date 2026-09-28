#!/usr/bin/env python3
"""Independently summarize the two frozen navigation-repair raw archives."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_archive(path: Path, zstd: Path) -> dict[str, bytes]:
    proc = subprocess.Popen([str(zstd), '-dc', str(path)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    wanted = {'navigation_trace.csv', 'sim_pose_trace.csv', 'measurement_events.csv',
              'beliefs.jsonl', 'launch.log', 'runtime_binding.json',
              'sidecar_events.jsonl'}
    found: dict[str, bytes] = {}
    with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
        for member in archive:
            if not member.isfile():
                continue
            parts = Path(member.name).parts
            if len(parts) == 1 and member.name.endswith('.json'):
                key = 'result.json'
            elif len(parts) == 2 and parts[1] in wanted:
                key = parts[1]
            else:
                continue
            assert key not in found
            stream = archive.extractfile(member)
            assert stream is not None
            found[key] = stream.read()
    proc.stdout.close()
    if proc.wait():
        raise RuntimeError(f'zstd failed: {path}')
    return found


def rows(data: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(data.decode())))


def audit(path: Path, receipt: dict, zstd: Path) -> dict:
    assert path.is_file() and path.stat().st_size == receipt['archive_bytes']
    assert sha(path) == receipt['archive_sha256']
    data = read_archive(path, zstd)
    nav = rows(data['navigation_trace.csv'])
    pose = rows(data['sim_pose_trace.csv'])
    events = rows(data['measurement_events.csv'])
    beliefs = [json.loads(line) for line in data['beliefs.jsonl'].splitlines() if line]
    log = data['launch.log'].decode(errors='replace')
    result = json.loads(data['result.json'])
    binding = json.loads(data['runtime_binding.json'])
    sent = [row for row in nav if row['event'] == 'SENT']
    done = [row for row in nav if row['event'] == 'RESULT']
    goals = {(round(float(row['goal_x']), 3), round(float(row['goal_y']), 3)) for row in sent}
    positions = {(round(float(row['robot_x']), 3), round(float(row['robot_y']), 3)) for row in events}
    poses = {(round(float(row['x']), 3), round(float(row['y']), 3)) for row in pose}
    maps = {hashlib.sha256(json.dumps(row['source_map']).encode()).hexdigest()
            for row in beliefs}
    sidecar_lines = data.get('sidecar_events.jsonl', b'').splitlines()
    sidecar_status = {}
    for line in sidecar_lines:
        status = json.loads(line).get('status', '?')
        sidecar_status[status] = sidecar_status.get(status, 0) + 1
    summary = {
        'arm': result['arm'], 'case_id': result['case_id'],
        'archive_bytes': path.stat().st_size, 'archive_sha256': sha(path),
        'candidate_support_count': binding['candidate_support_count'],
        'candidate_support_id': binding['bank_id'],
        'brg_enabled': binding['effective_launch_args']['brg_enabled'],
        'geometric_success': result['geometric_success'],
        'final_source_error_m': result['final_source_error_m'],
        'algorithm_declared_success': result['algorithm_declared_success'],
        'timeout': result['timeout'], 'status': result['status'],
        'navigation_sent': len(sent), 'navigation_results': len(done),
        'navigation_succeeded': sum(row['outcome'] == 'SUCCEEDED' for row in done),
        'unique_goals': len(goals),
        'origin_goals': sum(abs(x) < 1e-9 and abs(y) < 1e-9 for x, y in goals),
        'pose_count': len(pose), 'unique_poses': len(poses),
        'measurement_count': len(events), 'unique_measurement_positions': len(positions),
        'belief_rows': len(beliefs), 'unique_source_maps': len(maps),
        'plan_requests': log.count('PLAN_CB: called with goal='),
        'plan_returns': log.count('PLAN_CB: returning '),
        'nonempty_plan_returns': sum(int(n) > 0 for n in re.findall(r'PLAN_CB: returning (\d+) poses', log)),
        'callback_errors': log.count('Error executing callback') + log.count('AttributeError:'),
        'no_valid_plan': log.count('PMFS_NO_VALID_PLAN'),
        'sidecar_status': sidecar_status,
        'first_goal': sent[0] if sent else None,
        'last_goal': sent[-1] if sent else None,
    }
    assert summary['candidate_support_count'] == 596
    assert summary['navigation_sent'] == summary['navigation_succeeded']
    assert summary['plan_requests'] == summary['plan_returns'] == summary['nonempty_plan_returns']
    assert summary['origin_goals'] == summary['callback_errors'] == summary['no_valid_plan'] == 0
    assert summary['unique_poses'] > 1 and summary['unique_measurement_positions'] > 1
    assert summary['unique_source_maps'] > 1
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archives', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--zstd', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = []
    for arm in ('native_pmfs', 'brg'):
        receipt_paths = list(args.receipts.glob(f'navfix_{arm}_009_*.json'))
        assert len(receipt_paths) == 1
        receipt = json.loads(receipt_paths[0].read_text())
        archive = args.archives / (receipt_paths[0].stem + '.tar.zst')
        output.append(audit(archive, receipt, args.zstd))
    assert output[0]['candidate_support_id'] == output[1]['candidate_support_id']
    report = {'status': 'TWO_RUN_NAVIGATION_INTEGRITY_PASS',
              'scope': 'one inspected development case, Native vs frozen BRG',
              'runs': output}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
