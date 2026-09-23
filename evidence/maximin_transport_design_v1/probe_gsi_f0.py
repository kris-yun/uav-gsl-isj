#!/usr/bin/env python3
"""F0 algebra utilities for Transition-Ambiguous PMFS.

This file deliberately contains only source-blind algebra/unit tests.
It does NOT construct transport envelopes from data and does NOT use source truth.
"""

from __future__ import annotations

import math
from typing import Iterable, Tuple

import numpy as np


def drift_error_to_local_kl(drift_error: float, noise_std: float) -> float:
    """KL(N(mu+dt*dw, dt^2*sigma^2 I) || N(mu, dt^2*sigma^2 I))."""
    if noise_std <= 0:
        raise ValueError("noise_std must be > 0")
    return 0.5 * (float(drift_error) / float(noise_std)) ** 2


def _normalize_weights(weights: np.ndarray) -> np.ndarray:
    if weights.ndim != 1:
        raise ValueError("weights must be one-dimensional")
    if np.any(weights < 0):
        raise ValueError("weights must be nonnegative")
    total = float(weights.sum())
    if total <= 0:
        raise ValueError("weights must have positive mass")
    return weights / total


def weighted_variance(values: np.ndarray, weights: np.ndarray) -> float:
    weights = _normalize_weights(np.asarray(weights, dtype=float))
    values = np.asarray(values, dtype=float)
    if values.shape != weights.shape:
        raise ValueError("values and weights must have identical shape")
    mean = float(np.dot(weights, values))
    return float(np.dot(weights, (values - mean) ** 2))


def guaranteed_source_identifiability(
    lower: Iterable[float],
    upper: Iterable[float],
    weights: Iterable[float],
    *,
    tol: float = 1e-12,
    max_iter: int = 200,
) -> Tuple[float, np.ndarray, float]:
    """Minimum weighted variance over independent interval constraints.

    Solves
        min_q Var_w(q)
        s.t. lower_s <= q_s <= upper_s.

    KKT structure gives q_s = clip(mu, lower_s, upper_s), where
        mu = sum_s w_s clip(mu, lower_s, upper_s).

    Returns
    -------
    robust_variance, adversarial_q, mu
    """
    lo = np.asarray(list(lower), dtype=float)
    hi = np.asarray(list(upper), dtype=float)
    w = _normalize_weights(np.asarray(list(weights), dtype=float))

    if not (lo.ndim == hi.ndim == w.ndim == 1):
        raise ValueError("lower, upper, weights must be 1-D")
    if not (len(lo) == len(hi) == len(w)):
        raise ValueError("lower, upper, weights must have same length")
    if np.any(lo > hi):
        raise ValueError("lower cannot exceed upper")

    left = float(np.min(lo))
    right = float(np.max(hi))

    def f(mu: float) -> float:
        q = np.clip(mu, lo, hi)
        return float(np.dot(w, q) - mu)

    # Monotone non-increasing fixed-point residual.
    fl = f(left)
    fr = f(right)
    if fl < -tol or fr > tol:
        raise RuntimeError("fixed point was not bracketed")

    for _ in range(max_iter):
        mid = 0.5 * (left + right)
        fm = f(mid)
        if abs(fm) <= tol or (right - left) <= tol:
            left = right = mid
            break
        if fm > 0:
            left = mid
        else:
            right = mid

    mu = 0.5 * (left + right)
    q = np.clip(mu, lo, hi)
    var = weighted_variance(q, w)
    return var, q, mu


def _self_test() -> None:
    # 1) Point intervals recover native weighted variance.
    h = np.array([0.1, 0.4, 0.9])
    w = np.array([0.2, 0.3, 0.5])
    native = weighted_variance(h, w)
    robust, q, _ = guaranteed_source_identifiability(h, h, w)
    assert abs(native - robust) < 1e-11
    assert np.allclose(q, h)

    # 2) Common intersection means all candidates can be collapsed to one value.
    lo = np.array([0.1, 0.2, 0.3])
    hi = np.array([0.6, 0.5, 0.4])
    robust, q, _ = guaranteed_source_identifiability(lo, hi, w)
    assert robust < 1e-12
    assert np.max(q) - np.min(q) < 1e-10

    # 3) Disjoint intervals preserve guaranteed separation.
    lo = np.array([0.05, 0.70])
    hi = np.array([0.20, 0.90])
    w2 = np.array([0.5, 0.5])
    robust, q, _ = guaranteed_source_identifiability(lo, hi, w2)
    assert robust > 0
    assert q[0] <= 0.20 + 1e-12
    assert q[1] >= 0.70 - 1e-12

    # 4) Envelopes can only reduce or preserve variance when nominal h is feasible.
    h = np.array([0.05, 0.45, 0.95])
    lo = np.array([0.00, 0.35, 0.85])
    hi = np.array([0.15, 0.55, 1.00])
    native = weighted_variance(h, w)
    robust, _, _ = guaranteed_source_identifiability(lo, hi, w)
    assert robust <= native + 1e-12

    # 5) PMFS official sigma=0.5 sanity values.
    sigma = 0.5
    expected = {
        0.05: 0.005,
        0.10: 0.020,
        0.20: 0.080,
        0.25: 0.125,
        0.50: 0.500,
    }
    for dw, eta in expected.items():
        assert math.isclose(drift_error_to_local_kl(dw, sigma), eta, rel_tol=0, abs_tol=1e-12)


if __name__ == "__main__":
    _self_test()

    w = np.array([0.25, 0.35, 0.40])
    nominal = np.array([0.10, 0.45, 0.85])
    lower = np.array([0.05, 0.30, 0.75])
    upper = np.array([0.20, 0.60, 0.95])

    native = weighted_variance(nominal, w)
    robust, adversarial, mu = guaranteed_source_identifiability(lower, upper, w)

    print("F0 algebra tests: PASS")
    print(f"native_variance={native:.8f}")
    print(f"guaranteed_variance={robust:.8f}")
    print(f"adversarial_q={adversarial.tolist()}")
    print(f"fixed_point_mu={mu:.8f}")
