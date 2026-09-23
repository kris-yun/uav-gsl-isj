#!/usr/bin/env python3
"""Controlled PMFS-like mechanism stress test for transport deconfounding.

This is NOT the official PMFS implementation and is NOT House-level evidence.
It is a deterministic physics-inspired unit/stress test used to falsify the
mechanism before expensive repaired-baseline experiments.

Expected qualitative result:
- zero/small mismatch: finite robust ~= Native;
- moderate mismatch: finite robust may rescue transport-confounded source cases;
- excessive mismatch: both degrade;
- unbounded orthogonalization can be over-conservative.
"""

from __future__ import annotations

import numpy as np


DT = 0.2
SIGMA = 0.5
HORIZON = 50
RELEASE_SCALE = 0.55
GAMMA = 0.3
NOMINAL_WIND = np.array([0.8, 0.0])
FD_EPS = 0.05


def hit_field(source, wind, grid_pts):
    source = np.asarray(source, float)
    wind = np.asarray(wind, float)
    X = np.asarray(grid_pts, float)
    density = np.zeros(len(X))

    for k in range(1, HORIZON + 1):
        mean = source + (DT * k) * wind
        var = (DT**2) * (SIGMA**2) * k + 0.20**2
        diff = X - mean
        density += np.exp(-0.5 * np.sum(diff * diff, axis=1) / var) / (2 * np.pi * var)

    return 1 - np.exp(-RELEASE_SCALE * density)


def normalize(w):
    w = np.asarray(w, float)
    return w / w.sum()


def truth_rank(p, truth):
    v = p[truth]
    better = np.sum(p > v + 1e-14)
    equal = np.sum(np.isclose(p, v, atol=1e-14, rtol=1e-12))
    return float(better + (equal + 1) / 2)


def min_quad_unbounded(A, b, c, tol=1e-10):
    vals, vecs = np.linalg.eigh(A)
    bh = np.einsum("...ji,...j->...i", vecs, b)
    inv = np.zeros_like(vals)
    np.divide(1.0, vals, out=inv, where=vals > tol)
    return np.maximum(0.0, c - np.sum(bh * bh * inv, axis=-1))


def min_quad_ball(A, b, c, radius, tol=1e-10, iterations=28):
    """min_{||a||<=radius} a^T A a + 2 b^T a + c, A PSD."""
    if radius == 0:
        return np.asarray(c, float).copy()

    vals, vecs = np.linalg.eigh(A)
    bh = np.einsum("...ji,...j->...i", vecs, b)

    inv = np.zeros_like(vals)
    np.divide(1.0, vals, out=inv, where=vals > tol)
    a0h = -bh * inv
    unconstrained = np.linalg.norm(a0h, axis=-1) <= radius + 1e-12

    out = np.maximum(0.0, c - np.sum(bh * bh * inv, axis=-1))
    need = ~unconstrained
    if not np.any(need):
        return out

    ev = vals[need]
    bb = bh[need]
    cc = np.asarray(c)[need]

    lo = np.zeros(len(cc))
    hi = np.ones(len(cc))

    def norm_at(lam):
        return np.sqrt(np.sum((bb / (ev + lam[:, None])) ** 2, axis=1))

    n = norm_at(hi)
    for _ in range(60):
        mask = n > radius
        if not np.any(mask):
            break
        hi[mask] *= 2
        n = norm_at(hi)

    for _ in range(iterations):
        mid = (lo + hi) / 2
        n = norm_at(mid)
        mask = n > radius
        lo[mask] = mid[mask]
        hi[~mask] = mid[~mask]

    lam = (lo + hi) / 2
    ah = -bb / (ev + lam[:, None])
    val = cc + np.sum(ev * ah * ah + 2 * bb * ah, axis=1)
    out[need] = np.maximum(0.0, val)
    return out


