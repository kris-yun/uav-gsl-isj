#!/usr/bin/env python3
"""Reference mathematics for V4 OC-CRA.

Research-only implementation.  It deliberately uses physical-stop units,
proper log scores, cross-fitted source-null adequacy, a cumulative accepted
evidence ledger, and resolution-cut composition with a native PMFS posterior.

No source truth, House id, route id, localization error, temperature, blend
weight, or outcome-fitted threshold is an input.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

K_CAL = 4
K_SCORE = 4
EPS_FREQ = 0.5 / 201.0


def _logmeanexp(values: np.ndarray) -> float:
    a = np.asarray(values, dtype=float)
    m = float(np.max(a))
    return m + math.log(float(np.mean(np.exp(a - m))))


def _weighted_logsumexp(log_values: np.ndarray, weights: np.ndarray) -> float:
    v = np.asarray(log_values, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(v) == 0 or len(v) != len(w) or not np.all(np.isfinite(v)):
        raise ValueError("invalid weighted logsumexp input")
    if np.any(w < 0) or not float(np.sum(w)) > 0:
        raise ValueError("invalid weights")
    w = w / float(np.sum(w))
    a = v + np.log(np.maximum(w, np.finfo(float).tiny))
    m = float(np.max(a))
    return m + math.log(float(np.sum(np.exp(a - m))))


def adjacent(a: np.ndarray, b: np.ndarray) -> bool:
    """Exact V3 carrier adjacency contract, including corner touching."""
    ax1, ay1 = int(a[0] + a[2]), int(a[1] + a[3])
    bx1, by1 = int(b[0] + b[2]), int(b[1] + b[3])
    dx = max(int(b[0]) - ax1, int(a[0]) - bx1, 0)
    dy = max(int(b[1]) - ay1, int(a[1]) - by1, 0)
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
    probability: np.ndarray  # [S,M,J]
    hit_fraction: np.ndarray  # [J]
    stop_id: np.ndarray       # [J]


@dataclass
class Result:
    accepted: bool
    reason: str
    component_id: np.ndarray
    delta: np.ndarray | None = None
    causal_mass: np.ndarray | None = None
    fold_even: np.ndarray | None = None
    fold_odd: np.ndarray | None = None
    null_even: float | None = None
    null_odd: float | None = None
    best_component: int | None = None
    rival_component: int | None = None
    heldout_gain_even: float | None = None
    heldout_gain_odd: float | None = None
    stop_count: int = 0
    effective_eigenvalues: np.ndarray | None = None


def collapse_blocks_to_stops(
    probability: np.ndarray,
    observed_hit: np.ndarray,
    stop_id_per_block: np.ndarray,
    *,
    prediction_drift_tolerance: float = 1e-12,
) -> StopBank:
    """Collapse contiguous repeated blocks at one physical stop.

    Candidate/member predictions must be invariant within a stop.  Repeating a
    block therefore changes neither the stop prediction nor its statistical
    weight; only the observed hit fraction is retained.
    """
    p = np.asarray(probability, dtype=float)
    y = np.asarray(observed_hit, dtype=float)
    sid = np.asarray(stop_id_per_block)
    if p.ndim != 3:
        raise ValueError("probability must have shape [S,M,E]")
    S, M, E = p.shape
    if len(y) != E or len(sid) != E or M < K_CAL + K_SCORE:
        raise ValueError("block input shape mismatch")
    if E == 0:
        raise ValueError("empty block bank")
    if np.any((y < 0) | (y > 1)):
        raise ValueError("observed_hit must be in [0,1]")

    stop_p, stop_y, stop_ids = [], [], []
    start = 0
    for e in range(1, E + 1):
        if e == E or sid[e] != sid[start]:
            idx = np.arange(start, e)
            ref = p[:, :, idx[0]][:, :, None]
            drift = float(np.max(np.abs(p[:, :, idx] - ref)))
            if drift > prediction_drift_tolerance:
                raise ValueError(f"within-stop prediction drift {drift}")
            stop_p.append(np.mean(p[:, :, idx], axis=2))
            stop_y.append(float(np.mean(y[idx])))
            stop_ids.append(sid[start])
            start = e

    return StopBank(
        probability=np.stack(stop_p, axis=2),
        hit_fraction=np.asarray(stop_y, dtype=float),
        stop_id=np.asarray(stop_ids),
    )


def effective_precision(stop_probability: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Transport covariance plus finite observation covariance.

    One physical stop has effective sample size one.  Low transport variance is
    therefore not mapped to zero precision as it was by the V3 pseudoinverse.
    """
    p = np.asarray(stop_probability, dtype=float)
    S, M, J = p.shape
    if M < K_CAL:
        raise ValueError("insufficient calibration members")
    c_tr = np.zeros((J, J), dtype=float)
    n = 0
    for s in range(S):
        for m in range(K_CAL):
            for h in range(m + 1, K_CAL):
                d = p[s, m] - p[s, h]
                c_tr += 0.5 * np.outer(d, d)
                n += 1
    c_tr /= max(n, 1)
    c_tr = 0.5 * (c_tr + c_tr.T)

    pbar = np.mean(p[:, :K_CAL, :], axis=(0, 1))
    c_y = np.diag(pbar * (1.0 - pbar) + EPS_FREQ**2)
    c_eff = c_tr + c_y
    values, vectors = np.linalg.eigh(0.5 * (c_eff + c_eff.T))
    if not np.all(np.isfinite(values)) or float(np.min(values)) <= 0.0:
        raise ValueError("effective covariance is not positive definite")
    precision = (vectors * (1.0 / values)) @ vectors.T
    return 0.5 * (precision + precision.T), values


