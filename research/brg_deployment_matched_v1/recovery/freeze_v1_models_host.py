"""Hash and transfer three common-input V1 checkpoints before any rollout/eval."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
HOST = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_MODELS_20260928')
VM_DIR = '/home/zyc/brg_v1_models_20260928'
VM = 'zyc@192.168.111.128'
KEY = Path.home() / '.ssh' / 'id_ed25519_vm'
ARMS = ('candidate_gru', 'brg', 'brg_ungated')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def command(argv: list[str]) -> str:
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f'{argv[0]} failed: {r.stderr[-1000:]}')
    return r.stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=('warm', 'final'))
    args = ap.parse_args()
    phase = args.phase
    HOST.mkdir(parents=True, exist_ok=True)
    if not KEY.is_file() or shutil.disk_usage(HOST).free < 2_000_000_000:
        raise RuntimeError('key or host model archive free space missing')
    arms = {}
    for arm in ARMS:
        variant = 'gru' if arm == 'candidate_gru' else ('ungated' if arm == 'brg_ungated' else 'brg')
        source = HOST / phase / arm / 'best.pt'
        summary = json.loads((HOST / phase / arm / 'summary.json').read_text())
        if (summary['status'] != 'V1_GPU_TRAINING_PHASE_COMPLETE_NOT_SCIENTIFIC_PASS' or
                summary['variant'] != variant or summary['phase'] != phase or
                summary['epochs'] != (10 if phase == 'warm' else 20)):
            raise RuntimeError('training phase summary mismatch')
        target = HOST / f'{phase}_{arm}_best.pt'
        if target.exists():
            if sha(target) != sha(source):
                raise RuntimeError('existing selected checkpoint drift')
        else:
            shutil.copy2(source, target)
        arms[arm] = {'path': f'{VM_DIR}/{target.name}', 'sha256': sha(target),
                     'bytes': target.stat().st_size, 'variant': variant,
                     'best_dev_source_update_nll': summary['best_dev_source_update_nll'],
                     'summary_sha256': sha(HOST / phase / arm / 'summary.json')}
    status = ('BRG_V1_WARM_MODELS_FROZEN' if phase == 'warm' else
              'BRG_V1_FINAL_MODELS_FROZEN_BEFORE_EVAL')
    result = {'status': status, 'phase': phase,
              'model_source_sha256': sha(ROOT / 'v0_reference' / 'model.py'),
              'checkpoint_selection': 'development source-update prefix NLL',
              'house03_or_eval_used_for_selection': False,
              'arms': arms}
    target = HOST / ('WARM_CHECKPOINT_FREEZE.json' if phase == 'warm' else
                     'FINAL_CHECKPOINT_FREEZE.json')
    payload = json.dumps(result, indent=2) + '\n'
    if target.exists():
        if target.read_text() != payload:
            raise RuntimeError('existing model freeze changed')
    else:
        target.write_text(payload)
    command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
             f'mkdir -p {VM_DIR}'])
    for arm in ARMS:
        path = HOST / f'{phase}_{arm}_best.pt'
        command(['scp', '-q', '-i', str(KEY), str(path), f'{VM}:{VM_DIR}/{path.name}'])
        remote = command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                          f'sha256sum {VM_DIR}/{path.name}']).split()[0]
        if remote != arms[arm]['sha256']:
            raise RuntimeError('VM checkpoint SHA mismatch')
    command(['scp', '-q', '-i', str(KEY), str(target), f'{VM}:{VM_DIR}/{target.name}'])
    remote_freeze = command(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                             f'sha256sum {VM_DIR}/{target.name}']).split()[0]
    if remote_freeze != sha(target):
        raise RuntimeError('VM model freeze SHA mismatch')
    print(json.dumps({'status': status, 'manifest_sha256': sha(target),
                      'arms': {arm: arms[arm]['sha256'] for arm in ARMS}}))


if __name__ == '__main__':
    main()
