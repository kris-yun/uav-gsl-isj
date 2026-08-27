#!/usr/bin/env python3
"""Reference mathematics for V4 OC-SLA.

Observation-Conditioned Stable Likelihood Assimilation (OC-SLA).
Research-only. No truth, House id, route id, localization error, temperature,
blend weight, or outcome-fitted scientific threshold is an input.

Core invariants:
- physical stop is the inferential unit;
- one current source-update window is consumed exactly once;
- LOSO cross-predictive consensus must beat the pre-update native predictive
  mixture on every held-out physical stop;
- accepted stable evidence updates an independent binary macro-odds ledger;
- the final correction is the KL-nearest native posterior satisfying only the
  earned stable mass floor, so a native state already stronger on the validated
  macro region is returned exactly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable

import numpy as np

K_CAL = 4
K_SCORE = 4


def frequency_floor(timesteps: int) -> float:
    """Continuity floor tied to the PMFS transport-frequency grid."""
    if int(timesteps) <= 0:
        raise ValueError("timesteps must be positive")
    return 0.5 / (float(timesteps) + 1.0)


def _logmeanexp(values: np.ndarray) -> float:
    a = np.asarray(values, dtype=float)
    if a.size == 0 or not np.all(np.isfinite(a)):
        raise ValueError("invalid logmeanexp input")
    m = float(np.max(a))
    return m + math.log(float(np.mean(np.exp(a - m))))


def _weighted_logsumexp(log_values: np.ndarray, weights: np.ndarray) -> float:
    v = np.asarray(log_values, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(v) == 0 or len(v) != len(w) or not np.all(np.isfinite(v)):
        raise ValueError("invalid weighted logsumexp input")
    if np.any(w < 0.0) or not float(np.sum(w)) > 0.0:
        raise ValueError("invalid weighted logsumexp weights")
    keep = w > 0.0
    v = v[keep]
    w = w[keep]
    w = w / float(np.sum(w))
    m = float(np.max(v))
    return m + math.log(float(np.sum(w * np.exp(v - m))))


def _numerical_zero(*values: np.ndarray | float) -> float:
    scale = 1.0
    for value in values:
        a = np.asarray(value, dtype=float)
        if a.size:
            scale += float(np.max(np.abs(a)))
    return 64.0 * np.finfo(float).eps * scale


def _best_tie_set(values: np.ndarray) -> set[int]:
    v = np.asarray(values, dtype=float)
    maximum = float(np.max(v))
    tol = _numerical_zero(v)
    return set(np.flatnonzero(v >= maximum - tol).tolist())


def adjacent(a: np.ndarray, b: np.ndarray) -> bool:
    """Frozen persistent-carrier adjacency, including corner touching."""
    ax0, ay0, aw, ah = map(int, a)
    bx0, by0, bw, bh = map(int, b)
    ax1, ay1 = ax0 + aw, ay0 + ah
    bx1, by1 = bx0 + bw, by0 + bh
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return dx == 0 and dy == 0


class _DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def unite(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a != b:
            self.parent[b] = a


@dataclass
class StopBank:
    probability: np.ndarray          # [S,M,J]
    hit_fraction: np.ndarray         # [J]
    stop_id: np.ndarray              # [J]
    block_count: np.ndarray          # [J]
    max_prediction_drift: float


@dataclass
class StableState:
    q_causal: np.ndarray
    last_validated_mask: np.ndarray | None = None
    consumed_window_ids: set[str] = field(default_factory=set)

    def copy(self) -> "StableState":
        return StableState(
            q_causal=np.asarray(self.q_causal, dtype=float).copy(),
            last_validated_mask=None if self.last_validated_mask is None else np.asarray(self.last_validated_mask, dtype=bool).copy(),
            consumed_window_ids=set(self.consumed_window_ids),
        )


@dataclass
class StepResult:
    accepted: bool
    reason: str
    output_mass: np.ndarray
    state: StableState
    component_id: np.ndarray | None = None
    consensus_component: int | None = None
    consensus_mask: np.ndarray | None = None
    heldout_gain: np.ndarray | None = None
    stop_count: int = 0
    stop_ids: np.ndarray | None = None
    block_counts: np.ndarray | None = None
    effective_eigenvalues: np.ndarray | None = None
    causal_log_odds_increment: float | None = None
    alpha: float | None = None
    beta: float | None = None
    projection_active: bool = False
    loso_best_sets: tuple[tuple[int, ...], ...] | None = None


def initialize_state(geometry_prior: np.ndarray) -> StableState:
    q0 = np.asarray(geometry_prior, dtype=float)
    if q0.ndim != 1 or np.any(q0 < 0.0) or not float(np.sum(q0)) > 0.0:
        raise ValueError("invalid geometry prior")
    q0 = q0 / float(np.sum(q0))
    return StableState(q_causal=q0)


def collapse_blocks_to_stops(
    probability: np.ndarray,
    observed_hit: np.ndarray,
    physical_stop_id: np.ndarray,
    *,
    prediction_drift_tolerance: float = 1e-12,
) -> StopBank:
    """Collapse contiguous completed blocks to explicit physical-stop units.

    Stop identity is supplied by the PMFS movement/iteration state. Position
    equality is deliberately not used to infer stop identity.
    """
    p = np.asarray(probability, dtype=float)
    y = np.asarray(observed_hit, dtype=float)
    sid = np.asarray(physical_stop_id)
    if p.ndim != 3:
        raise ValueError("probability must have shape [S,M,E]")
    S, M, E = p.shape
    if S < 2 or M < K_CAL + K_SCORE or len(y) != E or len(sid) != E or E == 0:
        raise ValueError("block input shape mismatch")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(y)):
        raise ValueError("nonfinite block input")
    if np.any((y < 0.0) | (y > 1.0)):
        raise ValueError("observed_hit must be in [0,1]")

    stop_p: list[np.ndarray] = []
    stop_r: list[float] = []
    stop_ids: list[object] = []
    counts: list[int] = []
    seen: set[object] = set()
    max_drift = 0.0
    start = 0
    for e in range(1, E + 1):
        if e == E or sid[e] != sid[start]:
            current_id = sid[start].item() if hasattr(sid[start], "item") else sid[start]
            if current_id in seen:
                raise ValueError("physical_stop_id is noncontiguous/replayed within one window")
            seen.add(current_id)
            idx = np.arange(start, e)
            ref = p[:, :, idx[0]][:, :, None]
            drift = float(np.max(np.abs(p[:, :, idx] - ref)))
            max_drift = max(max_drift, drift)
            if drift > prediction_drift_tolerance:
                raise ValueError(f"within-stop prediction drift {drift}")
            stop_p.append(np.mean(p[:, :, idx], axis=2))
            stop_r.append(float(np.mean(y[idx])))
            stop_ids.append(current_id)
            counts.append(int(len(idx)))
            start = e

    return StopBank(
        probability=np.stack(stop_p, axis=2),
        hit_fraction=np.asarray(stop_r, dtype=float),
        stop_id=np.asarray(stop_ids),
        block_count=np.asarray(counts, dtype=int),
        max_prediction_drift=max_drift,
    )


def effective_precision(stop_probability: np.ndarray, timesteps: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Transport covariance plus conservative one-stop observation covariance."""
    p = np.asarray(stop_probability, dtype=float)
    if p.ndim != 3:
        raise ValueError("stop_probability must have shape [S,M,J]")
    S, M, J = p.shape
    if M < K_CAL or J <= 0:
        raise ValueError("insufficient stop bank")

    c_tr = np.zeros((J, J), dtype=float)
    count = 0
    for s in range(S):
        for m in range(K_CAL):
            for h in range(m + 1, K_CAL):
                d = p[s, m] - p[s, h]
                c_tr += 0.5 * np.outer(d, d)
                count += 1
    c_tr /= float(max(count, 1))
    c_tr = 0.5 * (c_tr + c_tr.T)

    eps = frequency_floor(timesteps)
    c_y = np.eye(J, dtype=float) * (0.25 + eps * eps)
    c_eff = c_tr + c_y
    values, vectors = np.linalg.eigh(0.5 * (c_eff + c_eff.T))
    if not np.all(np.isfinite(values)) or float(np.min(values)) <= 0.0:
        raise ValueError("effective covariance is not positive definite")
    precision = (vectors * (1.0 / values)) @ vectors.T
    precision = 0.5 * (precision + precision.T)
    return precision, values, c_tr, c_y


