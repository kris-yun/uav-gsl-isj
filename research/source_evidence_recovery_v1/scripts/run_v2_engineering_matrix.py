#!/usr/bin/env python3
"""Frozen, single-seed engineering matrix. This is not a scientific benchmark.

Uses the same training data, seed, number of updates, density model and
development source for all rows. Writes the protocol before any fit/evaluation.
The native House/GADEN/ROS experiment is deliberately a separate contract.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    p.add_argument('--targets', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--epochs', type=int, default=8)
    a = p.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Refuse to overwrite a previous matrix; use a fresh path.')
    out.mkdir(parents=True, exist_ok=True)
    variants = [
        ('nll', 'nll', True),
        ('distribution', 'distribution', True),
        ('privileged_pair', 'privileged_pair', True),
        ('mean_log', 'mean_log', True),
        ('projected_endpoint', 'projected_evidence', False),
        ('projected_evidence', 'projected_evidence', True),
        ('projected_no_anchor', 'projected_no_anchor', True),
    ]
    frozen = {
        'scope': 'MANUFACTURED_BACKEND_ENGINEERING_ONLY',
        'manifest_sha256': sha(a.manifest),
        'target_sha256': sha(Path(a.targets) / 'targets.json'),
        'variants': variants, 'epochs': a.epochs, 'seed': 23,
        'batch_size': 8, 'learning_rate': .002,
        'model_capacity': 'manifest config; identical in all rows',
        'data_order': 'identical, teacher target sampling uses a separate RNG',
        'evaluation': 'all development rows and all legal source candidates',
        'selection_rule': 'no winner selection or post-result tuning',
        'scientific_claim': False,
    }
    (out / 'PROTOCOL_FREEZE.json').write_text(json.dumps(frozen, indent=2))
    rows = []
    for name, variant, directional in variants:
        run = out / name
        cmd = [sys.executable, '-m', 'gsl_recovery.v2_cli', 'train-student',
               '--manifest', a.manifest, '--out', str(run), '--variant', variant,
               '--epochs', str(a.epochs), '--seed', '23', '--batch-size', '8',
               '--learning-rate', '0.002', '--device', 'cpu']
        if variant != 'nll':
            cmd += ['--targets', a.targets]
        if not directional:
            cmd += ['--no-directional']
        run.mkdir(parents=True, exist_ok=True)
        receipts = []
        for phase, command in [
            ('train', cmd),
            ('evaluate', [sys.executable, '-m', 'gsl_recovery.v2_cli', 'evaluate',
                          '--manifest', a.manifest, '--model', str(run / 'model'),
                          '--out', str(run / 'development')])]:
            t = time.perf_counter()
            r = subprocess.run(command, capture_output=True, text=True)
            (run / (phase + '.stdout.json')).write_text(r.stdout)
            (run / (phase + '.stderr.txt')).write_text(r.stderr)
            receipts.append({'phase': phase, 'argv': command, 'exit_code': r.returncode,
                             'wall_seconds': time.perf_counter() - t})
            if r.returncode:
                (run / 'command_receipts.json').write_text(json.dumps(receipts, indent=2))
                raise SystemExit(f'{name} {phase} failed; inspect preserved logs.')
            if phase == 'train':
                training = json.loads((run / 'training_receipt.json').read_text())
                if training.get('status') != 'COMPLETE':
                    (run / 'command_receipts.json').write_text(json.dumps(receipts, indent=2))
                    raise SystemExit(f'{name}: training incomplete; preserve and resume before evaluation.')
        (run / 'command_receipts.json').write_text(json.dumps(receipts, indent=2))
        fit = json.loads((run / 'training_receipt.json').read_text())
        ev = json.loads((run / 'development/evaluation.json').read_text())
        rows.append({'name': name, 'fit': fit,
                     'development': {k: v for k, v in ev.items() if k != 'rows'}})
        (out / 'matrix.json').write_text(json.dumps({'protocol': frozen, 'rows': rows}, indent=2))
        print(json.dumps({'name': name, 'fit_status': fit['status'],
                          'evidence_risk': fit['last_epoch_train_evidence_risk'],
                          'development_metrics': ev['source_balanced_metrics']}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