def _pair_cross(difference: np.ndarray, precision: np.ndarray) -> tuple[float, float]:
    d = np.asarray(difference, dtype=float)
    M, J = d.shape

    def calc(mask: np.ndarray) -> float:
        x = d[mask]
        mm = len(x)
        if mm < 2:
            raise ValueError("pair leave-one-out has <2 members")
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
            numerical_zero = 64.0 * np.finfo(float).eps * (1.0 + abs(strength) + abs(loo))
            if not (strength > numerical_zero and loo > numerical_zero):
                dsu.unite(i, j)
    labels: dict[int, int] = {}
    out = np.zeros(S, dtype=int)
    for s in range(S):
        root = dsu.find(s)
        if root not in labels:
            labels[root] = len(labels)
        out[s] = labels[root]
    return out


def _fold_scores(stop_probability: np.ndarray, hit_fraction: np.ndarray, mask: np.ndarray) -> np.ndarray:
    p = np.clip(stop_probability[:, K_CAL:K_CAL + K_SCORE, :], EPS_FREQ, 1.0 - EPS_FREQ)
    r = np.asarray(hit_fraction, dtype=float)
    S = p.shape[0]
    result = np.zeros(S, dtype=float)
    for s in range(S):
        member_scores = []
        for m in range(K_SCORE):
            pp = p[s, m, mask]
            rr = r[mask]
            member_scores.append(float(np.sum(rr * np.log(pp) + (1.0 - rr) * np.log1p(-pp))))
        result[s] = _logmeanexp(np.asarray(member_scores))
    return result


def _component_scores(source_scores: np.ndarray, component_id: np.ndarray, prior: np.ndarray) -> np.ndarray:
    count = int(np.max(component_id)) + 1
    out = np.full(count, -np.inf, dtype=float)
    for c in range(count):
        ix = np.flatnonzero(component_id == c)
        out[c] = _weighted_logsumexp(source_scores[ix], prior[ix])
    return out


