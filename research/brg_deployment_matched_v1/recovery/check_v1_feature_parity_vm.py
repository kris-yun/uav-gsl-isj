"""Replay an archived Native event history through the V1 online encoder."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0, str(ROOT))
from pmfs_brg.bank import TemplateBank
from serve_v1_vm import V1Session


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


class CaptureModel:
    def __init__(self):
        self.cfg = type('Config', (), {'obs_dim': 6, 'cue_dim': 6})()
        self.obs, self.cues = [], []

    def eval(self):
        return self

    def initial(self, batch, candidates):
        return torch.zeros(batch, candidates, 1)

    def step(self, observed, cues, state):
        self.obs.append(observed.numpy().copy()[0])
        self.cues.append(cues.numpy().copy()[0])
        return torch.zeros(1, cues.shape[1]), state


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--case-file', required=True)
    ap.add_argument('--archive-root', required=True)
    ap.add_argument('--episode', required=True)
    args = ap.parse_args()
    case = json.loads(Path(args.case_file).read_text())
    root = Path(args.archive_root)
    raw = next(root.glob('*_raw'))
    events = rows(raw / 'measurement_events.csv')
    blocks = rows(raw / 'measurement_blocks.csv')
    bank = TemplateBank.load(ROOT / f'legal_support_v2/env_{case["environment_index"]}_bank.npz')
    model = CaptureModel()
    meta = {'observation_contract_id': 'VGR_FOPDT_300S_PHYSICAL_FRAME_V1',
            'feature_config': {}, 'max_tested_history': 128, 'temperature': 1.0}
    session = V1Session(model, meta, bank, raw / 'measurement_blocks.csv',
                        raw / 'measurement_samples.csv', raw / 'sensor_trace.csv',
                        tuple(case['start_xy']))
    session.reset('parity_check', bank.fingerprint)
    for n, (event, block) in enumerate(zip(events, blocks)):
        r = session.observe({'run_id': 'parity_check', 'event_id': n,
                             'time_s': float(block['sim_time_end']) + .1,
                             'x': float(event['robot_x']), 'y': float(event['robot_y']),
                             'z': .2, 'concentration_ppm': float(event['concentration'])})
        if len(r['q']) != len(bank.ids):
            raise RuntimeError('candidate axis length mismatch')
    episode = np.load(args.episode)
    obs = np.stack(model.obs)
    cues = np.stack(model.cues)
    if obs.shape != episode['obs'].shape or cues.shape != episode['cues'].shape:
        raise RuntimeError('offline and online shape mismatch')
    obs_abs = float(np.max(np.abs(obs - episode['obs'])))
    cue_abs = float(np.max(np.abs(cues - episode['cues'])))
    if obs_abs > 1e-7 or cue_abs > 1e-7:
        raise RuntimeError(f'online/offline feature mismatch: obs={obs_abs}, cues={cue_abs}')
    print(json.dumps({'status': 'V1_ONLINE_OFFLINE_FEATURE_PARITY_PASS',
                      'events': len(events), 'candidates': len(bank.ids),
                      'max_abs_obs': obs_abs, 'max_abs_cues': cue_abs}))


if __name__ == '__main__':
    main()
