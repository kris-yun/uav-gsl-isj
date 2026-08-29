#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import numpy as np


class Mode(str, Enum):
    FULL = "pfdei_full"
    SHADOW = "pfdei_shadow"
    ABLATE_SENSOR = "pfdei_ablate_sensor"
    ABLATE_TEMPORAL = "pfdei_ablate_temporal"
    ABLATE_COHERENCE = "pfdei_ablate_coherence"
    ABLATE_NUISANCE = "pfdei_ablate_nuisance"


@dataclass(frozen=True)
class SensorInverseConfig:
    dt: float = 0.2
    tau: float = 1.2
    delay_samples: int = 2
    serialization_bound_ppm: float = 1e-10


@dataclass(frozen=True)
class InferenceResult:
    scores: np.ndarray
    z_evidence: np.ndarray
    posterior: np.ndarray
    selected_source: int


class StreamingSensorInverse:
    """Exact inverse for the frozen deterministic first-order delayed sensor.

    Forward contract:
        M_k = alpha M_{k-1} + (1-alpha) C_{k-delay}
    Hence:
        C_{k-delay} = (M_k-alpha M_{k-1})/(1-alpha)

    Returned arrays are aligned to physical concentration time, so the first
    `delay_samples` physical samples are not recoverable from a run that starts
    without pre-history and are omitted.
    """
    def __init__(self, cfg: SensorInverseConfig = SensorInverseConfig()):
        self.cfg = cfg
        if cfg.dt <= 0 or cfg.tau <= 0 or cfg.delay_samples < 0:
            raise ValueError("invalid sensor inverse config")
        self.alpha = math.exp(-cfg.dt / cfg.tau)

    def deconvolve(self, measured_ppm) -> np.ndarray:
        m = np.asarray(measured_ppm, dtype=np.float64)
        if m.ndim != 1 or m.size < 2 or not np.all(np.isfinite(m)):
            raise ValueError("measured_ppm must be finite 1-D")
        raw = (m[1:] - self.alpha * m[:-1]) / (1.0 - self.alpha)
        if np.any(raw < -self.cfg.serialization_bound_ppm):
            raise ValueError("inverse produced materially negative concentration")
        c = np.maximum(raw, 0.0)
        skip = max(self.cfg.delay_samples - 1, 0)
        if c.size <= skip:
            raise ValueError("trace too short after sensor-delay alignment")
        return c[skip:]


def _norm_mass(q) -> np.ndarray:
    a = np.asarray(q, dtype=np.float64)
    if a.ndim != 1 or np.any(a < 0) or not np.all(np.isfinite(a)) or a.sum() <= 0:
        raise ValueError("invalid prior mass")
    return a / a.sum()


def _check_tensor(x, observed) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(observed, dtype=np.float64)
    p = np.asarray(x, dtype=np.float64)
    if y.ndim != 1 or y.size < 3 or not np.all(np.isfinite(y)) or np.any(y < 0):
        raise ValueError("observed must be nonnegative finite [T]")
    if p.ndim != 3 or p.shape[0] < 2 or p.shape[1] < 2 or p.shape[2] != y.size:
        raise ValueError("predicted must be [S,M,T] with S,M>=2")
    if not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError("predicted must be nonnegative finite")
    return p, y


def log_level(x, reference_ppm: float) -> np.ndarray:
    if reference_ppm <= 0 or not math.isfinite(reference_ppm):
        raise ValueError("reference_ppm must be positive")
    a = np.asarray(x, dtype=np.float64)
    if np.any(a < 0) or not np.all(np.isfinite(a)):
        raise ValueError("nonnegative finite ppm required")
    return np.log1p(a / reference_ppm)


def path_vector(x, reference_ppm: float, temporal: bool) -> np.ndarray:
    """Map a chronology to a fixed Euclidean path representation.

    Level alone is intentionally order-insensitive under common permutation.
    FULL adds adjacent increments, making the representation depend on path order
    without a learned lag or tuned temporal bandwidth.
    """
    a = log_level(x, reference_ppm)
    if not temporal:
        return a
    if a.size < 2:
        raise ValueError("need >=2 samples for temporal representation")
    d = np.diff(a)
    return np.concatenate([a / math.sqrt(a.size), d / math.sqrt(d.size)])


def path_distance(a, b, reference_ppm: float, temporal: bool) -> float:
    va = path_vector(a, reference_ppm, temporal)
    vb = path_vector(b, reference_ppm, temporal)
    if va.shape != vb.shape:
        raise ValueError("path shape mismatch")
    return float(np.linalg.norm(va - vb))


