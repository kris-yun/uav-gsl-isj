"""DRPE V1 dependency-light core.

This file contains only the frozen representation primitives used by the
offline screen. It does not perform ROS integration or train on test truth.
"""
from __future__ import annotations
import math
import numpy as np

DT = 0.2
GAS_THRESHOLD_PPM = 0.1
PERIODS_S = (1.0, 5.0, 20.0)
DECAY_CYCLES = 2.0
RIDGE_ALPHA = 1.0
POSTERIOR_BETA = 2.0
SCORE_CLIP = 3.0


def whiff_onsets(concentration_ppm, threshold=GAS_THRESHOLD_PPM):
    c = np.asarray(concentration_ppm, dtype=float)
    hit = c > threshold
    out = np.zeros(len(c), dtype=float)
    if len(c):
        out[0] = float(hit[0])
    if len(c) > 1:
        out[1:] = np.logical_and(hit[1:], np.logical_not(hit[:-1]))
    return out


def resonant_envelope(events, period_s, dt=DT, decay_cycles=DECAY_CYCLES):
    """Complex leaky resonator; return source-blind normalized envelope."""
    x = np.asarray(events, dtype=float)
    r = math.exp(-dt / (decay_cycles * period_s))
    rot = complex(math.cos(2 * math.pi * dt / period_s),
                  math.sin(2 * math.pi * dt / period_s))
    z = 0j
    norm = 0.0
    out = np.zeros(len(x), dtype=float)
    for i, v in enumerate(x):
        z = r * rot * z + float(v)
        norm = r * norm + 1.0
        out[i] = abs(z) / max(norm, 1e-12)
    return out


def resonant_bank(concentration_ppm):
    u = whiff_onsets(concentration_ppm)
    return np.stack([resonant_envelope(u, p) for p in PERIODS_S], axis=1)


def _weighted_stats(m, q, plausible, cross, along, distance, wind_speed):
    m = np.clip(np.asarray(m, dtype=float), 0.0, 1.0)
    den = float(m.sum()) + 1e-12
    b = 1.0 - m
    denb = float(b.sum()) + 1e-12
    plume = plausible * np.exp(-cross)

    hit = np.array([
        np.sum(m * q) / den,
        np.sum(m * q / (distance + 0.5)) / den,
        np.sum(m * plume) / den,
        np.sum(m * plume / (1.0 + np.maximum(along, 0.0))) / den,
        np.sum(m * cross) / den,
        np.sum(m * distance) / den,
        np.sum(m * wind_speed * q) / den,
        np.sum(m * plausible) / den,
    ])
    blank = np.array([
        np.sum(b * q) / denb,
        np.sum(b * plume) / denb,
        np.sum(b * cross) / denb,
        np.sum(b * distance) / denb,
    ])
    return np.concatenate([
        hit,
        np.array([
            hit[0] - blank[0],
            hit[2] - blank[1],
            hit[4] - blank[2],
            hit[5] - blank[3],
            float(m.mean()),
        ]),
    ])


def candidate_feature(trace_xy, wind_uv, branch_states, candidate_xy):
    """45-D frozen DRPE feature for one source candidate."""
    rxy = np.asarray(trace_xy, dtype=float)
    w = np.asarray(wind_uv, dtype=float)
    c = np.asarray(candidate_xy, dtype=float)

    delta = rxy - c[None, :]
    distance = np.linalg.norm(delta, axis=1)
    wind_speed = np.linalg.norm(w, axis=1)
    wind_unit = w / np.maximum(wind_speed[:, None], 1e-6)
    delta_unit = delta / np.maximum(distance[:, None], 1e-6)

    align = np.sum(delta_unit * wind_unit, axis=1)
    q = np.maximum(align, 0.0)
    along = np.sum(delta * wind_unit, axis=1)
    cross = np.abs(delta[:, 0] * wind_unit[:, 1]
                   - delta[:, 1] * wind_unit[:, 0])
    plausible = (along > 0.0).astype(float)

    feat = [
        float(distance.mean()),
        float(distance.min()),
        float(q.mean()),
        float(plausible.mean()),
        float(cross.mean()),
        float(np.maximum(along, 0.0).mean()),
    ]
    for k in range(branch_states.shape[1]):
        feat.extend(_weighted_stats(
            branch_states[:, k], q, plausible, cross, along,
            distance, wind_speed
        ).tolist())
    return np.asarray(feat, dtype=float)


def fused_leaf_factor(score, mean_score, std_score,
                      beta=POSTERIOR_BETA, clip=SCORE_CLIP):
    z = (float(score) - float(mean_score)) / max(float(std_score), 1e-12)
    z = max(-clip, min(clip, z))
    return math.exp(beta * z)
