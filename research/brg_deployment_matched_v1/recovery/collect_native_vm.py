#!/usr/bin/env python3
"""Run and package one frozen OPEN VGR Native collection on the VM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/home/zyc/brg_v1_recovery_20260928')
CASES = ROOT / 'v1_cases'
ACTIVE = Path('/home/zyc/brg_v1_active_case_20260928')
LOGS = Path('/home/zyc/brg_v1_logs_20260928')
PACKAGES = Path('/home/zyc/brg_v1_collection_packages_20260928')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def case_for(ordinal: int) -> tuple[Path, dict]:
    hits = list(CASES.glob(f'{ordinal:03d}_*.json'))
    if len(hits) != 1:
        raise RuntimeError('frozen case file missing or ambiguous')
    case = json.loads(hits[0].read_text())
    if case['ordinal'] != ordinal or case['split'] not in ('train', 'dev'):
        raise RuntimeError('case is not in frozen training/development split')
    if not case['truth_in_support']:
        raise RuntimeError('training truth outside Native support')
    if Path(case['realization']) != ACTIVE / case['case_id'] / 'realization':
        raise RuntimeError('active realization binding changed')
    return hits[0], case


def paths(ordinal: int, case: dict) -> tuple[Path, Path, Path, Path]:
    stem = f'native_{ordinal:03d}_{case["case_id"]}'
    out = LOGS / (stem + '.json')
    raw = LOGS / (stem + '_raw')
    episode = LOGS / (stem + '_episode.npz')
    archive = PACKAGES / (stem + '.tar.zst')
    return out, raw, episode, archive


def collect(ordinal: int) -> dict:
    case_file, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if not Path(case['realization']).is_dir():
        raise RuntimeError('archived native realization must be restored first')
    if out.exists() or raw.exists() or episode.exists() or archive.exists():
        raise RuntimeError('refuse to overwrite an existing collection')
    # The ROS environment must already be sourced by the caller.
    run(['python3', str(ROOT / 'bind_v1_case_vm.py'), '--arm', 'native_pmfs',
         '--case-file', str(case_file), '--budget-s', '300', '--output', str(out),
         '--domain', '225', '--training-collection', '--realtime-factor', '5'])
    result = json.loads(out.read_text())
    if result['status'] not in ('completed', 'time_budget') or not result['common_legal_support_matches']:
        raise RuntimeError(f'Native collection failed; raw logs preserved: {result["status"]}')
    run(['python3', str(ROOT / 'encode_v1_episode_vm.py'), '--case-file', str(case_file),
         '--raw-run', str(raw), '--policy', 'native_pmfs', '--output', str(episode)])
    return package(ordinal)


def resume_encode(ordinal: int) -> dict:
    """Resume an already completed VGR run after an encoder-only audit fix."""
    case_file, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if not out.is_file() or not raw.is_dir() or episode.exists() or archive.exists():
        raise RuntimeError('no complete unencoded Native run to resume')
    result = json.loads(out.read_text())
    if (result['case_id'] != case['case_id'] or
            result['status'] not in ('completed', 'time_budget') or
            not result['common_legal_support_matches']):
        raise RuntimeError('completed Native result invalid; preserving raw logs')
    run(['python3', str(ROOT / 'encode_v1_episode_vm.py'), '--case-file', str(case_file),
         '--raw-run', str(raw), '--policy', 'native_pmfs', '--output', str(episode)])
    return package(ordinal)


def package(ordinal: int) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if archive.exists():
        raise RuntimeError('refuse to overwrite package')
    metadata = episode.with_suffix('.json')
    if not all(p.exists() for p in (out, raw, episode, metadata)):
        raise RuntimeError('collection files incomplete')
    result = json.loads(out.read_text())
    ep = json.loads(metadata.read_text())
    if ep['case_id'] != case['case_id'] or ep['bank_fingerprint'] != case['candidate_support_id']:
        raise RuntimeError('encoded episode/case mismatch')
    PACKAGES.mkdir(parents=True, exist_ok=True)
    member_names = [p.name for p in (out, raw, episode, metadata)]
    tar = subprocess.Popen(['tar', '-C', str(LOGS), '-cf', '-', *member_names],
                           stdout=subprocess.PIPE)
    assert tar.stdout is not None
    zstd = subprocess.run(['zstd', '-T1', '-1', '-o', str(archive)], stdin=tar.stdout,
                          capture_output=True, text=True)
    tar.stdout.close()
    tar_code = tar.wait()
    if tar_code or zstd.returncode:
        raise RuntimeError(f'collection package failed: {tar_code} {zstd.stderr[-500:]}')
    receipt = {'status': 'VGR_NATIVE_COLLECTION_PACKAGE_READY', 'ordinal': ordinal,
               'case_id': case['case_id'], 'split': case['split'], 'archive': str(archive),
               'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive),
               'episode_sha256': sha(episode), 'event_count': ep['events'],
               'source_update_prefixes': ep['source_update_prefixes'],
               'candidate_support_count': ep['candidate_count'],
               'wall_time_s': result['wall_time_s'], 'scientific_result': False}
    print(json.dumps(receipt), flush=True)
    return receipt


def cleanup(ordinal: int, expected_sha: str) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case)
    if len(expected_sha) != 64 or sha(archive) != expected_sha:
        raise RuntimeError('VM package SHA mismatch; preserving work copy')
    active = ACTIVE / case['case_id']
    targets = [active, out, raw, episode, episode.with_suffix('.json'), archive]
    # Exact frozen paths only; no recursive deletion of a computed parent.
    if active.resolve().parent != ACTIVE.resolve() or raw.resolve().parent != LOGS.resolve():
        raise RuntimeError('cleanup target escaped intended directory')
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    result = {'status': 'VERIFIED_NATIVE_WORK_COPY_REMOVED', 'ordinal': ordinal,
              'case_id': case['case_id'], 'host_verified_package_sha256': expected_sha}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('collect', 'resume-encode', 'package', 'cleanup'))
    ap.add_argument('ordinal', type=int)
    ap.add_argument('expected_sha', nargs='?')
    args = ap.parse_args()
    if args.action == 'collect':
        collect(args.ordinal)
    elif args.action == 'resume-encode':
        resume_encode(args.ordinal)
    elif args.action == 'package':
        package(args.ordinal)
    else:
        if args.expected_sha is None:
            raise RuntimeError('cleanup requires verified host package SHA')
        cleanup(args.ordinal, args.expected_sha)


if __name__ == '__main__':
    main()