def coherent_scramble(x: np.ndarray) -> np.ndarray:
    """Destroy cross-time member identity while preserving each time slice exactly.

    x'[s,m,t] = x[s,(m+t) mod M,t].  At each t the multiset over m is identical,
    but no output member follows one original nuisance trajectory through time.
    """
    p = np.asarray(x, dtype=np.float64)
    if p.ndim != 3:
        raise ValueError("expected [S,M,T]")
    S, M, T = p.shape
    out = np.empty_like(p)
    for t in range(T):
        for m in range(M):
            out[:, m, t] = p[:, (m + t) % M, t]
    return out


def energy_scores(observed, predicted, reference_ppm: float, temporal: bool = True) -> np.ndarray:
    p, y = _check_tensor(predicted, observed)
    S, M, _ = p.shape
    out = np.empty(S, dtype=np.float64)
    for s in range(S):
        first = sum(path_distance(y, p[s, m], reference_ppm, temporal) for m in range(M)) / M
        second = 0.0
        for m in range(M):
            for n in range(M):
                second += path_distance(p[s, m], p[s, n], reference_ppm, temporal)
        second /= (2.0 * M * M)
        out[s] = first - second
    return out


def mean_field_scores(observed, predicted, reference_ppm: float, temporal: bool = True) -> np.ndarray:
    p, y = _check_tensor(predicted, observed)
    mu = p.mean(axis=1)
    return np.asarray([path_distance(y, mu[s], reference_ppm, temporal) for s in range(mu.shape[0])])


def normal_midrank_evidence_lower_is_better(scores) -> np.ndarray:
    x = np.asarray(scores, dtype=np.float64)
    if x.ndim != 1 or x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("invalid scores")
    n = x.size
    order = np.argsort(x, kind="stable")
    rank = np.zeros(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i + 1
        tol = 1e-12 * (1.0 + abs(float(x[order[i]])))
        while j < n and abs(float(x[order[j]] - x[order[i]])) <= tol:
            j += 1
        mid = 0.5 * ((i + 1) + j)
        rank[order[i:j]] = mid
        i = j
    p = 1.0 - (rank - 0.5) / n
    return np.asarray([_normal_quantile(float(v)) for v in p], dtype=np.float64)


def _normal_quantile(probability: float) -> float:
    p = min(max(probability, 1e-12), 1.0 - 1e-12)
    a=(-3.969683028665376e1,2.209460984245205e2,-2.759285104469687e2,1.383577518672690e2,-3.066479806614716e1,2.506628277459239)
    b=(-5.447609879822406e1,1.615858368580409e2,-1.556989798598866e2,6.680131188771972e1,-1.328068155288572e1)
    c=(-7.784894002430293e-3,-3.223964580411365e-1,-2.400758277161838,-2.549732539343734,4.374664141464968,2.938163982698783)
    d=(7.784695709041462e-3,3.224671290700398e-1,2.445134137142996,3.754408661907416)
    low=0.02425; high=1.0-low
    if p < low:
        q=math.sqrt(-2.0*math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    if p > high:
        q=math.sqrt(-2.0*math.log(1.0-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)


def reversible_posterior(prior, z_evidence) -> np.ndarray:
    q0 = _norm_mass(prior)
    z = np.asarray(z_evidence, dtype=np.float64)
    if z.shape != q0.shape or not np.all(np.isfinite(z)):
        raise ValueError("evidence/prior shape mismatch")
    logq = np.log(np.maximum(q0, np.finfo(np.float64).tiny)) + z
    logq -= np.max(logq)
    q = np.exp(logq)
    return q / q.sum()


def infer(observed_physical_ppm, predicted_physical_ppm, prior, reference_ppm: float,
          mode: Mode | str = Mode.FULL) -> InferenceResult:
    mode = Mode(mode)
    p, y = _check_tensor(predicted_physical_ppm, observed_physical_ppm)
    if mode == Mode.ABLATE_COHERENCE:
        p = coherent_scramble(p)
    temporal = mode != Mode.ABLATE_TEMPORAL
    if mode == Mode.ABLATE_NUISANCE:
        score = mean_field_scores(y, p, reference_ppm, temporal=temporal)
    else:
        score = energy_scores(y, p, reference_ppm, temporal=temporal)
    z = normal_midrank_evidence_lower_is_better(score)
    q = reversible_posterior(prior, z)
    return InferenceResult(score, z, q, int(np.argmax(q)))
