#!/usr/bin/env python3
"""One frozen 300 s four-arm VGR development pilot run, then raw log package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/home/zyc/brg_v1_recovery_20260928')
ACTIVE = Path('/home/zyc/brg_v1_active_case_20260928')
LOGS = Path('/home/zyc/brg_v1_logs_20260928')
PACKAGES = Path('/home/zyc/brg_v1_collection_packages_20260928')
MODELS = Path('/home/zyc/brg_v1_models_20260928')
ARMS = ('native_pmfs', 'candidate_gru', 'brg', 'brg_ungated')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def frozen_case(ordinal: int):
    freeze = json.loads((ROOT / 'PILOT_EVAL_FREEZE.json').read_text())
    if (freeze['status'] != 'BRG_V1_NATIVE_ONLY_THREE_CASE_PILOT_FROZEN' or
            freeze['expected_run_count'] != 12 or
            [x['ordinal'] for x in freeze['cases']] != [9, 21, 65]):
        raise RuntimeError('three-case pilot manifest missing or changed')
    matches = [x for x in freeze['cases'] if x['ordinal'] == ordinal]
    if len(matches) != 1:
        raise RuntimeError('case outside frozen pilot three')
    path = ROOT / matches[0]['case_file']
    if sha(path) != matches[0]['case_file_sha256']:
        raise RuntimeError('frozen eval case hash drift')
    case = json.loads(path.read_text())
    if case['split'] != 'eval' or case['case_id'] != matches[0]['case_id']:
        raise RuntimeError('evaluation case identity mismatch')
    return path, case


def pilot_checkpoint(arm: str) -> Path | None:
    if arm == 'native_pmfs':
        return None
    freeze = json.loads((MODELS / 'PILOT_CHECKPOINT_FREEZE.json').read_text())
    if (freeze['status'] != 'BRG_V1_NATIVE_PILOT_MODELS_FROZEN_BEFORE_EVAL' or
            freeze['phase'] != 'native_pilot'):
        raise RuntimeError('pilot three-model freeze missing')
    item = freeze['arms'][arm]
    path = Path(item['path'])
    if path != MODELS / f'pilot_{arm}_best.pt' or sha(path) != item['sha256']:
        raise RuntimeError('pilot learned checkpoint SHA drift')
    return path


def paths(ordinal: int, case: dict, arm: str):
    stem = f'pilot_{arm}_{ordinal:03d}_{case["case_id"]}'
    return LOGS / (stem + '.json'), LOGS / (stem + '_raw'), PACKAGES / (stem + '.tar.zst')


def package(ordinal: int, arm: str) -> dict:
    _, case = frozen_case(ordinal)
    out, raw, archive = paths(ordinal, case, arm)
    if archive.exists() or not out.is_file() or not raw.is_dir():
        raise RuntimeError('evaluation result incomplete or archive exists')
    result = json.loads(out.read_text())
    binding_path = raw / 'runtime_binding.json'
    binding = json.loads(binding_path.read_text()) if binding_path.exists() else None
    ck = pilot_checkpoint(arm)
    if (result['case_id'] != case['case_id'] or result['arm'] != arm or
            result['budget_s'] != 300 or
            (result['status'] in ('completed', 'time_budget', 'navigation_failure')
             and not result['common_legal_support_matches']) or
            (binding is None and result['status'] not in ('service_error', 'algorithm_error')) or
            (binding is not None and
             (binding['training_collection'] or binding['fixed_source_blind_coverage'] or
              (ck is not None and str(ck) not in str(binding['argv']))))):
        raise RuntimeError('evaluation runtime contract mismatch')
    PACKAGES.mkdir(parents=True, exist_ok=True)
    tar = subprocess.Popen(['tar', '-C', str(LOGS), '-cf', '-', out.name, raw.name],
                           stdout=subprocess.PIPE)
    assert tar.stdout is not None
    zstd = subprocess.run(['zstd', '-T1', '-1', '-o', str(archive)],
                          stdin=tar.stdout, capture_output=True, text=True)
    tar.stdout.close()
    if tar.wait() or zstd.returncode:
        raise RuntimeError('evaluation tar/zstd failed')
    receipt = {'status': 'BRG_V1_PILOT_RUN_PACKAGED', 'ordinal': ordinal,
               'case_id': case['case_id'], 'arm': arm,
               'archive': str(archive), 'archive_bytes': archive.stat().st_size,
               'archive_sha256': sha(archive),
               'checkpoint_sha256': sha(ck) if ck else None,
               'geometric_success': result['geometric_success'],
               'final_source_error_m': result['final_source_error_m'],
               'algorithm_declared_success': result['algorithm_declared_success'],
               'timeout': result['timeout'], 'wrong_declaration': result['wrong_declaration'],
               'status_detail': result['status'], 'failure_reason': result['failure_reason'],
               'wall_time_s': result['wall_time_s']}
    print(json.dumps(receipt), flush=True)
    return receipt


def evaluate(ordinal: int, arm: str) -> dict:
    case_file, case = frozen_case(ordinal)
    if arm not in ARMS or not Path(case['realization']).is_dir():
        raise RuntimeError('unknown arm or native plume not restored')
    ck = pilot_checkpoint(arm)
    out, raw, archive = paths(ordinal, case, arm)
    if out.exists() or raw.exists() or archive.exists():
        raise RuntimeError('refuse to overwrite evaluation run')
    command = ['python3', str(ROOT / 'bind_v1_case_vm.py'), '--arm', arm,
               '--case-file', str(case_file), '--budget-s', '300',
               '--output', str(out), '--domain', '225', '--realtime-factor', '5']
    if ck:
        command += ['--checkpoint', str(ck)]
    subprocess.run(command, check=True)
    result = json.loads(out.read_text())
    if result['status'] == 'infrastructure_error':
        raise RuntimeError('evaluation infrastructure stop; preserve raw case')
    return package(ordinal, arm)


def cleanup(ordinal: int, arm: str, expected_sha: str) -> dict:
    _, case = frozen_case(ordinal)
    out, raw, archive = paths(ordinal, case, arm)
    if len(expected_sha) != 64 or sha(archive) != expected_sha:
        raise RuntimeError('VM eval archive SHA mismatch; preserving raw copy')
    active = ACTIVE / case['case_id']
    if active.resolve().parent != ACTIVE.resolve() or raw.resolve().parent != LOGS.resolve():
        raise RuntimeError('cleanup target escaped intended directory')
    for target in (active, out, raw, archive):
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    result = {'status': 'VERIFIED_EVAL_WORK_COPY_REMOVED',
              'ordinal': ordinal, 'arm': arm, 'case_id': case['case_id']}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('evaluate', 'cleanup'))
    ap.add_argument('ordinal', type=int)
    ap.add_argument('arm', choices=ARMS)
    ap.add_argument('expected_sha', nargs='?')
    args = ap.parse_args()
    if args.action == 'evaluate':
        evaluate(args.ordinal, args.arm)
    else:
        if not args.expected_sha:
            raise RuntimeError('cleanup requires host-verified archive SHA')
        cleanup(args.ordinal, args.arm, args.expected_sha)


if __name__ == '__main__':
    main()
