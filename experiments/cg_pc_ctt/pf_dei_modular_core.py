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
    # Runtime raw-double default. Historical six-decimal CSV replay must pass
    # its analytically derived serialization tolerance explicitly.
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
    """Map one chronology to the frozen Euclidean path representation.

    The level channel always has exactly the same normalization.  M4 adds only
    the adjacent increment channel, so `pfdei_ablate_temporal` is a literal
    one-module removal rather than a simultaneous rescaling.
    """
    a = log_level(x, reference_ppm)
    level = a / math.sqrt(a.size)
    if not temporal:
        return level
    if a.size < 2:
        raise ValueError("need >=2 samples for temporal representation")
    d = np.diff(a) / math.sqrt(a.size - 1)
    return np.concatenate([level, d])


def _path_tensor(x, reference_ppm: float, temporal: bool) -> np.ndarray:
    """Vectorized path features for arrays whose last dimension is time."""
    a = log_level(x, reference_ppm)
    level = a / math.sqrt(a.shape[-1])
    if not temporal:
        return level
    if a.shape[-1] < 2:
        raise ValueError("need >=2 samples for temporal representation")
    d = np.diff(a, axis=-1) / math.sqrt(a.shape[-1] - 1)
    return np.concatenate([level, d], axis=-1)


def path_distance(a, b, reference_ppm: float, temporal: bool) -> float:
    va = path_vector(a, reference_ppm, temporal)
    vb = path_vector(b, reference_ppm, temporal)
    if va.shape != vb.shape:
        raise ValueError("path shape mismatch")
    return float(np.linalg.norm(va - vb))


def coherent_scramble(x: np.ndarray) -> np.ndarray:
    """Destroy cross-time member identity while preserving each time slice exactly.

    x'[s,m,t] = x[s,(m+t) mod M,t]. At every t the multiset over m is identical,
    but no output member follows one original nuisance trajectory through time.
    """
    p = np.asarray(x, dtype=np.float64)
    if p.ndim != 3:
        raise ValueError("expected [S,M,T]")
    _, M, T = p.shape
    member = (np.arange(M, dtype=np.int64)[:, None] + np.arange(T, dtype=np.int64)[None, :]) % M
    return np.take_along_axis(p, member[None, :, :], axis=1)


def energy_scores(observed, predicted, reference_ppm: float, temporal: bool = True) -> np.ndarray:
    """Finite-ensemble energy score, vectorized over source/member dimensions.

    This is mathematically identical to
      mean_m ||y-x_m|| - (1/(2M^2)) sum_mn ||x_m-x_n||
    in the frozen path representation, but computes pairwise distances from a
    per-source Gram matrix.  It avoids an [S,M,M,D] broadcast tensor and avoids
    Python loops over S*M^2, which matters for 210 sources x 8 members x ~1680
    time samples x many replay prefixes.
    """
    p, y = _check_tensor(predicted, observed)
    pv = _path_tensor(p, reference_ppm, temporal)
    yv = _path_tensor(y, reference_ppm, temporal)

    p2 = np.einsum("smd,smd->sm", pv, pv, optimize=True)
    y2 = float(np.dot(yv, yv))
    py = np.einsum("smd,d->sm", pv, yv, optimize=True)
    d2 = np.maximum(p2 + y2 - 2.0 * py, 0.0)
    first = np.mean(np.sqrt(d2), axis=1)

    gram = np.einsum("smd,snd->smn", pv, pv, optimize=True)
    pair2 = np.maximum(p2[:, :, None] + p2[:, None, :] - 2.0 * gram, 0.0)
    second = np.sum(np.sqrt(pair2), axis=(1, 2)) / (2.0 * p.shape[1] * p.shape[1])
    return np.asarray(first - second, dtype=np.float64)


def mean_field_scores(observed, predicted, reference_ppm: float, temporal: bool = True) -> np.ndarray:
    p, y = _check_tensor(predicted, observed)
    mu = p.mean(axis=1)
    mv = _path_tensor(mu, reference_ppm, temporal)
    yv = _path_tensor(y, reference_ppm, temporal)
    return np.linalg.norm(mv - yv[None, :], axis=1)


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


def carrier_to_cell_projection(carrier_posterior, carrier_of_cell, reference_cell_mass) -> np.ndarray:
    """KL/I-projection from carrier mass to cell mass under a frozen reference.

    The carrier posterior is preserved exactly at the carrier marginal, while
    the within-carrier shape is inherited from `reference_cell_mass`.
    """
    q_carrier = _norm_mass(carrier_posterior)
    carrier_of_cell = np.asarray(carrier_of_cell, dtype=np.int64)
    ref = np.asarray(reference_cell_mass, dtype=np.float64)
    if carrier_of_cell.ndim != 1 or ref.ndim != 1 or carrier_of_cell.size != ref.size:
        raise ValueError("shape mismatch")
    if carrier_of_cell.size == 0 or np.any(carrier_of_cell < 0) or not np.all(np.isfinite(ref)) or np.any(ref < 0):
        raise ValueError("invalid carrier projection inputs")
    if q_carrier.size <= int(carrier_of_cell.max()):
        raise ValueError("carrier posterior too small for cell assignment")

    out = np.zeros_like(ref, dtype=np.float64)
    for carrier in range(q_carrier.size):
        mask = carrier_of_cell == carrier
        if not np.any(mask):
            raise ValueError("carrier has no reference cells")
        denom = float(ref[mask].sum())
        if not math.isfinite(denom) or denom <= 0.0:
            raise ValueError("reference mass missing within carrier")
        out[mask] = q_carrier[carrier] * ref[mask] / denom
    return out


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
