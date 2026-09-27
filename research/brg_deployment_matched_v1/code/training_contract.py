"""Small, explicit utilities for a PROPOSED deployment-matched BRG/GRU revision.

Not a ROS connector, trained model, simulator or causal mechanism guarantee.
Existing concentration/candidate features and the recurrent core are unchanged.
New timing features are shared between the training encoder and runtime encoder.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Sequence
import hashlib
import math
import numpy as np
import torch

@dataclass(frozen=True)
class Window:
    event_id: int
    start_s: float
    end_s: float
    x_m: float
    y_m: float
    raw_samples: int

class TimingEncoder:
    """Three lawful timing/motion features; no source truth or gas values.

    Window timestamps must come from actual acquisition messages in simulation
    time, NOT inferred from receipt time or frame number. Same-location repeated
    measurements are valid and are NOT removed as duplicates.
    """
    def __init__(self, run_start_s: float, initial_xy: tuple[float, float],
                 horizon_s: float = 300.0):
        if not all(math.isfinite(v) for v in (run_start_s, *initial_xy, horizon_s)) or horizon_s <= 0:
            raise ValueError('invalid run context')
        self.start = float(run_start_s)
        self.end = float(run_start_s)
        self.xy = tuple(map(float, initial_xy))
        self.horizon = float(horizon_s)
        self.last_id = -1

    def push(self, w: Window) -> np.ndarray:
        values = (w.start_s, w.end_s, w.x_m, w.y_m)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('non-finite window metadata')
        if not isinstance(w.event_id, int) or w.event_id <= self.last_id:
            raise ValueError('duplicate or reordered event: runtime must deduplicate BEFORE push')
        if not isinstance(w.raw_samples, int) or w.raw_samples <= 0:
            raise ValueError('raw sample count must be positive')
        if w.start_s < self.start or w.end_s <= w.start_s:
            raise ValueError('invalid physical acquisition window')
        if w.start_s < self.end - 1e-8 or w.end_s <= self.end:
            raise ValueError('overlapping or non-increasing acquisition window')
        if w.end_s > self.start + self.horizon + 1e-8:
            raise ValueError('out of signed time budget; do not clip')
        dt = w.end_s - self.end
        duration = w.end_s - w.start_s
        distance = math.hypot(w.x_m - self.xy[0], w.y_m - self.xy[1])
        # Units: 1 s, 1 s, 0.30 m. No target-fitted standardization.
        out = (np.log1p(np.array([dt, duration, distance / .30])) / 8.).astype(np.float32)
        self.end = w.end_s
        self.xy = (w.x_m, w.y_m)
        self.last_id = w.event_id
        return out

def encode_timing(windows: Sequence[Window], run_start_s: float,
                  initial_xy: tuple[float, float], horizon_s: float = 300.) -> np.ndarray:
    if not windows:
        raise ValueError('empty trajectory is not a trainable source observation')
    encoder = TimingEncoder(run_start_s, initial_xy, horizon_s)
    return np.stack([encoder.push(w) for w in windows])

def append_timing(old_observations: np.ndarray, timing: np.ndarray) -> np.ndarray:
    """Original 3 channels plus 3 timing/motion channels -> obs_dim=6."""
    old = np.asarray(old_observations, dtype=np.float32)
    time = np.asarray(timing, dtype=np.float32)
    if old.ndim != 2 or old.shape[1] != 3 or time.shape != old.shape:
        raise ValueError('expected two [T,3] arrays')
    if not (np.isfinite(old).all() and np.isfinite(time).all()):
        raise ValueError('non-finite features')
    return np.concatenate((old, time), axis=1)

def prefix_nll(logits: torch.Tensor, truth_index: int,
               mask: torch.Tensor | None = None) -> torch.Tensor:
    """One trajectory contribution. No multiplying old posterior into new output.

    Existing trainer ALREADY uses prefix CE for its ten observations. Here the
    same objective operates on actual variable-length episodes. `mask` supports
    decision-prefix evaluation; it is not a mechanism to omit hard outcomes.
    """
    if logits.ndim != 2 or logits.shape[0] < 1 or logits.shape[1] < 2:
        raise ValueError('expected [events,candidates]')
    if not 0 <= truth_index < logits.shape[1]:
        raise ValueError('truth outside candidate support: no nearest-label substitution')
    if not torch.isfinite(logits).all():
        raise ValueError('non-finite logits')
    loss = -torch.log_softmax(logits, dim=-1)[:, truth_index]
    if mask is None:
        return loss.mean()
    mask = torch.as_tensor(mask, device=logits.device, dtype=torch.bool)
    if mask.shape != (logits.shape[0],) or not mask.any():
        raise ValueError('invalid or empty evaluation mask')
    return loss[mask].mean()

def source_plume_balanced_reduce(losses: Sequence[torch.Tensor],
                                 source_groups: Sequence[str],
                                 plume_groups: Sequence[str]) -> torch.Tensor:
    """Average collection-policy routes within plume, then plume within source.

    More crops, routes, or events from one plume are not extra source weight.
    The function is an objective weighting rule, not a confidence interval.
    """
    if not losses or not (len(losses) == len(source_groups) == len(plume_groups)):
        raise ValueError('nonempty aligned inputs required')
    groups = defaultdict(lambda: defaultdict(list))
    mapping = {}
    for loss, source, plume in zip(losses, source_groups, plume_groups):
        if loss.ndim != 0 or not torch.isfinite(loss):
            raise ValueError('finite scalar loss required')
        if plume in mapping and mapping[plume] != source:
            raise ValueError('same plume assigned to different source groups')
        mapping[plume] = source
        groups[source][plume].append(loss)
    return torch.stack([
        torch.stack([torch.stack(v).mean() for v in plumes.values()]).mean()
        for plumes in groups.values()
    ]).mean()

def deterministic_source_split(keys: Sequence[str], salt: str,
                               n_dev: int, n_eval: int) -> dict[str, str]:
    """Metadata-only split. A key must group physical sources across all winds.

    Group neighboring source pairs together before calling this function.
    Counts are to be signed after the existing-asset inventory, before training.
    No adjustment after inspecting outcomes; never hash seeds independently.
    """
    if len(set(keys)) != len(keys) or min(n_dev, n_eval) < 1 or n_dev + n_eval >= len(keys):
        raise ValueError('invalid group/count contract')
    order = sorted(keys, key=lambda k: (hashlib.sha256((salt+'|'+k).encode()).hexdigest(), k))
    out = {}
    for i, k in enumerate(order):
        out[k] = 'eval' if i < n_eval else ('dev' if i < n_eval+n_dev else 'train')
    return out

def validate_rows(rows: Sequence[dict]) -> None:
    """Leakage checks. Runtime messages must separately prohibit these labels."""
    src_parts, plume_parts = {}, {}
    for r in rows:
        house = str(r['house']).lower().replace('_', '')
        if house not in {'house01', 'house02'}:
            raise ValueError('this development revision permits only OPEN H01/H02')
        part = r['split']
        if part not in {'train', 'dev', 'eval'}:
            raise ValueError('unknown partition')
        for mapping, key in ((src_parts, r['source_group']), (plume_parts, r['plume_group'])):
            if key in mapping and mapping[key] != part:
                raise ValueError('source/plume leakage across partitions')
            mapping[key] = part
        if r.get('labels_used_for_policy', False):
            raise ValueError('source labels may supervise training, not choose collection actions')
        if r.get('future_gas_used', False):
            raise ValueError('future concentration used in context')
        if not r.get('same_sensor_pipeline', False):
            raise ValueError('raw snapshots are not deployment-matched episodes')
        if part != 'train' and r.get('included_in_gradient_update', False):
            raise ValueError('held-out row included in gradient update')
