#!/usr/bin/env python3
"""Package the two repaired pilot runs and their frozen provenance for review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
RECOVERY = HERE.parent
VM_DATA = Path('C:/Users/50176/Desktop/vm数据')
STAGING = Path('D:/ZYC/A-gas/_staging/BRG_PILOT_NAVFIX_20260928')
OUTPUT = VM_DATA / 'BRG_NAVFIX_CASE009_REVIEW_20260928.zip'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if OUTPUT.exists():
        raise RuntimeError(f'refuse to overwrite review package: {OUTPUT}')
    inputs: list[tuple[str, Path]] = []
    for name in (
        'NAVFIX_EXECUTION_CONTRACT_20260928.md', 'NAVFIX_PRE_RUN_FREEZE.json',
        'NAVFIX_TWO_RUN_AUDIT.json', 'NAVFIX_TWO_RUN_REPORT_20260928.md',
        'ROS_PATH_ALIAS_MINIMAL.patch', 'PMFS_NO_VALID_PLAN.patch',
        'live_path_callback_smoke.py', 'audit_navfix_two_runs.py',
        'package_navfix_review.py',
    ):
        inputs.append((f'navfix/{name}', HERE / name))
    for name in ('bind_v1_case_vm.py', 'evaluate_v1_navfix_vm.py',
                 'evaluate_v1_navfix_host.py', 'serve_v1_vm.py',
                 'PILOT_EVAL_FREEZE.json'):
        inputs.append((f'code_and_freeze/{name}', RECOVERY / name))
    case = RECOVERY / 'v1_cases/009_House01_1,3-2,4_fast_pmfs_26_36_seed1453872.json'
    inputs.append(('code_and_freeze/case009.json', case))
    for receipt in sorted((RECOVERY / 'navfix_eval_collection_receipts').glob('*.json')):
        inputs.append((f'receipts/{receipt.name}', receipt))
    if len(list((RECOVERY / 'navfix_eval_collection_receipts').glob('*.json'))) != 2:
        raise RuntimeError('expected exactly two repaired pilot receipts')
    for archive in sorted((VM_DATA / 'BRG_V1_NAVFIX2_20260928').glob('*.tar.zst')):
        inputs.append((f'raw_runs/{archive.name}', archive))
    if len(list((VM_DATA / 'BRG_V1_NAVFIX2_20260928').glob('*.tar.zst'))) != 2:
        raise RuntimeError('expected exactly two repaired raw archives')
    inputs += [
        ('code_and_freeze/PILOT_CHECKPOINT_FREEZE.json',
         VM_DATA / 'BRG_V1_MODELS_20260928/PILOT_CHECKPOINT_FREEZE.json'),
        ('code_and_freeze/pilot_brg_best.pt',
         VM_DATA / 'BRG_V1_MODELS_20260928/pilot_brg_best.pt'),
        ('code_and_freeze/env_0_bank.npz', STAGING / 'env_0_bank.npz'),
        ('prior/BRG_V1_THREE_CASE_PILOT_REVIEW_V2_20260928.zip',
         VM_DATA / 'BRG_V1_THREE_CASE_PILOT_REVIEW_V2_20260928.zip'),
        ('input/BRG_PILOT_NAVIGATION_FIX_AND_LITERATURE_20260928.zip',
         Path('C:/Users/50176/Downloads/BRG_PILOT_NAVIGATION_FIX_AND_LITERATURE_20260928.zip')),
    ]
    expected = {
        'prior/BRG_V1_THREE_CASE_PILOT_REVIEW_V2_20260928.zip':
        '5b3f1d30a378c16e3cb0be7255faa9fb0234e8a394bbc86a7a1dbd127b26f5b8',
        'input/BRG_PILOT_NAVIGATION_FIX_AND_LITERATURE_20260928.zip':
        '05a94ad072eb6053f83a1326baaf1e2addab5b7354ada762935f3438eb76112b',
        'code_and_freeze/env_0_bank.npz':
        'bf213e252dd44dde1077c678f881bf703e2c7ab86144e569bb5d581bf1f2d390',
        'code_and_freeze/pilot_brg_best.pt':
        'ee57607060f7241bdc24edb2d71e97a2b6c5c0de1901b2d1462d5034dc5c2289',
    }
    output_hashes = {}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as review:
        for name, path in inputs:
            data = path.read_bytes()
            digest = sha(data)
            if name in expected and digest != expected[name]:
                raise RuntimeError(f'frozen input SHA mismatch: {name}')
            output_hashes[name] = digest
            mode = zipfile.ZIP_STORED if name.endswith(('.zip', '.zst', '.pt', '.npz')) else zipfile.ZIP_DEFLATED
            review.writestr(name, data, compress_type=mode)
        review.writestr('SHA256SUMS', ''.join(
            f'{digest}  {name}\n' for name, digest in sorted(output_hashes.items())
        ).encode())
    with zipfile.ZipFile(OUTPUT) as review:
        assert review.testzip() is None
        for name, digest in output_hashes.items():
            assert sha(review.read(name)) == digest
    print(json.dumps({'path': str(OUTPUT), 'bytes': OUTPUT.stat().st_size,
                      'sha256': sha(OUTPUT.read_bytes()), 'member_count': len(output_hashes) + 1}, indent=2))


if __name__ == '__main__':
    main()
