#!/usr/bin/env python3
"""Source-blind F0 solver for Shared Adversarial Transport Identifiability (SATI).

Given nominal candidate hit predictions h_s, sensitivities g_s, posterior weights w_s,
solve

    min_{||a||_2 <= r} Var_w(h + G a).

No source truth is used.
"""

from __future__ import annotations

import numpy as np


def _normalize_weights(weights: np.ndarray) -> np.ndarray:
    w = np.asarray(weights, dtype=float).reshape(-1)
    if np.any(w < 0):
        raise ValueError("weights must be nonnegative")
    z = float(w.sum())
    if z <= 0:
        raise ValueError("weights must have positive mass")
    return w / z


def weighted_variance(values: np.ndarray, weights: np.ndarray) -> float:
    x = np.asarray(values, dtype=float).reshape(-1)
    w = _normalize_weights(weights)
    if x.shape != w.shape:
        raise ValueError("values and weights shape mismatch")
    mu = float(w @ x)
    return float(w @ ((x - mu) ** 2))


def sati_trust_region(
    nominal: np.ndarray,
    gradients: np.ndarray,
    weights: np.ndarray,
    radius: float,
    *,
    tol: float = 1e-12,
    max_iter: int = 200,
):
    """Solve min_{||a||<=radius} Var_w(nominal + gradients @ a).

    Returns (robust_variance, adversarial_a, native_variance).
    """
    h = np.asarray(nominal, dtype=float).reshape(-1)
    G = np.asarray(gradients, dtype=float)
    w = _normalize_weights(weights)
    r = float(radius)

    if r < 0:
        raise ValueError("radius must be >= 0")
    if G.ndim != 2 or G.shape[0] != h.shape[0]:
        raise ValueError("gradients must have shape [num_sources, dim]")
    if w.shape != h.shape:
        raise ValueError("weights shape mismatch")

    C = np.diag(w) - np.outer(w, w)
    A = G.T @ C @ G
    b = G.T @ C @ h
    c = float(h.T @ C @ h)

    native = c
    if r == 0 or G.shape[1] == 0:
        return native, np.zeros(G.shape[1]), native

    # Minimum-norm unconstrained minimizer.
    a0 = -np.linalg.pinv(A, rcond=1e-12) @ b
    if np.linalg.norm(a0) <= r + tol:
        q = h + G @ a0
        return weighted_variance(q, w), a0, native

    I = np.eye(A.shape[0])

    def a_of_lambda(lam: float) -> np.ndarray:
        return -np.linalg.solve(A + lam * I, b)

    # Find a bracket where the regularized minimizer lies inside the ball.
    lo = 0.0
    hi = 1.0
    while np.linalg.norm(a_of_lambda(hi)) > r:
        hi *= 2.0
        if hi > 1e16:
            raise RuntimeError("failed to bracket trust-region multiplier")

    # Lambda increases => norm decreases.
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        a = a_of_lambda(mid)
        n = float(np.linalg.norm(a))
        if abs(n - r) <= tol:
            lo = hi = mid
            break
        if n > r:
            lo = mid
        else:
            hi = mid

    lam = 0.5 * (lo + hi)
    a_star = a_of_lambda(lam)
    q = h + G @ a_star
    robust = weighted_variance(q, w)

    return robust, a_star, native



def nuisance_orthogonal_source_variance(
    nominal: np.ndarray,
    gradients: np.ndarray,
    weights: np.ndarray,
):
    """Parameter-free residual source variance after projecting out transport nuisance.

    Returns (residual_variance, confounding_ratio, native_variance).
    """
    h = np.asarray(nominal, dtype=float).reshape(-1)
    G = np.asarray(gradients, dtype=float)
    w = _normalize_weights(weights)

    if G.ndim != 2 or G.shape[0] != h.shape[0]:
        raise ValueError("gradients must have shape [num_sources, dim]")
    if w.shape != h.shape:
        raise ValueError("weights shape mismatch")

    C = np.diag(w) - np.outer(w, w)
    A = G.T @ C @ G
    b = G.T @ C @ h
    native = float(h.T @ C @ h)

    explained = float(b.T @ np.linalg.pinv(A, rcond=1e-12) @ b) if A.size else 0.0
    residual = max(0.0, native - explained)

    if native <= 1e-15:
        confounding = 0.0
    else:
        confounding = min(1.0, max(0.0, explained / native))

    return residual, confounding, native


def _self_test():
    # zero radius exactly reproduces native
    h = np.array([0.1, 0.5, 0.9])
    G = np.array([[0.2, 0.0], [0.0, 0.1], [-0.2, 0.0]])
    w = np.array([0.2, 0.3, 0.5])

    robust, a, native = sati_trust_region(h, G, w, 0.0)
    assert abs(robust - native) < 1e-12
    assert np.allclose(a, 0)

    # adversary can only reduce/preserve source variance
    robust, a, native = sati_trust_region(h, G, w, 0.2)
    assert robust <= native + 1e-12
    assert np.linalg.norm(a) <= 0.2 + 1e-10

    # common sensitivity shift cannot alter candidate separation
    G_common = np.tile(np.array([[0.3, -0.1]]), (len(h), 1))
    robust, a, native = sati_trust_region(h, G_common, w, 0.5)
    assert abs(robust - native) < 1e-10

    # 1-D example where the adversary exactly collapses all candidates.
    h2 = np.array([0.2, 0.5, 0.8])
    G2 = np.array([[1.0], [0.0], [-1.0]])
    w2 = np.ones(3) / 3
    robust, a, native = sati_trust_region(h2, G2, w2, 0.3)
    assert robust < 1e-10
    assert abs(abs(a[0]) - 0.3) < 1e-8

    # Nuisance-orthogonal score: common shifts do not remove source information.
    residual, confounding, native = nuisance_orthogonal_source_variance(h, G_common, w)
    assert abs(residual - native) < 1e-10
    assert confounding < 1e-10

    # When source variation lies in the nuisance span, the residual is zero.
    residual, confounding, native = nuisance_orthogonal_source_variance(h2, G2, w2)
    assert residual < 1e-10
    assert abs(confounding - 1.0) < 1e-10


if __name__ == "__main__":
    _self_test()

    h = np.array([0.10, 0.45, 0.85, 0.65])
    G = np.array([
        [0.30, 0.05],
        [0.10, 0.10],
        [-0.20, 0.08],
        [-0.05, -0.05],
    ])
    w = np.array([0.15, 0.25, 0.35, 0.25])

    robust, a, native = sati_trust_region(h, G, w, radius=0.20)
    residual, confounding, _ = nuisance_orthogonal_source_variance(h, G, w)
    print("SATI/NOSI F0 algebra tests: PASS")
    print(f"native_variance={native:.10f}")
    print(f"robust_variance={robust:.10f}")
    print(f"nuisance_orthogonal_variance={residual:.10f}")
    print(f"transport_confounding_ratio={confounding:.10f}")
    print(f"ratio={robust/native:.6f}")
    print(f"adversarial_drift={a.tolist()}")
    print(f"adversarial_norm={np.linalg.norm(a):.10f}")
