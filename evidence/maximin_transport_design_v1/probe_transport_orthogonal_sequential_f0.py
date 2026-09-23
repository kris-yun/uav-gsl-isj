#!/usr/bin/env python3
"""F0 algebra probe for Transport-Orthogonal Sequential Source Identification.

Source-blind tests only. No source truth, no dataset tuning.

Core pairwise quantity:
    D_perp(B) = min_a ||d_B + J_B a||^2
              = d^T d - d^T J (J^T J)^dagger J^T d

Posterior-weighted source utility:
    I_perp(B) = 1/2 sum_{s,r} pi_s pi_r D_perp_sr(B)
"""

from __future__ import annotations

import numpy as np


def normalize_weights(w):
    w = np.asarray(w, dtype=float).reshape(-1)
    if np.any(w < 0) or float(w.sum()) <= 0:
        raise ValueError("invalid weights")
    return w / w.sum()


def native_weighted_variance(h, w):
    h = np.asarray(h, dtype=float).reshape(-1)
    w = normalize_weights(w)
    mu = float(w @ h)
    return float(w @ ((h - mu) ** 2))


def pair_transport_orthogonal_distance(delta_h, delta_g, rcond=1e-12):
    """Min_a ||delta_h + delta_g @ a||_2^2."""
    d = np.asarray(delta_h, dtype=float).reshape(-1)
    J = np.asarray(delta_g, dtype=float)
    if J.ndim == 1:
        J = J.reshape(-1, 1)
    if J.shape[0] != d.shape[0]:
        raise ValueError("row mismatch")

    if J.shape[1] == 0 or np.allclose(J, 0):
        return float(d @ d)

    A = J.T @ J
    b = J.T @ d
    explained = float(b.T @ np.linalg.pinv(A, rcond=rcond) @ b)
    out = float(d @ d - explained)
    # Roundoff can make a theoretically nonnegative quantity tiny-negative.
    return max(0.0, out)


def accumulated_identifiability(H, G, weights):
    """Posterior-weighted pairwise transport-orthogonal source identifiability.

    H: [S, M] nominal hit predictions for S source candidates over M measurements.
    G: [S, M, D] transport sensitivities.
    weights: [S] source posterior weights.
    """
    H = np.asarray(H, dtype=float)
    G = np.asarray(G, dtype=float)
    w = normalize_weights(weights)

    if H.ndim != 2:
        raise ValueError("H must be [S,M]")
    if G.ndim != 3:
        raise ValueError("G must be [S,M,D]")
    if H.shape[:2] != G.shape[:2]:
        raise ValueError("H/G shape mismatch")
    if H.shape[0] != w.shape[0]:
        raise ValueError("source-count mismatch")

    total = 0.0
    S = H.shape[0]
    for s in range(S):
        for r in range(S):
            if w[s] == 0 or w[r] == 0:
                continue
            dh = H[s] - H[r]
            dg = G[s] - G[r]
            total += 0.5 * w[s] * w[r] * pair_transport_orthogonal_distance(dh, dg)
    return float(total)


def marginal_gain(H_history, G_history, h_new, g_new, weights):
    H_history = np.asarray(H_history, dtype=float)
    G_history = np.asarray(G_history, dtype=float)
    h_new = np.asarray(h_new, dtype=float).reshape(-1)
    g_new = np.asarray(g_new, dtype=float)

    S = h_new.shape[0]
    if H_history.size == 0:
        H0 = np.empty((S, 0))
        G0 = np.empty((S, 0, g_new.shape[1]))
    else:
        H0 = H_history
        G0 = G_history

    before = accumulated_identifiability(H0, G0, weights) if H0.shape[1] else 0.0
    H1 = np.concatenate([H0, h_new[:, None]], axis=1)
    G1 = np.concatenate([G0, g_new[:, None, :]], axis=1)
    after = accumulated_identifiability(H1, G1, weights)
    return after - before, before, after


def _self_test():
    # T0: no nuisance -> one-cell marginal gain exactly equals native PMFS variance.
    h = np.array([0.10, 0.40, 0.85, 0.60])
    w = np.array([0.10, 0.25, 0.45, 0.20])
    g0 = np.zeros((len(h), 2))
    gain, _, _ = marginal_gain(
        np.empty((len(h), 0)),
        np.empty((len(h), 0, 2)),
        h,
        g0,
        w,
    )
    native = native_weighted_variance(h, w)
    assert abs(gain - native) < 1e-12, (gain, native)

    # T1: common-mode transport sensitivity cannot change pairwise source separation.
    common = np.tile(np.array([[0.3, -0.2]]), (len(h), 1))
    gain, _, _ = marginal_gain(
        np.empty((len(h), 0)),
        np.empty((len(h), 0, 2)),
        h,
        common,
        w,
    )
    assert abs(gain - native) < 1e-12, (gain, native)

    # T2: one scalar cell can be fully transport-confounded.
    dh = np.array([1.0])
    dg = np.array([[1.0]])
    assert pair_transport_orthogonal_distance(dh, dg) < 1e-12

    # T3: two individually confounded measurements can jointly deconfound.
    # cell 1: dh=1, dg=+1 -> residual 0
    # cell 2: dh=1, dg=-1 -> residual 0
    # together: d=[1,1], J=[1,-1], exactly orthogonal -> residual 2
    assert pair_transport_orthogonal_distance([1.0], [[1.0]]) < 1e-12
    assert pair_transport_orthogonal_distance([1.0], [[-1.0]]) < 1e-12
    joint = pair_transport_orthogonal_distance([1.0, 1.0], [[1.0], [-1.0]])
    assert abs(joint - 2.0) < 1e-12, joint

    # T4: accumulated identifiability is monotone under added measurements.
    rng = np.random.default_rng(0)
    for _ in range(50):
        S, M, D = 5, 4, 2
        H = rng.normal(size=(S, M))
        G = rng.normal(size=(S, M, D))
        w = rng.random(S)
        vals = []
        for m in range(1, M + 1):
            vals.append(accumulated_identifiability(H[:, :m], G[:, :m], w))
        assert all(vals[i + 1] + 1e-10 >= vals[i] for i in range(len(vals) - 1)), vals


if __name__ == "__main__":
    _self_test()
    print("TO sequential-identifiability F0 tests: PASS")
    print("Key signature: two individually confounded cells can be jointly source-identifying.")