def _pair_cross(difference: np.ndarray, precision: np.ndarray) -> tuple[float, float]:
    d = np.asarray(difference, dtype=float)
    M, J = d.shape

    def calc(mask: np.ndarray) -> float:
        x = d[mask]
        mm = len(x)
        if mm < 2:
            raise ValueError("pair LOO has fewer than two members")
        total = np.sum(x, axis=0)
        self_term = sum(float(v @ precision @ v) for v in x)
        return (float(total @ precision @ total) - self_term) / float(mm * (mm - 1))

    full = calc(np.ones(M, dtype=bool))
    loo = min(calc(np.arange(M) != r) for r in range(M))
    return full, loo


def physical_components(stop_probability: np.ndarray, rectangles: np.ndarray, precision: np.ndarray) -> np.ndarray:
    p = np.asarray(stop_probability, dtype=float)
    rect = np.asarray(rectangles, dtype=int)
    S = p.shape[0]
    if rect.shape != (S, 4):
        raise ValueError("rectangles shape mismatch")
    dsu = _DSU(S)
    for i in range(S):
        for j in range(i + 1, S):
            if not adjacent(rect[i], rect[j]):
                continue
            d = p[i, :K_CAL, :] - p[j, :K_CAL, :]
            strength, loo = _pair_cross(d, precision)
            zero = _numerical_zero(strength, loo)
            if not (strength > zero and loo > zero):
                dsu.unite(i, j)

    labels: dict[int, int] = {}
    out = np.zeros(S, dtype=int)
    for s in range(S):
        root = dsu.find(s)
        if root not in labels:
            labels[root] = len(labels)
        out[s] = labels[root]
    return out


