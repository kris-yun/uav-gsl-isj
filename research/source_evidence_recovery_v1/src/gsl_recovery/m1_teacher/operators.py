"""Gaussian integration-by-parts lifts and a one-dimensional branch sampler.

These are executable reference operators, not a GADEN adjoint.  All derivatives
are with respect to *natural* Gaussian simulator noise; no artificial jitter is
introduced to make an inverse exist.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from scipy.special import ndtr
from scipy.optimize import brentq


@dataclass(frozen=True)
class LiftResult:
    lift: np.ndarray
    response_residual: float
    wind_residual: float
    feasible: bool
    rank: int


def gaussian_lift(jx, ju, source_tangent, *, preserve_wind=True, rcond=1e-10,
                  tolerance=1e-7) -> LiftResult:
    """Solve Jx v = d_s X, Ju v = 0 in minimum Euclidean norm.

    jx: [response_dim,noise_dim], ju: [wind_dim,noise_dim],
    source_tangent: [response_dim,source_dim]. Infeasibility is reported, never
    repaired with noise. A caller must reject infeasible teacher samples.
    """
    jx = np.atleast_2d(np.asarray(jx, float))
    ju = np.asarray(ju, float).reshape(-1, jx.shape[1])
    d = np.asarray(source_tangent, float)
    if d.ndim == 1:
        d = d[:, None]
    if d.shape[0] != jx.shape[0]:
        raise ValueError("source_tangent response dimension mismatch")
    p = np.eye(jx.shape[1])
    if preserve_wind and ju.size:
        p -= np.linalg.pinv(ju, rcond=rcond) @ ju
    gram = jx @ p @ jx.T
    v = p @ jx.T @ np.linalg.pinv(gram, rcond=rcond) @ d
    rx = float(np.linalg.norm(jx @ v - d))
    ru = float(np.linalg.norm(ju @ v)) if ju.size else 0.0
    feasible = rx <= tolerance * (1.0 + np.linalg.norm(d))
    if preserve_wind:
        feasible = feasible and ru <= tolerance * (1.0 + np.linalg.norm(d))
    return LiftResult(v, rx, ru, bool(feasible), int(np.linalg.matrix_rank(gram)))


def divergence_fd(lift_fn: Callable[[np.ndarray], np.ndarray], xi, step=1e-5):
    """Central-difference divergence, including the noise dependence of the lift.

    Reference implementation O(noise_dim) lift evaluations. High-dimensional
    native simulators require differentiable JVP/VJP or trace estimators.
    """
    xi = np.asarray(xi, float)
    base = np.asarray(lift_fn(xi), float)
    if base.ndim == 1:
        base = base[:, None]
    if base.shape[0] != xi.size:
        raise ValueError("lift first dimension must equal noise dimension")
    out = np.zeros(base.shape[1])
    for j in range(xi.size):
        h = step * max(1.0, abs(xi[j]))
        plus, minus = xi.copy(), xi.copy()
        plus[j] += h
        minus[j] -= h
        vp = np.asarray(lift_fn(plus)).reshape(base.shape)
        vm = np.asarray(lift_fn(minus)).reshape(base.shape)
        out += (vp[j] - vm[j]) / (2.0 * h)
    return out


def gaussian_score_weight(lift_fn, xi, step=1e-5):
    xi = np.asarray(xi, float)
    v = np.asarray(lift_fn(xi), float)
    if v.ndim == 1:
        v = v[:, None]
    return xi @ v - divergence_fd(lift_fn, xi, step=step)


def standard_normal_pdf(x):
    return np.exp(-0.5 * np.asarray(x) ** 2) / np.sqrt(2.0 * np.pi)


@dataclass(frozen=True)
class BoundarySample:
    root: float
    coefficient: np.ndarray
    plus_value: float
    minus_value: float
    derivative_residual: float


def sample_scalar_branch(g: Callable[[float], float], source_derivative,
                         noise_derivative: Callable[[float], float],
                         trace_plus: Callable[[float], float],
                         trace_minus: Callable[[float], float], bracket=(-12., 12.),
                         normal_lift=None) -> BoundarySample:
    """Snap a 1-D Gaussian noise coordinate to a simple gate root.

    Exact coarea weight phi(root)/|dg/dxi| times (dg/ds-grad(g).v).
    This scalar common-normal-lift version is sufficient for the supplied
    controlled gate (v_gate=0). Different lifts on the two sides require two
    separate weighted traces and are deliberately not silently approximated.
    The finite bracket must contain the unique relevant root.
    """
    root = float(brentq(g, *bracket))
    dg = float(noise_derivative(root))
    if abs(dg) < 1e-10:
        raise ValueError("nonregular branch: coarea derivative vanishes")
    ds = np.asarray(source_derivative, float)
    nv = np.zeros_like(ds) if normal_lift is None else np.asarray(normal_lift, float)
    coef = standard_normal_pdf(root) / abs(dg) * (ds - dg * nv)
    return BoundarySample(root, coef, float(trace_plus(root)),
                          float(trace_minus(root)), abs(float(g(root))))
