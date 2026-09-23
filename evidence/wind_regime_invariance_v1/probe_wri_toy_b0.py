#!/usr/bin/env python3
"""WRi-PMFS controlled mechanism probe.

No House data and no source-truth tuning.

Tests whether preserving wind environments provides source-identification
information beyond:
  - collapsing all history into the final wind,
  - using an average wind,
  - keeping only recent/current-regime data.

The toy uses a PMFS-like stochastic drift-diffusion filament age mixture.
"""

from __future__ import annotations

import argparse
import numpy as np


def hit_prob(points, source, wind, *, sigma_v=0.45, dt=0.4,
             ages=28, filaments_per_age=4, cell=0.45):
    pts = np.atleast_2d(points).astype(float)
    source = np.asarray(source, dtype=float)
    wind = np.asarray(wind, dtype=float)
    area = cell ** 2
    acc = np.zeros(len(pts), dtype=float)

    for k in range(1, ages + 1):
        mean = source + wind * dt * k
        var = (dt * sigma_v) ** 2 * k + cell ** 2 / 12
        d2 = ((pts - mean) ** 2).sum(axis=1)
        p_one = np.exp(-0.5 * d2 / var) / (2 * np.pi * var) * area
        p_one = np.clip(p_one, 0.0, 0.95)
        acc += 1.0 - (1.0 - p_one) ** filaments_per_age

    return np.clip(1.8 * acc / ages, 1e-5, 0.95)


def candidate_hits(points, sources, wind):
    return np.vstack([hit_prob(points, s, wind) for s in sources])


def loglik_counts(H, indices, counts, trials):
    p = np.clip(H[:, indices], 1e-6, 1 - 1e-6)
    k = np.asarray(counts, dtype=float)[None, :]
    n = np.asarray(trials, dtype=float)[None, :]
    return np.sum(k * np.log(p) + (n - k) * np.log(1 - p), axis=1)


def rank(log_score, truth):
    order = np.argsort(-log_score, kind="stable")
    return int(np.where(order == truth)[0][0]) + 1


def build_geometry():
    xs = np.linspace(0.5, 8.5, 13)
    ys = np.linspace(0.5, 6.5, 9)
    points = np.array([(x, y) for y in ys for x in xs])
    sources = np.array([(1.0, y) for y in [1.0, 2.25, 3.5, 4.75, 6.0]])
    nominal_wind = np.array([0.9, 0.0])

    requested = np.array([
        [2.5, 1.25], [4.5, 1.25],
        [2.5, 2.75], [4.5, 2.75],
        [2.5, 4.25], [4.5, 4.25],
        [2.5, 5.75], [4.5, 5.75],
    ])
    probe = np.array([
        int(np.argmin(((points - p) ** 2).sum(axis=1))) for p in requested
    ])
    return points, sources, nominal_wind, probe


def one_trial(points, sources, probe, winds, truth, seed, n_per_stop=30):
    rng = np.random.default_rng(seed)
    Hs = [candidate_hits(points, sources, np.asarray(w)) for w in winds]

    K = []
    for e in range(len(winds)):
        p_true = Hs[e][truth, probe]
        K.append(rng.binomial(n_per_stop, p_true))
    K = np.asarray(K)
    N = np.full_like(K, n_per_stop)

    idx_all = np.tile(probe, len(winds))
    k_all = K.reshape(-1)
    n_all = N.reshape(-1)

    # A: historical observations all explained by final/current wind.
    ll_collapse = loglik_counts(Hs[-1], idx_all, k_all, n_all)

    # B: all observations explained by the mean wind.
    Havg = candidate_hits(points, sources, np.mean(np.asarray(winds), axis=0))
    ll_average = loglik_counts(Havg, idx_all, k_all, n_all)

    # C: recent/current regime only.
    ll_recent = loglik_counts(Hs[-1], probe, K[-1], N[-1])

    # D: correctly factorized environments.
    ll_regime = np.zeros(len(sources))
    for e in range(len(winds)):
        ll_regime += loglik_counts(Hs[e], probe, K[e], N[e])

    # E: equal-count factorized control, 8 total stops over all 8 unique sites.
    even = np.arange(0, len(probe), 2)
    odd = np.arange(1, len(probe), 2)
    subsets = [even, odd]
    ll_equal = np.zeros(len(sources))
    for e, sub in enumerate(subsets):
        ll_equal += loglik_counts(Hs[e], probe[sub], K[e, sub], N[e, sub])

    # F: destructive environment-label swap.
    ll_swap = np.zeros(len(sources))
    for e in range(len(winds)):
        wrong = (e + 1) % len(winds)
        ll_swap += loglik_counts(Hs[wrong], probe, K[e], N[e])

    return {
        "collapse_current": rank(ll_collapse, truth),
        "average_wind": rank(ll_average, truth),
        "recent_only": rank(ll_recent, truth),
        "regime_all": rank(ll_regime, truth),
        "regime_equal": rank(ll_equal, truth),
        "label_swap_null": rank(ll_swap, truth),
    }


def evaluate(magnitude, seeds_per_source):
    points, sources, w0, probe = build_geometry()
    winds = [
        w0 + np.array([0.0, magnitude]),
        w0 + np.array([0.0, -magnitude]),
    ]

    records = []
    for truth in range(len(sources)):
        for seed in range(seeds_per_source):
            rr = one_trial(
                points, sources, probe, winds, truth,
                seed=100000 * truth + seed,
            )
            for method, truth_rank in rr.items():
                records.append((method, truth_rank))

    print(f"cross-wind switch magnitude = {magnitude:.3f} m/s")
    for method in sorted({m for m, _ in records}):
        ranks = np.array([r for m, r in records if m == method])
        print(
            f"{method:20s} "
            f"mean_rank={ranks.mean():.4f} "
            f"top1={(ranks == 1).mean():.4f} "
            f"top2={(ranks <= 2).mean():.4f}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--magnitude", type=float, default=0.18)
    parser.add_argument("--seeds-per-source", type=int, default=200)
    args = parser.parse_args()
    evaluate(args.magnitude, args.seeds_per_source)
