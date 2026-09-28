"""Freeze and transfer the three Native-only pilot weights without relabeling them final."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import torch


ROOT = Path(__file__).resolve().parent
HOST = Path.home() / 'Desktop' / ('vm' + chr(0x6570) + chr(0x636e)) / 'BRG_V1_MODELS_20260928'
VM_DIR = '/home/zyc/brg_v1_models_20260928'
VM = 'zyc@192.168.111.128'
KEY = Path.home() / '.ssh' / 'id_ed25519_vm'
ARMS = {'candidate_gru': 'gru', 'brg': 'brg', 'brg_ungated': 'ungated'}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def command(argv: list[str]) -> str:
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed: {result.stderr[-1000:]}')
    return result.stdout.strip()


def main() -> None:
    pilot = json.loads((ROOT / 'quick_pilot_20260928' / 'PILOT_PRETRAIN_FREEZE.json').read_text())
    eval_freeze = ROOT / 'PILOT_EVAL_FREEZE.json'
    if (pilot['trainer_sha256'] != sha(ROOT / 'train_v1_native_pilot.py') or
            pilot['model_source_sha256'] != sha(ROOT / 'v0_reference' / 'model.py') or
            pilot['training_manifest_sha256'] != sha(ROOT / 'NATIVE_OPEN_EPISODE_INVENTORY_FROZEN.json') or
            not KEY.is_file() or shutil.disk_usage(HOST).free < 1_000_000_000):
        raise RuntimeError('pilot source, inputs, key, or host capacity drift')
    arms = {}
    for arm, variant in ARMS.items():
        source_dir = HOST / 'native_pilot' / arm
        source = source_dir / 'best.pt'
        summary_path = source_dir / 'summary.json'
        history_path = source_dir / 'history.json'
        summary = json.loads(summary_path.read_text())
        history = json.loads(history_path.read_text())
        ck = torch.load(source, map_location='cpu', weights_only=True)
        meta = ck['metadata']
        if (summary['status'] != 'V1_GPU_TRAINING_PHASE_COMPLETE_NOT_SCIENTIFIC_PASS' or
                summary['variant'] != variant or summary['phase'] != 'native_pilot' or
                summary['epochs'] != 10 or len(history) != 10 or
                summary['train_episodes'] != 40 or summary['dev_episodes'] != 8 or
                meta['deployment_status'] != 'NATIVE_ONLY_INITIAL_PILOT_NOT_FULL_V1' or
                meta['phase'] != 'native_pilot' or meta['variant'] != variant or
                meta['manifest_sha256'] != pilot['training_manifest_sha256'] or
                meta['model_source_sha256'] != pilot['model_source_sha256'] or
                meta['dev_source_update_nll'] != min(row['dev_source_update_nll'] for row in history) or
                summary['best_dev_source_update_nll'] != meta['dev_source_update_nll']):
            raise RuntimeError(f'pilot training summary/checkpoint mismatch: {arm}')
        target = HOST / f'pilot_{arm}_best.pt'
        if target.exists():
            if sha(target) != sha(source):
                raise RuntimeError(f'existing selected pilot checkpoint changed: {arm}')
        else:
            shutil.copy2(source, target)
        arms[arm] = {
            'path': f'{VM_DIR}/{target.name}', 'sha256': sha(target),
            'bytes': target.stat().st_size, 'variant': variant,
            'best_epoch': meta['epoch'],
            'best_dev_source_update_nll': summary['best_dev_source_update_nll'],
            'summary_sha256': sha(summary_path), 'history_sha256': sha(history_path),
        }
    result = {
        'status': 'BRG_V1_NATIVE_PILOT_MODELS_FROZEN_BEFORE_EVAL',
        'phase': 'native_pilot',
        'training_scope': '40 Native train and 8 Native dev episodes only',
        'training_manifest_sha256': pilot['training_manifest_sha256'],
        'trainer_sha256': pilot['trainer_sha256'],
        'model_source_sha256': pilot['model_source_sha256'],
        'evaluation_freeze_sha256': sha(eval_freeze),
        'checkpoint_selection': 'development source-update prefix NLL',
        'evaluation_cases_used_for_selection': False,
        'arms': arms,
    }
    target = HOST / 'PILOT_CHECKPOINT_FREEZE.json'
    payload = json.dumps(result, indent=2) + '\n'
    if target.exists():
        if target.read_text() != payload:
            raise RuntimeError('existing pilot model freeze changed')
    else:
        target.write_text(payload)
    command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM, f'mkdir -p {VM_DIR}'])
    for arm in ARMS:
        path = HOST / f'pilot_{arm}_best.pt'
        command(['scp', '-q', '-i', str(KEY), str(path), f'{VM}:{VM_DIR}/{path.name}'])
        remote_hash = command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                               f'sha256sum {VM_DIR}/{path.name}']).split()[0]
        if remote_hash != arms[arm]['sha256']:
            raise RuntimeError(f'VM pilot checkpoint SHA drift: {arm}')
    command(['scp', '-q', '-i', str(KEY), str(target), f'{VM}:{VM_DIR}/{target.name}'])
    remote_hash = command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                           f'sha256sum {VM_DIR}/{target.name}']).split()[0]
    if remote_hash != sha(target):
        raise RuntimeError('VM pilot model freeze SHA drift')
    print(json.dumps({'status': result['status'], 'manifest_sha256': sha(target),
                      'arms': {arm: arms[arm]['sha256'] for arm in ARMS}}))


if __name__ == '__main__':
    main()