def source_stop_scores(stop_probability: np.ndarray, hit_fraction: np.ndarray, timesteps: int) -> np.ndarray:
    """Unit-weight fractional-Bernoulli proper log score per source and stop."""
    p = np.asarray(stop_probability, dtype=float)
    r = np.asarray(hit_fraction, dtype=float)
    if p.ndim != 3 or p.shape[2] != len(r):
        raise ValueError("stop score shape mismatch")
    eps = frequency_floor(timesteps)
    pp = np.clip(p[:, K_CAL:K_CAL + K_SCORE, :], eps, 1.0 - eps)
    S, _, J = pp.shape
    score = np.zeros((S, J), dtype=float)
    for s in range(S):
        for j in range(J):
            member = r[j] * np.log(pp[s, :, j]) + (1.0 - r[j]) * np.log1p(-pp[s, :, j])
            score[s, j] = _logmeanexp(member)
    return score


def _component_indices(component_id: np.ndarray) -> list[np.ndarray]:
    comp = np.asarray(component_id, dtype=int)
    return [np.flatnonzero(comp == c) for c in range(int(np.max(comp)) + 1)]


def _normalize(mass: np.ndarray, name: str) -> np.ndarray:
    q = np.asarray(mass, dtype=float)
    if q.ndim != 1 or np.any(q < 0.0) or not np.all(np.isfinite(q)) or not float(np.sum(q)) > 0.0:
        raise ValueError(f"invalid {name}")
    return q / float(np.sum(q))