def compute(
    probability: np.ndarray,
    observed_hit: np.ndarray,
    stop_id_per_block: np.ndarray,
    rectangles: np.ndarray,
    geometry_prior: np.ndarray,
    cumulative_ledger: np.ndarray | None = None,
) -> Result:
    bank = collapse_blocks_to_stops(probability, observed_hit, stop_id_per_block)
    p, r = bank.probability, bank.hit_fraction
    S, M, J = p.shape
    prior = np.asarray(geometry_prior, dtype=float)
    if len(prior) != S or np.any(prior < 0) or not float(np.sum(prior)) > 0:
        raise ValueError("invalid geometry prior")
    prior = prior / float(np.sum(prior))

    if J < 4:
        return Result(False, "NEED_4_PHYSICAL_STOPS", np.arange(S), stop_count=J)
    even_mask = np.arange(J) % 2 == 0
    odd_mask = ~even_mask
    if int(np.sum(even_mask)) < 2 or int(np.sum(odd_mask)) < 2:
        return Result(False, "NEED_2_STOPS_PER_FOLD", np.arange(S), stop_count=J)

    precision, eigenvalues = effective_precision(p)
    component = physical_components(p, rectangles, precision)
    component_count = int(np.max(component)) + 1
    if component_count < 2:
        return Result(False, "ONE_RESOLUTION_COMPONENT", component, stop_count=J,
                      effective_eigenvalues=eigenvalues)

    score_e = _fold_scores(p, r, even_mask)
    score_o = _fold_scores(p, r, odd_mask)
    null_e = _weighted_logsumexp(score_e, prior)
    null_o = _weighted_logsumexp(score_o, prior)
    comp_e = _component_scores(score_e, component, prior)
    comp_o = _component_scores(score_o, component, prior)

    best_e = int(np.argmax(comp_e))
    best_o = int(np.argmax(comp_o))
    heldout_gain_odd = float(comp_o[best_e] - null_o)
    heldout_gain_even = float(comp_e[best_o] - null_e)
    if not (heldout_gain_even > 0.0 and heldout_gain_odd > 0.0):
        return Result(False, "CROSS_FIT_SOURCE_NULL_FAIL", component,
                      fold_even=score_e, fold_odd=score_o,
                      null_even=null_e, null_odd=null_o,
                      heldout_gain_even=heldout_gain_even,
                      heldout_gain_odd=heldout_gain_odd,
                      stop_count=J, effective_eigenvalues=eigenvalues)

    combined = comp_e + comp_o
    order = np.argsort(combined)[::-1]
    best, rival = int(order[0]), int(order[1])
    if not (comp_e[best] > comp_e[rival] and comp_o[best] > comp_o[rival]):
        return Result(False, "FOLD_DIRECTION_DISAGREE", component,
                      fold_even=score_e, fold_odd=score_o,
                      null_even=null_e, null_odd=null_o,
                      best_component=best, rival_component=rival,
                      heldout_gain_even=heldout_gain_even,
                      heldout_gain_odd=heldout_gain_odd,
                      stop_count=J, effective_eigenvalues=eigenvalues)

    delta = np.zeros(S, dtype=float)
    for c in range(component_count):
        dc = (comp_e[c] - null_e) + (comp_o[c] - null_o)
        delta[component == c] = dc

    if cumulative_ledger is None:
        ledger = np.zeros(S, dtype=float)
    else:
        ledger = np.asarray(cumulative_ledger, dtype=float)
        if ledger.shape != (S,) or not np.all(np.isfinite(ledger)):
            raise ValueError("invalid cumulative ledger")
    updated = ledger + delta
    log_mass = np.log(np.maximum(prior, np.finfo(float).tiny)) + updated
    log_mass -= float(np.max(log_mass))
    causal = np.exp(log_mass)
    causal /= float(np.sum(causal))

    return Result(True, "accepted", component,
                  delta=delta, causal_mass=causal,
                  fold_even=score_e, fold_odd=score_o,
                  null_even=null_e, null_odd=null_o,
                  best_component=best, rival_component=rival,
                  heldout_gain_even=heldout_gain_even,
                  heldout_gain_odd=heldout_gain_odd,
                  stop_count=J, effective_eigenvalues=eigenvalues)


def resolution_cut_compose(
    native_mass: np.ndarray,
    causal_mass: np.ndarray,
    component_id: np.ndarray,
    geometry_prior: np.ndarray,
) -> np.ndarray:
    """Causal component mass + native conditional mass inside each component."""
    qn = np.maximum(np.asarray(native_mass, dtype=float), 0.0)
    qc = np.maximum(np.asarray(causal_mass, dtype=float), 0.0)
    q0 = np.maximum(np.asarray(geometry_prior, dtype=float), 0.0)
    comp = np.asarray(component_id, dtype=int)
    if not (len(qn) == len(qc) == len(q0) == len(comp)):
        raise ValueError("cut composition shape mismatch")
    if not float(np.sum(qn)) > 0 or not float(np.sum(qc)) > 0 or not float(np.sum(q0)) > 0:
        raise ValueError("empty cut distribution")
    qn /= float(np.sum(qn)); qc /= float(np.sum(qc)); q0 /= float(np.sum(q0))
    out = np.zeros_like(qn)
    for c in np.unique(comp):
        ix = np.flatnonzero(comp == c)
        causal_component = float(np.sum(qc[ix]))
        native_component = float(np.sum(qn[ix]))
        if native_component > 0.0:
            out[ix] = causal_component * qn[ix] / native_component
        else:
            geometry_component = float(np.sum(q0[ix]))
            if not geometry_component > 0.0:
                raise ValueError("zero native and geometry component mass")
            out[ix] = causal_component * q0[ix] / geometry_component
    out /= float(np.sum(out))
    return out
