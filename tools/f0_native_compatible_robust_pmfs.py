#!/usr/bin/env python3
from __future__ import annotations

import random


def native_factor(measured, confidence, simulated, gamma):
    return 1.0 - confidence * gamma * abs(measured - simulated)


def native_source_score(measured, confidence, simulated, gamma):
    score = 1.0
    for m, c, h in zip(measured, confidence, simulated):
        score *= native_factor(m, c, h, gamma)
    return score


def robust_source_score_interval(measured, confidence, simulated_intervals, gamma):
    lo_score = 1.0
    hi_score = 1.0
    for m, c, bounds in zip(measured, confidence, simulated_intervals):
        lo, hi = bounds
        if lo > hi:
            raise ValueError("invalid interval")
        d_min = 0.0 if lo <= m <= hi else min(abs(m - lo), abs(m - hi))
        d_max = max(abs(m - lo), abs(m - hi))
        a_lo = 1.0 - c * gamma * d_max
        a_hi = 1.0 - c * gamma * d_min
        if a_lo < -1e-12:
            raise ValueError("negative PMFS compatibility")
        lo_score *= a_lo
        hi_score *= a_hi
    return lo_score, hi_score


def normalized_score_bounds(score_intervals):
    lows, highs = [], []
    for s, pair in enumerate(score_intervals):
        lo_s, hi_s = pair
        lower_den = lo_s + sum(hi for j, (_, hi) in enumerate(score_intervals) if j != s)
        upper_den = hi_s + sum(lo for j, (lo, _) in enumerate(score_intervals) if j != s)
        lows.append(0.0 if lower_den == 0 else lo_s / lower_den)
        highs.append(1.0 if upper_den == 0 else hi_s / upper_den)
    return lows, highs


def native_weighted_variance(weights, values):
    total = sum(weights)
    w = [x / total for x in weights]
    mean = sum(a * b for a, b in zip(w, values))
    return sum(a * (b - mean) ** 2 for a, b in zip(w, values))


def robust_separability_variance(weights, intervals):
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must have positive sum")
    w = [x / total for x in weights]

    overlap_lo = max(lo for lo, _ in intervals)
    overlap_hi = min(hi for _, hi in intervals)
    if overlap_lo <= overlap_hi:
        c = 0.5 * (overlap_lo + overlap_hi)
        return 0.0, c, [c] * len(intervals)

    def clip(c, bounds):
        lo, hi = bounds
        return min(max(c, lo), hi)

    def gradient_half(c):
        return sum(a * (c - clip(c, b)) for a, b in zip(w, intervals))

    lo = min(a for a, _ in intervals)
    hi = max(b for _, b in intervals)

    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if gradient_half(mid) < 0:
            lo = mid
        else:
            hi = mid

    c = 0.5 * (lo + hi)
    q_star = [clip(c, b) for b in intervals]
    var = native_weighted_variance(w, q_star)
    return var, c, q_star


def main():
    random.seed(20260923)

    for _ in range(1000):
        n_sources = 8
        n_cells = 20
        gamma = random.choice([0.3, 1.0])
        measured = [random.random() for _ in range(n_cells)]
        confidence = [random.random() for _ in range(n_cells)]
        hitmaps = [[random.random() for _ in range(n_cells)] for _ in range(n_sources)]
        weights = [random.random() + 1e-3 for _ in range(n_sources)]

        native_scores = [
            native_source_score(measured, confidence, h, gamma) for h in hitmaps
        ]
        score_intervals = [
            robust_source_score_interval(
                measured, confidence, [(x, x) for x in h], gamma
            )
            for h in hitmaps
        ]
        lower, upper = normalized_score_bounds(score_intervals)
        native_norm = [x / sum(native_scores) for x in native_scores]

        for p, lo, hi in zip(native_norm, lower, upper):
            assert abs(p - lo) < 1e-12
            assert abs(p - hi) < 1e-12

        cell_values = [hitmaps[s][0] for s in range(n_sources)]
        native_var = native_weighted_variance(weights, cell_values)
        robust_var, _, _ = robust_separability_variance(
            weights, [(x, x) for x in cell_values]
        )
        assert abs(native_var - robust_var) < 1e-12

    for _ in range(1000):
        n = 10
        weights = [random.random() + 1e-3 for _ in range(n)]
        values = [random.random() for _ in range(n)]
        radius = random.random() * 0.25
        intervals = [
            (max(0.0, x - radius), min(1.0, x + radius)) for x in values
        ]
        native_var = native_weighted_variance(weights, values)
        robust_var, _, _ = robust_separability_variance(weights, intervals)
        assert robust_var <= native_var + 1e-12

    weights = [0.1, 0.2, 0.3, 0.4]
    intervals = [(0.1, 0.6), (0.3, 0.8), (0.4, 0.9), (0.35, 0.7)]
    robust_var, _, q = robust_separability_variance(weights, intervals)
    assert abs(robust_var) < 1e-15
    assert max(q) - min(q) < 1e-15

    intervals = [(0.02, 0.15), (0.20, 0.35), (0.65, 0.78), (0.82, 0.95)]
    robust_var, c, q = robust_separability_variance(weights, intervals)
    assert robust_var > 0

    print("robust_var_example", robust_var)
    print("consensus", c)
    print("worst_case_candidate_hits", q)
    print("F0_NATIVE_COMPATIBLE_ROBUST_PMFS_PASS")


if __name__ == "__main__":
    main()