def loso_cross_predictive_consensus(
    source_score: np.ndarray,
    component_id: np.ndarray,
    geometry_prior: np.ndarray,
    native_pre_prior: np.ndarray,
) -> tuple[bool, str, int | None, np.ndarray | None, tuple[tuple[int, ...], ...]]:
    """Select without each stop, then require held-out gain over native forecast."""
    a = np.asarray(source_score, dtype=float)
    S, J = a.shape
    q0 = _normalize(geometry_prior, "geometry prior")
    qn = _normalize(native_pre_prior, "native pre-update prior")
    if len(q0) != S or len(qn) != S:
        raise ValueError("LOSO prior shape mismatch")
    if J < 3:
        return False, "NEED_3_PHYSICAL_STOPS", None, None, tuple()

    components = _component_indices(component_id)
    if len(components) < 2:
        return False, "ONE_RESOLUTION_COMPONENT", None, None, tuple()

    best_sets: list[tuple[int, ...]] = []
    for h in range(J):
        train = np.arange(J) != h
        values = np.empty(len(components), dtype=float)
        for c, ix in enumerate(components):
            values[c] = _weighted_logsumexp(np.sum(a[ix][:, train], axis=1), q0[ix])
        best_sets.append(tuple(sorted(_best_tie_set(values))))

    common = set(best_sets[0])
    for best in best_sets[1:]:
        common &= set(best)
    if len(common) != 1:
        return False, "LOSO_COMPONENT_DISAGREE", None, None, tuple(best_sets)
    best = int(next(iter(common)))
    ix = components[best]

    native_null = np.asarray([_weighted_logsumexp(a[:, h], qn) for h in range(J)], dtype=float)
    component_heldout = np.asarray([_weighted_logsumexp(a[ix, h], q0[ix]) for h in range(J)], dtype=float)
    gain = component_heldout - native_null
    zero = _numerical_zero(component_heldout, native_null, gain)
    if np.any(gain <= zero):
        return False, "LOSO_NATIVE_NULL_FAIL", best, gain, tuple(best_sets)
    return True, "accepted", best, gain, tuple(best_sets)


