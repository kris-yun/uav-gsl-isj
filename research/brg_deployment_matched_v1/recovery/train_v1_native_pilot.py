"""Fresh-start, source-balanced V1 training; native_pilot is a separate pre-training amendment.

Warm phase: ten epochs on Native+coverage routes. Final phase: continue the
same optimizer/model for twenty epochs after exactly one shared self-rollout
collection. Development source-update NLL selects checkpoints. Eval sources
are never loaded here.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'v0_reference'))
from model import CandidateBRG, ModelConfig, save_checkpoint


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class Episode:
    obs: np.ndarray
    cues: np.ndarray
    label: int
    update_mask: np.ndarray
    source: str
    plume: str
    policy: str
    split: str
    episode_hash: str


def load_manifest(path: Path, phase: str) -> tuple[list[Episode], list[Episode]]:
    rows = json.loads(path.read_text())['episodes']
    train, dev = [], []
    source_split = {}
    plume_split = {}
    train_policies = set()
    for row in rows:
        if row['split'] not in ('train', 'dev'):
            raise RuntimeError('evaluation source listed in trainer manifest')
        meta = json.loads(Path(row['metadata_path']).read_text())
        data_path = Path(row['episode_path'])
        if sha(data_path) != row['episode_sha256'] or meta['features_sha256'] != row['episode_sha256']:
            raise RuntimeError('episode checksum drift')
        if (meta['case_id'] != row['case_id'] or meta['source_group'] != row['source_group'] or
                meta['plume_group'] != row['plume_group'] or
                meta['split'] != row['split'] or meta['future_gas_used'] or
                meta['labels_used_for_policy'] or not meta['same_sensor_pipeline']):
            raise RuntimeError('deployment metadata/leakage check failed')
        if meta['house'] not in ('House01', 'House02'):
            raise RuntimeError('non-OPEN House in trainer')
        for mapping, key in ((source_split, row['source_group']),
                             (plume_split, row['plume_group'])):
            if key in mapping and mapping[key] != row['split']:
                raise RuntimeError('source/plume leakage')
            mapping[key] = row['split']
        with np.load(data_path) as z:
            obs = z['obs'].astype(np.float32)
            cues = z['cues'].astype(np.float32)
            mask = z['source_update_mask'].astype(bool)
            label = int(z['label_index'])
        if (obs.ndim != 2 or obs.shape[1] != 6 or cues.shape != (len(obs), meta['candidate_count'], 6)
                or not 0 <= label < cues.shape[1] or mask.shape != (len(obs),) or
                not mask.any() or not np.isfinite(obs).all() or not np.isfinite(cues).all()):
            raise RuntimeError('bad episode array or missing source-update prefix')
        policy = row['policy']
        item = Episode(obs, cues, label, mask, row['source_group'],
                       row['plume_group'], policy, row['split'], row['episode_sha256'])
        (train if row['split'] == 'train' else dev).append(item)
        if row['split'] == 'train':
            train_policies.add(policy)
    if len({x.source for x in train}) != 6 or len({x.source for x in dev}) != 2:
        raise RuntimeError('frozen six/two physical source split incomplete')
    if len({x.plume for x in train}) != 40 or len({x.plume for x in dev}) != 8:
        raise RuntimeError('frozen 40/8 plume coverage incomplete')
    if phase == 'native_pilot':
        required = {'native_pmfs'}
    elif phase == 'warm':
        required = {'native_pmfs', 'coverage'}
    elif phase == 'final':
        required = {'native_pmfs', 'coverage', 'candidate_gru', 'brg', 'brg_ungated'}
    else:
        raise RuntimeError('unknown explicitly authorized training phase')
    if train_policies != required:
        raise RuntimeError(f'training policy set incomplete or changed: {train_policies}')
    for plume in {x.plume for x in train}:
        if {x.policy for x in train if x.plume == plume} != required:
            raise RuntimeError(f'training routes incomplete for plume {plume}')
    for plume in {x.plume for x in dev}:
        expected_dev = {'native_pmfs'} if phase == 'native_pilot' else {'native_pmfs', 'coverage'}
        if {x.policy for x in dev if x.plume == plume} != expected_dev:
            raise RuntimeError(f'development routes incomplete for plume {plume}')
    return train, dev


def episode_loss(model: CandidateBRG, episode: Episode, device: str,
                 update_only: bool) -> torch.Tensor:
    o = torch.from_numpy(episode.obs).to(device).unsqueeze(0)
    c = torch.from_numpy(episode.cues).to(device).unsqueeze(0)
    logits = model(o, c)[0]
    loss = -torch.log_softmax(logits, -1)[:, episode.label]
    if update_only:
        loss = loss[torch.from_numpy(episode.update_mask).to(device)]
    return loss.mean()


def dev_nll(model: CandidateBRG, episodes: list[Episode], device: str) -> float:
    grouped = defaultdict(lambda: defaultdict(list))
    model.eval()
    with torch.inference_mode():
        for e in episodes:
            grouped[e.source][e.plume].append(float(episode_loss(model, e, device, True)))
    return float(np.mean([np.mean([np.mean(routes) for routes in plumes.values()])
                          for plumes in grouped.values()]))


def schedule(episodes: list[Episode], epoch: int, seed: int) -> list[list[Episode]]:
    grouped = defaultdict(lambda: defaultdict(list))
    for e in episodes:
        grouped[e.source][e.plume].append(e)
    rng = random.Random(seed + 1009 * epoch)
    sources = sorted(grouped)
    plumes = {source: sorted(grouped[source]) for source in sources}
    for values in plumes.values():
        rng.shuffle(values)
    steps = max(len(v) for v in plumes.values())
    batches = []
    for step in range(steps):
        batch = []
        for source in sources:
            plume = plumes[source][step % len(plumes[source])]
            routes = sorted(grouped[source][plume], key=lambda e: e.policy)
            batch.append(routes[(epoch + step) % len(routes)])
        batches.append(batch)
    return batches


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--phase', choices=('warm', 'final', 'native_pilot'), required=True)
    ap.add_argument('--variant', choices=('gru', 'brg', 'ungated'), required=True)
    ap.add_argument('--resume-trainer')
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError('the signed local GPU training path requires CUDA')
    if args.phase == 'final' and not args.resume_trainer:
        raise RuntimeError('final phase must continue the frozen warm optimizer')
    if args.phase in ('warm', 'native_pilot') and args.resume_trainer:
        raise RuntimeError('warm phase must initialize fresh weights')
    seed = 2026092701
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(2)
    train, dev = load_manifest(Path(args.manifest), args.phase)
    cfg = ModelConfig(hidden=35 if args.variant == 'gru' else 32,
                      rounds=1 if args.variant == 'gru' else 3,
                      variant=args.variant, obs_dim=6, cue_dim=6)
    model = CandidateBRG(cfg).to('cuda')
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    if args.resume_trainer:
        saved = torch.load(args.resume_trainer, map_location='cuda', weights_only=True)
        if (saved['variant'] != args.variant or saved['completed_epochs'] != 10 or
                saved.get('metadata', {}).get('phase') != 'warm'):
            raise RuntimeError('warm trainer state mismatch')
        model.load_state_dict(saved['model'])
        optimizer.load_state_dict(saved['optimizer'])
    out = Path(args.out)
    if out.exists():
        raise RuntimeError('refuse to overwrite existing training output')
    out.mkdir(parents=True)
    epochs = 10 if args.phase in ('warm', 'native_pilot') else 20
    metadata = {'deployment_status': ('NATIVE_ONLY_INITIAL_PILOT_NOT_FULL_V1' if args.phase == 'native_pilot' else 'OPEN_DEVELOPMENT_NOT_SCIENTIFIC_PASS'),
                'observation_contract_id': 'VGR_FOPDT_300S_PHYSICAL_FRAME_V1',
                'feature_config': {}, 'temperature': 1.0,
                'variant': args.variant, 'phase': args.phase, 'seed': seed,
                'training_source_count': 6, 'development_source_count': 2,
                'train_plume_count': 40, 'dev_plume_count': 8,
                'max_tested_history': max(len(x.obs) for x in train),
                'model_source_sha256': sha(HERE / 'v0_reference' / 'model.py'),
                'manifest_sha256': sha(Path(args.manifest)),
                'parameter_count': model.parameter_count,
                'active_parameter_count': model.active_parameter_count,
                'checkpoint_selection': 'independent_dev_source_update_prefix_nll'}
    best = float('inf')
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for batch in schedule(train, epoch, seed):
            optimizer.zero_grad(set_to_none=True)
            for episode in batch:
                loss = episode_loss(model, episode, 'cuda', False)
                if not torch.isfinite(loss):
                    raise RuntimeError('nonfinite training loss')
                (loss / len(batch)).backward()
                train_losses.append(float(loss.detach()))
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
        metric = dev_nll(model, dev, 'cuda')
        row = {'epoch': epoch, 'train_prefix_nll': float(np.mean(train_losses)),
               'dev_source_update_nll': metric}
        history.append(row)
        print(json.dumps(row), flush=True)
        if metric < best:
            best = metric
            save_checkpoint(out / 'best.pt', model,
                            {**metadata, 'epoch': epoch, 'dev_source_update_nll': metric})
        (out / 'history.json').write_text(json.dumps(history, indent=2) + '\n')
    save_checkpoint(out / 'last.pt', model,
                    {**metadata, 'epoch': epochs, 'dev_source_update_nll': metric})
    torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                'variant': args.variant, 'completed_epochs': 10 if args.phase in ('warm', 'native_pilot') else 30,
                'metadata': metadata}, out / 'trainer_state.pt')
    summary = {'status': 'V1_GPU_TRAINING_PHASE_COMPLETE_NOT_SCIENTIFIC_PASS',
               'variant': args.variant, 'phase': args.phase, 'epochs': epochs,
               'best_dev_source_update_nll': best, 'train_episodes': len(train),
               'dev_episodes': len(dev), 'cuda': torch.cuda.get_device_name(0),
               'torch': torch.__version__, 'model_sha256': metadata['model_source_sha256']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
