"""One real VGR episode forward/backward timing; no model training output."""
import argparse
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'v0_reference'))
from model import CandidateBRG, ModelConfig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--episode', required=True)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable')
    with np.load(args.episode) as episode:
        obs = torch.from_numpy(episode['obs'].astype(np.float32)).unsqueeze(0).cuda()
        cues = torch.from_numpy(episode['cues'].astype(np.float32)).unsqueeze(0).cuda()
        label = int(episode['label_index'])
    torch.manual_seed(2026092701)
    model = CandidateBRG(ModelConfig(obs_dim=6, cue_dim=6)).cuda()
    times = []
    for _ in range(3):
        model.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        start = time.perf_counter()
        logits = model(obs, cues)[0]
        loss = -torch.log_softmax(logits, dim=-1)[:, label].mean()
        loss.backward()
        torch.cuda.synchronize()
        times.append(time.perf_counter() - start)
    print({'status': 'REAL_EPISODE_GPU_THROUGHPUT_ONLY',
           'events': obs.shape[1], 'candidates': cues.shape[2],
           'seconds_per_forward_backward': times,
           'gpu': torch.cuda.get_device_name(0),
           'peak_allocated_bytes': torch.cuda.max_memory_allocated()})


if __name__ == '__main__':
    main()