def binary_stable_update(
    q_causal: np.ndarray,
    source_score: np.ndarray,
    selected_mask: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Cross-predictive binary B-versus-complement generalized-Bayes update."""
    qc = _normalize(q_causal, "causal state")
    a = np.asarray(source_score, dtype=float)
    mask = np.asarray(selected_mask, dtype=bool)
    if a.shape[0] != len(qc) or len(mask) != len(qc) or not np.any(mask) or np.all(mask):
        raise ValueError("invalid binary stable update")
    outside = ~mask
    mass_b = float(np.sum(qc[mask]))
    mass_o = float(np.sum(qc[outside]))
    if not (mass_b > 0.0 and mass_o > 0.0):
        raise ValueError("degenerate binary stable prior")

    increment = 0.0
    for h in range(a.shape[1]):
        score_b = _weighted_logsumexp(a[mask, h], qc[mask])
        score_o = _weighted_logsumexp(a[outside, h], qc[outside])
        increment += score_b - score_o

    log_odds = math.log(mass_b) - math.log(mass_o) + increment
    if log_odds >= 0.0:
        e = math.exp(-min(log_odds, 700.0))
        post_b = 1.0 / (1.0 + e)
    else:
        e = math.exp(max(log_odds, -700.0))
        post_b = e / (1.0 + e)

    out = np.zeros_like(qc)
    out[mask] = qc[mask] / mass_b * post_b
    out[outside] = qc[outside] / mass_o * (1.0 - post_b)
    return out / float(np.sum(out)), float(increment)


def information_projection_mass_floor(
    native_mass: np.ndarray,
    selected_mask: np.ndarray,
    alpha: float,
    geometry_prior: np.ndarray,
) -> tuple[np.ndarray, bool, float]:
    """KL-nearest native distribution subject to Q(B) >= alpha."""
    qn = _normalize(native_mass, "native posterior")
    q0 = _normalize(geometry_prior, "geometry prior")
    mask = np.asarray(selected_mask, dtype=bool)
    if len(qn) != len(q0) or len(mask) != len(qn) or not np.any(mask) or np.all(mask):
        raise ValueError("invalid mass-floor mask")
    if not (0.0 <= float(alpha) <= 1.0):
        raise ValueError("invalid alpha")
    beta = float(np.sum(qn[mask]))
    zero = _numerical_zero(alpha, beta)
    if beta + zero >= alpha:
        return qn.copy(), False, beta

    out = np.zeros_like(qn)
    if beta > 0.0:
        out[mask] = float(alpha) * qn[mask] / beta
    else:
        geometry_inside = float(np.sum(q0[mask]))
        if not geometry_inside > 0.0:
            raise ValueError("zero geometry support inside selected component")
        out[mask] = float(alpha) * q0[mask] / geometry_inside

    outside = ~mask
    native_outside = float(np.sum(qn[outside]))
    if native_outside > 0.0:
        out[outside] = (1.0 - float(alpha)) * qn[outside] / native_outside
    else:
        geometry_outside = float(np.sum(q0[outside]))
        if not geometry_outside > 0.0:
            raise ValueError("zero geometry support outside selected component")
        out[outside] = (1.0 - float(alpha)) * q0[outside] / geometry_outside
    out /= float(np.sum(out))
    return out, True, beta


def _apply_existing_floor(
    native_post_mass: np.ndarray,
    state: StableState,
    geometry_prior: np.ndarray,
) -> tuple[np.ndarray, bool, float | None, float | None]:
    if state.last_validated_mask is None:
        return _normalize(native_post_mass, "native posterior"), False, None, None
    mask = np.asarray(state.last_validated_mask, dtype=bool)
    alpha = float(np.sum(_normalize(state.q_causal, "causal state")[mask]))
    output, active, beta = information_projection_mass_floor(native_post_mass, mask, alpha, geometry_prior)
    return output, active, alpha, beta


def step(
    probability_by_block: np.ndarray,
    observed_hit_by_block: np.ndarray,
    physical_stop_id_by_block: np.ndarray,
    rectangles: np.ndarray,
    geometry_prior: np.ndarray,
    native_pre_prior: np.ndarray,
    native_post_mass: np.ndarray,
    timesteps: int,
    state: StableState,
    *,
    window_id: str,
) -> StepResult:
    """Consume one source-update window exactly once."""
    if not window_id:
        raise ValueError("window_id is required")
    if window_id in state.consumed_window_ids:
        raise ValueError("DUPLICATE_CONSUMED_WINDOW")

    next_state = state.copy()
    # Every raw window is consumed once even if the stable channel abstains.
    next_state.consumed_window_ids.add(window_id)

    bank = collapse_blocks_to_stops(probability_by_block, observed_hit_by_block, physical_stop_id_by_block)
    if bank.probability.shape[2] < 3:
        output, active, alpha, beta = _apply_existing_floor(native_post_mass, next_state, geometry_prior)
        return StepResult(False, "NEED_3_PHYSICAL_STOPS", output, next_state,
                          stop_count=bank.probability.shape[2], stop_ids=bank.stop_id,
                          block_counts=bank.block_count, alpha=alpha, beta=beta,
                          projection_active=active)

    precision, eigenvalues, _, _ = effective_precision(bank.probability, timesteps)
    component = physical_components(bank.probability, rectangles, precision)
    scores = source_stop_scores(bank.probability, bank.hit_fraction, timesteps)
    ok, reason, best, gains, best_sets = loso_cross_predictive_consensus(
        scores, component, geometry_prior, native_pre_prior)

    if not ok or best is None:
        output, active, alpha, beta = _apply_existing_floor(native_post_mass, next_state, geometry_prior)
        return StepResult(False, reason, output, next_state, component_id=component,
                          consensus_component=best, heldout_gain=gains,
                          stop_count=bank.probability.shape[2], stop_ids=bank.stop_id,
                          block_counts=bank.block_count, effective_eigenvalues=eigenvalues,
                          alpha=alpha, beta=beta, projection_active=active,
                          loso_best_sets=best_sets)

    mask = component == int(best)
    updated_causal, increment = binary_stable_update(next_state.q_causal, scores, mask)
    next_state.q_causal = updated_causal
    next_state.last_validated_mask = mask.copy()
    alpha = float(np.sum(updated_causal[mask]))
    output, active, beta = information_projection_mass_floor(native_post_mass, mask, alpha, geometry_prior)
    return StepResult(True, "accepted", output, next_state, component_id=component,
                      consensus_component=int(best), consensus_mask=mask,
                      heldout_gain=gains, stop_count=bank.probability.shape[2],
                      stop_ids=bank.stop_id, block_counts=bank.block_count,
                      effective_eigenvalues=eigenvalues,
                      causal_log_odds_increment=increment, alpha=alpha, beta=beta,
                      projection_active=active, loso_best_sets=best_sets)
