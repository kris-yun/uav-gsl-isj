#!/usr/bin/env python3
"""Candidate-conditioned residual Set-NRE for frozen PF-DEI H01 banks.

The network is permutation invariant over nuisance members inside a sensing
block and over the set of visible blocks.  It contains no temporal convolution,
attention, recurrent layer, Transformer, or trajectory forecaster.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn


REFERENCE_PPM = 0.1
BLOCK_SAMPLES = 10
BLOCKS_PER_STOP = 8
SOURCE_UPDATE_STOP_STRIDE = 3


@dataclass(frozen=True)
class BlockLayout:
    sample_indices: np.ndarray       # [blocks,10]
    stop_index: np.ndarray           # [blocks]
    block_within_stop: np.ndarray    # [blocks]
    stop_x: np.ndarray               # [blocks]
    stop_y: np.ndarray               # [blocks]
    available_updates: tuple[int, ...]

    def visible_blocks(self, update: int) -> int:
        if update not in self.available_updates:
            raise ValueError(f"source update {update} unavailable")
        return BLOCKS_PER_STOP * (1 + SOURCE_UPDATE_STOP_STRIDE * update)


def build_block_layout(x: np.ndarray, y: np.ndarray, stop_start: np.ndarray,
                       length: int) -> BlockLayout:
    """Recover the same eight ten-sample blocks consumed at each physical stop."""
    x = np.asarray(x[:length], dtype=np.float64)
    y = np.asarray(y[:length], dtype=np.float64)
    starts = np.flatnonzero(np.asarray(stop_start[:length]) > 0.5)
    if len(starts) < 4 or starts[0] != 0:
        raise ValueError("invalid physical-stop schedule")
    groups = []
    stop_ids = []
    within = []
    xs = []
    ys = []
    complete_stops = 0
    for stop_id, start in enumerate(starts):
        sx, sy = x[start], y[start]
        end = int(start)
        while end < length and abs(x[end] - sx) <= 1e-6 and abs(y[end] - sy) <= 1e-6:
            end += 1
        stationary = np.arange(start, end, dtype=np.int64)
        if stationary.size < BLOCKS_PER_STOP * BLOCK_SAMPLES:
            if stop_id != len(starts) - 1:
                raise ValueError(f"non-trailing stop {stop_id + 1} has only {stationary.size} stationary samples")
            # A 300 s run may terminate after entering its final physical stop
            # but before completing eight blocks.  It never contributes to a
            # completed source update and is therefore excluded fail-closed.
            break
        # Initial readiness precedes the first StopAndMeasure cycle.  Later
        # cycles consume immediately after arrival.  This is the frozen forward
        # closure rule and matches the archived block manifest exactly.
        used = stationary[-80:] if stop_id == 0 else stationary[:80]
        for b in range(BLOCKS_PER_STOP):
            groups.append(used[b * 10:(b + 1) * 10])
            stop_ids.append(stop_id)
            within.append(b)
            xs.append(sx); ys.append(sy)
        complete_stops += 1
    available = tuple(range(1, (complete_stops - 1) // SOURCE_UPDATE_STOP_STRIDE + 1))
    if not available:
        raise ValueError("trajectory has no complete source-update prefix")
    return BlockLayout(
        sample_indices=np.stack(groups),
        stop_index=np.asarray(stop_ids, dtype=np.int64),
        block_within_stop=np.asarray(within, dtype=np.int64),
        stop_x=np.asarray(xs, dtype=np.float32),
        stop_y=np.asarray(ys, dtype=np.float32),
        available_updates=available,
    )


def log_measurement(values: np.ndarray) -> np.ndarray:
    v = np.asarray(values, dtype=np.float32)
    if np.any(v < 0) or not np.all(np.isfinite(v)):
        raise ValueError("measured ppm must be finite and nonnegative")
    return np.log1p(v / REFERENCE_PPM).astype(np.float32)


def posterior_features(q: np.ndarray, carrier_xy: np.ndarray, candidate: int) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    xy = np.asarray(carrier_xy, dtype=np.float64)
    if q.shape != (xy.shape[0],) or np.any(q <= 0) or not np.isclose(q.sum(), 1.0, atol=1e-9):
        raise ValueError("PMFS posterior must be strictly positive and normalized")
    entropy = -float(np.sum(q * np.log(q))) / math.log(len(q))
    mean = np.sum(q[:, None] * xy, axis=0)
    centered = xy - mean
    spread = math.sqrt(float(np.sum(q * np.sum(centered * centered, axis=1))))
    logq = math.log(float(q[candidate]))
    return np.asarray([
        logq / 50.0,
        entropy,
        float(np.max(q)),
        float(mean[0]), float(mean[1]),
        spread,
    ], dtype=np.float32)


def candidate_features(carrier: dict, xy_center: np.ndarray, xy_scale: np.ndarray,
                       q: np.ndarray, carrier_xy: np.ndarray, candidate: int) -> np.ndarray:
    cx, cy = float(carrier["centroid_x"]), float(carrier["centroid_y"])
    base = np.asarray([
        (cx - xy_center[0]) / xy_scale[0],
        (cy - xy_center[1]) / xy_scale[1],
        float(carrier["width_m"]) / xy_scale[0],
        float(carrier["height_m"]) / xy_scale[1],
        math.log1p(float(carrier["free_count"])) / math.log(5.0),
        math.log(float(carrier["prior_mass"])) / 10.0,
    ], dtype=np.float32)
    return np.concatenate([base, posterior_features(q, carrier_xy, candidate)])


def block_context(layout: BlockLayout, visible: int, carrier: dict,
                  xy_center: np.ndarray, xy_scale: np.ndarray) -> np.ndarray:
    cx, cy = float(carrier["centroid_x"]), float(carrier["centroid_y"])
    sx = layout.stop_x[:visible]
    sy = layout.stop_y[:visible]
    max_stop = max(int(layout.stop_index[:visible].max()), 1)
    return np.column_stack([
        (sx - xy_center[0]) / xy_scale[0],
        (sy - xy_center[1]) / xy_scale[1],
        (cx - sx) / xy_scale[0],
        (cy - sy) / xy_scale[1],
        2.0 * layout.block_within_stop[:visible] / 7.0 - 1.0,
        layout.stop_index[:visible] / max_stop,
    ]).astype(np.float32)


def masked_moments(x: torch.Tensor, mask: torch.Tensor, dim: int):
    """Permutation-invariant mean/max/std/sqrt-normalized sum."""
    m = mask.to(x.dtype)
    while m.ndim < x.ndim:
        m = m.unsqueeze(-1)
    count = m.sum(dim=dim).clamp_min(1.0)
    total = (x * m).sum(dim=dim)
    mean = total / count
    centered = (x - mean.unsqueeze(dim)) * m
    var = (centered * centered).sum(dim=dim) / count
    neg = torch.finfo(x.dtype).min
    maximum = x.masked_fill(~m.bool(), neg).amax(dim=dim)
    sqrt_sum = total / torch.sqrt(count)
    return mean, maximum, torch.sqrt(var.clamp_min(0.0) + 1e-8), sqrt_sum


class ConditionedDeepSetNRE(nn.Module):
    """Deep Set++ over nuisance members, then Deep Set++ over blocks."""

    def __init__(self, candidate_dim: int = 12, block_context_dim: int = 6,
                 hidden: int = 32):
        super().__init__()
        self.candidate_dim = candidate_dim
        self.block_context_dim = block_context_dim
        # [obs10, pred10, residual10, abs-residual10]
        self.member_encoder = nn.Sequential(
            nn.Linear(40, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
        )
        member_pool_dim = 4 * hidden
        # member moments + obs mean/sd/slope/max + block context + candidate
        self.block_encoder = nn.Sequential(
            nn.Linear(member_pool_dim + 4 + block_context_dim + candidate_dim, 64),
            nn.SiLU(), nn.Linear(64, hidden), nn.SiLU(),
        )
        block_pool_dim = 4 * hidden
        self.head = nn.Sequential(
            nn.Linear(block_pool_dim + 1 + candidate_dim, 64),
            nn.SiLU(), nn.Linear(64, 32), nn.SiLU(), nn.Linear(32, 1),
        )

    def forward(self, observation: torch.Tensor, prediction_set: torch.Tensor,
                block_context_tensor: torch.Tensor, candidate: torch.Tensor,
                block_mask: torch.Tensor, member_mask: torch.Tensor) -> torch.Tensor:
        # obs [N,B,10], pred [N,B,M,10]
        obs = observation.unsqueeze(2).expand_as(prediction_set)
        member_input = torch.cat([
            obs, prediction_set, obs - prediction_set, torch.abs(obs - prediction_set)
        ], dim=-1)
        encoded = self.member_encoder(member_input)
        mm = member_mask[:, None, :].expand(-1, prediction_set.shape[1], -1)
        member_parts = masked_moments(encoded, mm, dim=2)
        member_pool = torch.cat(member_parts, dim=-1)
        obs_mean = observation.mean(dim=-1, keepdim=True)
        obs_std = observation.std(dim=-1, correction=0, keepdim=True)
        obs_slope = (observation[..., -1:] - observation[..., :1]) / 9.0
        obs_max = observation.amax(dim=-1, keepdim=True)
        cand = candidate[:, None, :].expand(-1, observation.shape[1], -1)
        block_input = torch.cat([
            member_pool, obs_mean, obs_std, obs_slope, obs_max,
            block_context_tensor, cand,
        ], dim=-1)
        block_encoded = self.block_encoder(block_input)
        block_parts = masked_moments(block_encoded, block_mask, dim=1)
        block_pool = torch.cat(block_parts, dim=-1)
        count = block_mask.sum(dim=1, keepdim=True).to(observation.dtype)
        final = torch.cat([block_pool, torch.log1p(count), candidate], dim=-1)
        return self.head(final).squeeze(-1)


def residual_corrected_posterior(q: np.ndarray, log_ratio: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    r = np.asarray(log_ratio, dtype=np.float64)
    if q.shape != r.shape or np.any(q <= 0) or not np.all(np.isfinite(r)):
        raise ValueError("invalid residual posterior inputs")
    z = np.log(q) + r
    z -= np.max(z)
    p = np.exp(z)
    p /= np.sum(p)
    return p


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
