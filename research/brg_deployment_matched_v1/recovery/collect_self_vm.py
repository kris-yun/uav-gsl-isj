#!/usr/bin/env python3
"""One authorized warm-policy self trajectory on a frozen training plume."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from collect_native_vm import ACTIVE, LOGS, PACKAGES, ROOT, case_for, sha

ARMS = ('candidate_gru', 'brg', 'brg_ungated')
MODEL_ROOT = Path('/home/zyc/brg_v1_models_20260928')


def checkpoint(arm: str) -> Path:
    freeze = json.loads((MODEL_ROOT / 'WARM_CHECKPOINT_FREEZE.json').read_text())
    if freeze['status'] != 'BRG_V1_WARM_MODELS_FROZEN':
        raise RuntimeError('warm rollout checkpoint freeze missing')
    item = freeze['arms'][arm]
    path = Path(item['path'])
    if path != MODEL_ROOT / f'warm_{arm}_best.pt' or sha(path) != item['sha256']:
        raise RuntimeError('warm checkpoint SHA drift')
    return path


def paths(ordinal: int, case: dict, arm: str):
    stem = f'self_{arm}_{ordinal:03d}_{case["case_id"]}'
    out = LOGS / (stem + '.json')
    raw = LOGS / (stem + '_raw')
    episode = LOGS / (stem + '_episode.npz')
    archive = PACKAGES / (stem + '.tar.zst')
    return out, raw, episode, archive


def package(ordinal: int, arm: str) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case, arm)
    meta = episode.with_suffix('.json')
    if archive.exists() or not all(x.exists() for x in (out, raw, episode, meta)):
        raise RuntimeError('self trajectory incomplete or archive exists')
    result = json.loads(out.read_text())
    episode_meta = json.loads(meta.read_text())
    binding = json.loads((raw / 'runtime_binding.json').read_text())
    ck = checkpoint(arm)
    if (case['split'] != 'train' or result['arm'] != arm or
            episode_meta['policy'] != arm or
            episode_meta['case_id'] != case['case_id'] or
            binding['fixed_source_blind_coverage'] or
            not binding['training_collection'] or
            str(ck) not in str(binding['argv'])):
        raise RuntimeError('warm self rollout binding mismatch')
    PACKAGES.mkdir(parents=True, exist_ok=True)
    tar = subprocess.Popen(['tar', '-C', str(LOGS), '-cf', '-',
                            out.name, raw.name, episode.name, meta.name],
                           stdout=subprocess.PIPE)
    assert tar.stdout is not None
    zstd = subprocess.run(['zstd', '-T1', '-1', '-o', str(archive)],
                          stdin=tar.stdout, capture_output=True, text=True)
    tar.stdout.close()
    if tar.wait() or zstd.returncode:
        raise RuntimeError('self trajectory tar/zstd failed')
    receipt = {'status': 'VGR_WARM_SELF_COLLECTION_PACKAGE_READY',
               'ordinal': ordinal, 'case_id': case['case_id'], 'arm': arm,
               'split': 'train', 'archive': str(archive),
               'archive_bytes': archive.stat().st_size,
               'archive_sha256': sha(archive), 'episode_sha256': sha(episode),
               'checkpoint_sha256': sha(ck), 'event_count': episode_meta['events'],
               'source_update_prefixes': episode_meta['source_update_prefixes'],
               'candidate_support_count': episode_meta['candidate_count'],
               'wall_time_s': result['wall_time_s'], 'scientific_result': False}
    print(json.dumps(receipt), flush=True)
    return receipt


def collect(ordinal: int, arm: str) -> dict:
    case_file, case = case_for(ordinal)
    if case['split'] != 'train' or arm not in ARMS:
        raise RuntimeError('self collection limited to frozen training cases/three arms')
    ck = checkpoint(arm)
    out, raw, episode, archive = paths(ordinal, case, arm)
    if not Path(case['realization']).is_dir():
        raise RuntimeError('original native plume not restored')
    if any(x.exists() for x in (out, raw, episode, archive)):
        raise RuntimeError('refuse to overwrite self trajectory')
    subprocess.run(['python3', str(ROOT / 'bind_v1_case_vm.py'),
                    '--arm', arm, '--case-file', str(case_file),
                    '--budget-s', '300', '--output', str(out), '--domain', '225',
                    '--training-collection', '--checkpoint', str(ck),
                    '--realtime-factor', '5'], check=True)
    result = json.loads(out.read_text())
    if result['status'] not in ('completed', 'time_budget') or not result['common_legal_support_matches']:
        raise RuntimeError('warm self rollout failed; preserving raw logs')
    subprocess.run(['python3', str(ROOT / 'encode_v1_episode_vm.py'),
                    '--case-file', str(case_file), '--raw-run', str(raw),
                    '--policy', arm, '--output', str(episode)], check=True)
    return package(ordinal, arm)


def resume_encode(ordinal: int, arm: str) -> dict:
    case_file, case = case_for(ordinal)
    if case['split'] != 'train' or arm not in ARMS:
        raise RuntimeError('self collection limited to frozen training cases/three arms')
    checkpoint(arm)
    out, raw, episode, archive = paths(ordinal, case, arm)
    if not out.is_file() or not raw.is_dir() or episode.exists() or archive.exists():
        raise RuntimeError('no complete unencoded self trajectory to resume')
    result = json.loads(out.read_text())
    if (result['case_id'] != case['case_id'] or result['arm'] != arm or
            result['status'] not in ('completed', 'time_budget') or
            not result['common_legal_support_matches']):
        raise RuntimeError('self trajectory invalid; preserving raw logs')
    subprocess.run(['python3', str(ROOT / 'encode_v1_episode_vm.py'),
                    '--case-file', str(case_file), '--raw-run', str(raw),
                    '--policy', arm, '--output', str(episode)], check=True)
    return package(ordinal, arm)


def cleanup(ordinal: int, arm: str, expected_sha: str) -> dict:
    _, case = case_for(ordinal)
    out, raw, episode, archive = paths(ordinal, case, arm)
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
    result = {'status': 'VERIFIED_WARM_SELF_WORK_COPY_REMOVED',
              'ordinal': ordinal, 'arm': arm, 'case_id': case['case_id']}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('collect', 'resume-encode', 'cleanup'))
    ap.add_argument('ordinal', type=int)
    ap.add_argument('arm', choices=ARMS)
    ap.add_argument('expected_sha', nargs='?')
    args = ap.parse_args()
    if args.action == 'collect':
        collect(args.ordinal, args.arm)
    elif args.action == 'resume-encode':
        resume_encode(args.ordinal, args.arm)
    else:
        if not args.expected_sha:
            raise RuntimeError('cleanup requires host-verified SHA')
        cleanup(args.ordinal, args.arm, args.expected_sha)


if __name__ == '__main__':
    main()
