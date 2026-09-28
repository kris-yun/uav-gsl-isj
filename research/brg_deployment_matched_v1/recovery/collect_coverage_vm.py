#!/usr/bin/env python3
"""Collect one frozen, source-blind VGR map-coverage route on an OPEN plume."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from collect_native_vm import ACTIVE, LOGS, PACKAGES, ROOT, case_for, sha


def paths(ordinal: int, case: dict):
    stem = f'coverage_{ordinal:03d}_{case["case_id"]}'
    out = LOGS / (stem + '.json')
    raw = LOGS / (stem + '_raw')
    episode = LOGS / (stem + '_episode.npz')
    archive = PACKAGES / (stem + '.tar.zst')
    return out, raw, episode, archive


def package(ordinal: int) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    meta = episode.with_suffix('.json')
    if archive.exists() or not all(x.exists() for x in (out, raw, episode, meta)):
        raise RuntimeError('coverage files incomplete or archive already exists')
    result = json.loads(out.read_text())
    episode_meta = json.loads(meta.read_text())
    binding = json.loads((raw / 'runtime_binding.json').read_text())
    if (not result['fixed_source_blind_coverage'] or
            not binding['fixed_source_blind_coverage'] or
            binding['effective_launch_args']['coverage_goal_file'] !=
                '/home/zyc/brg_v1_recovery_20260928/coverage_routes/COVERAGE_STOP_GOALS_FREEZE_V3.json' or
            binding['effective_launch_args']['coverage_environment_index'] !=
                str(case['environment_index']) or
            'open_loop_profile' in binding['effective_launch_args'] or
            episode_meta['policy'] != 'coverage' or
            episode_meta['case_id'] != case['case_id']):
        raise RuntimeError('source-blind coverage policy binding mismatch')
    goal_trace = raw / 'coverage_goal_trace.csv'
    if not goal_trace.is_file() or goal_trace.stat().st_size < 70:
        raise RuntimeError('stop-goal coverage trace missing')
    PACKAGES.mkdir(parents=True, exist_ok=True)
    tar = subprocess.Popen(['tar', '-C', str(LOGS), '-cf', '-',
                            out.name, raw.name, episode.name, meta.name],
                           stdout=subprocess.PIPE)
    assert tar.stdout is not None
    zstd = subprocess.run(['zstd', '-T1', '-1', '-o', str(archive)],
                          stdin=tar.stdout, capture_output=True, text=True)
    tar.stdout.close()
    if tar.wait() or zstd.returncode:
        raise RuntimeError('coverage package tar/zstd failed')
    receipt = {'status': 'VGR_COVERAGE_COLLECTION_PACKAGE_READY', 'ordinal': ordinal,
               'case_id': case['case_id'], 'split': case['split'], 'archive': str(archive),
               'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive),
               'episode_sha256': sha(episode), 'event_count': episode_meta['events'],
               'source_update_prefixes': episode_meta['source_update_prefixes'],
               'candidate_support_count': episode_meta['candidate_count'],
               'wall_time_s': result['wall_time_s'], 'scientific_result': False}
    print(json.dumps(receipt), flush=True)
    return receipt


def collect(ordinal: int) -> dict:
    case_file, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if not Path(case['realization']).is_dir():
        raise RuntimeError('native realization must be restored first')
    if any(x.exists() for x in (out, raw, episode, archive)):
        raise RuntimeError('refuse to overwrite an existing coverage collection')
    subprocess.run(['python3', str(ROOT / 'bind_v1_case_vm.py'),
                    '--arm', 'native_pmfs', '--case-file', str(case_file),
                    '--budget-s', '300', '--output', str(out), '--domain', '225',
                    '--training-collection', '--coverage', '--realtime-factor', '5'], check=True)
    result = json.loads(out.read_text())
    if result['status'] not in ('completed', 'time_budget') or not result['common_legal_support_matches']:
        raise RuntimeError('coverage collection failed; preserving raw logs')
    subprocess.run(['python3', str(ROOT / 'encode_v1_episode_vm.py'),
                    '--case-file', str(case_file), '--raw-run', str(raw),
                    '--policy', 'coverage', '--output', str(episode)], check=True)
    return package(ordinal)


def resume_encode(ordinal: int) -> dict:
    case_file, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if not out.is_file() or not raw.is_dir() or episode.exists() or archive.exists():
        raise RuntimeError('no complete unencoded coverage run to resume')
    result = json.loads(out.read_text())
    if result['case_id'] != case['case_id'] or result['status'] not in ('completed', 'time_budget'):
        raise RuntimeError('coverage run invalid; preserving raw logs')
    subprocess.run(['python3', str(ROOT / 'encode_v1_episode_vm.py'),
                    '--case-file', str(case_file), '--raw-run', str(raw),
                    '--policy', 'coverage', '--output', str(episode)], check=True)
    return package(ordinal)


def cleanup(ordinal: int, expected_sha: str) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if len(expected_sha) != 64 or sha(archive) != expected_sha:
        raise RuntimeError('VM package SHA mismatch; preserving work copy')
    active = ACTIVE / case['case_id']
    if active.resolve().parent != ACTIVE.resolve() or raw.resolve().parent != LOGS.resolve():
        raise RuntimeError('cleanup target escaped intended directory')
    for target in (active, out, raw, episode, episode.with_suffix('.json'), archive):
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    result = {'status': 'VERIFIED_COVERAGE_WORK_COPY_REMOVED', 'ordinal': ordinal,
              'case_id': case['case_id']}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('collect', 'resume-encode', 'cleanup'))
    ap.add_argument('ordinal', type=int)
    ap.add_argument('expected_sha', nargs='?')
    args = ap.parse_args()
    if args.action == 'collect':
        collect(args.ordinal)
    elif args.action == 'resume-encode':
        resume_encode(args.ordinal)
    else:
        if not args.expected_sha:
            raise RuntimeError('cleanup requires host-verified SHA')
        cleanup(args.ordinal, args.expected_sha)


if __name__ == '__main__':
    main()