class Toy:
    def __init__(self):
        self.coords = np.array(
            [(x, y) for x in np.linspace(0, 10, 21) for y in np.linspace(0, 8, 17)]
        )
        self.sources = np.array(
            [(x, y) for x in np.linspace(1, 7, 7) for y in np.linspace(1, 7, 7)]
        )
        self.S = len(self.sources)
        self.M = len(self.coords)

        self.H = np.array([hit_field(s, NOMINAL_WIND, self.coords) for s in self.sources])
        self.G = np.empty((self.S, self.M, 2))

        for d in range(2):
            e = np.zeros(2)
            e[d] = FD_EPS
            hp = np.array([hit_field(s, NOMINAL_WIND + e, self.coords) for s in self.sources])
            hm = np.array([hit_field(s, NOMINAL_WIND - e, self.coords) for s in self.sources])
            self.G[:, :, d] = (hp - hm) / (2 * FD_EPS)

        self.pairs = np.array(
            [(i, j) for i in range(self.S) for j in range(i + 1, self.S)], int
        )
        self.dH = self.H[self.pairs[:, 0]] - self.H[self.pairs[:, 1]]
        self.dG = self.G[self.pairs[:, 0]] - self.G[self.pairs[:, 1]]

        self.action_idx = np.array(
            [
                i
                for i, (x, y) in enumerate(self.coords)
                if abs(x - round(x / 2) * 2) < 1e-9
                and abs(y - round(y / 2) * 2) < 1e-9
            ],
            int,
        )
        self.B0 = [self.nearest(z) for z in [(3, 2), (3, 6), (8, 2), (8, 6)]]

    def nearest(self, point):
        p = np.asarray(point)
        return int(np.argmin(np.sum((self.coords - p) ** 2, axis=1)))

    def posterior(self, obs_idx, obs_vals):
        pred = self.H[:, obs_idx]
        obs = np.asarray(obs_vals)[None, :]
        compat = np.clip(1 - GAMMA * np.abs(pred - obs), 1e-12, None)
        logp = np.log(compat).sum(axis=1)
        logp -= logp.max()
        p = np.exp(logp)
        return normalize(p)

    def sufficient_stats(self, B):
        J = self.dG[:, B, :]
        d = self.dH[:, B]
        A = np.einsum("pnd,pne->pde", J, J)
        b = np.einsum("pnd,pn->pd", J, d)
        c = np.einsum("pn,pn->p", d, d)
        return A, b, c

    def native_scores(self, B, p):
        mu = p @ self.H
        v = np.maximum(0.0, p @ (self.H**2) - mu**2)
        mask = np.zeros(self.M, bool)
        mask[self.action_idx] = True
        v[~mask] = -np.inf
        v[np.asarray(B, int)] = -np.inf
        return v

    def robust_scores(self, B, p, radius, unbounded=False):
        A, b, c = self.sufficient_stats(B)
        pair_w = p[self.pairs[:, 0]] * p[self.pairs[:, 1]]

        if unbounded:
            base = min_quad_unbounded(A, b, c)
        else:
            base = min_quad_ball(A, b, c, radius)

        ai = self.action_idx
        g = np.transpose(self.dG[:, ai, :], (1, 0, 2))
        d = np.transpose(self.dH[:, ai], (1, 0))

        A2 = A[None] + g[:, :, :, None] * g[:, :, None, :]
        b2 = b[None] + g * d[:, :, None]
        c2 = c[None] + d * d

        if unbounded:
            new = min_quad_unbounded(A2, b2, c2)
        else:
            new = min_quad_ball(A2, b2, c2, radius)

        vals = (new - base[None]) @ pair_w
        out = np.full(self.M, -np.inf)
        out[ai] = vals
        out[np.asarray(B, int)] = -np.inf
        return out

    def run(self, truth, true_wind, method, radius, steps=4):
        true_map = hit_field(self.sources[truth], true_wind, self.coords)

        B = list(self.B0)
        obs = [true_map[j] for j in B]
        p = self.posterior(B, obs)
        ranks = [truth_rank(p, truth)]

        for _ in range(steps):
            if method == "native":
                score = self.native_scores(B, p)
            elif method == "finite":
                score = self.robust_scores(B, p, radius, unbounded=False)
            elif method == "unbounded":
                score = self.robust_scores(B, p, radius, unbounded=True)
            else:
                raise ValueError(method)

            j = int(np.argmax(score))
            B.append(j)
            obs.append(true_map[j])
            p = self.posterior(B, obs)
            ranks.append(truth_rank(p, truth))

        return ranks


def summarize(values):
    a = np.asarray(values, float)
    return float(a.mean()), float(np.median(a))


def main():
    toy = Toy()

    # Exact reduction test: finite radius 0 must equal Native acquisition.
    p = np.ones(toy.S) / toy.S
    s_native = toy.native_scores(toy.B0, p)
    s_zero = toy.robust_scores(toy.B0, p, radius=0.0, unbounded=False)
    valid = toy.action_idx
    assert np.allclose(s_native[valid], s_zero[valid], atol=1e-10, equal_nan=True)

    # Stress A
    sources_25 = list(range(0, toy.S, 2))
    for sign in (+1, -1):
        wind = NOMINAL_WIND + np.array([0.0, sign * 0.20])
        rows = []
        for truth in sources_25:
            rows.append(
                (
                    toy.run(truth, wind, "native", 0.20)[-1],
                    toy.run(truth, wind, "finite", 0.20)[-1],
                    toy.run(truth, wind, "unbounded", 0.20)[-1],
                )
            )
        arr = np.asarray(rows)
        print(f"\nCrosswind {sign*0.20:+.2f} m/s, n={len(rows)}")
        for k, name in enumerate(["native", "finite", "unbounded"]):
            print(name, "mean/median", summarize(arr[:, k]))
        for k, name in [(1, "finite"), (2, "unbounded")]:
            print(
                name,
                "W/T/L",
                int(np.sum(arr[:, k] < arr[:, 0])),
                int(np.sum(arr[:, k] == arr[:, 0])),
                int(np.sum(arr[:, k] > arr[:, 0])),
            )

    # Stress B: mismatch gradient
    grad_sources = [0, 3, 6, 8, 12, 18, 24, 30, 36, 40, 45, 48]
    print("\nMismatch gradient")
    for mag in [0.05, 0.10, 0.20, 0.30]:
        wind = NOMINAL_WIND + np.array([0.0, mag])
        native = []
        robust = []
        for truth in grad_sources:
            native.append(toy.run(truth, wind, "native", mag)[-1])
            robust.append(toy.run(truth, wind, "finite", mag)[-1])

        n = np.asarray(native)
        r = np.asarray(robust)
        print(
            f"{mag:.2f}",
            "native", summarize(n),
            "finite", summarize(r),
            "W/T/L",
            int(np.sum(r < n)),
            int(np.sum(r == n)),
            int(np.sum(r > n)),
            "mean_improvement",
            float(np.mean(n - r)),
        )


if __name__ == "__main__":
    main()
