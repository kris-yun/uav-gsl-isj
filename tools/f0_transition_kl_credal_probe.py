#!/usr/bin/env python3
"""F0 math sanity checks for Transition-KL Credal PMFS.

This script is intentionally data-free. It validates only the scalar KL-ball
and robust binary-information algebra. It is NOT evidence that the GSL method
improves localization.

No SciPy dependency is required.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple


EPS = 1e-12


def binary_entropy(p: float) -> float:
    p = min(max(p, EPS), 1.0 - EPS)
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))


def bernoulli_kl(q: float, p: float) -> float:
    q = min(max(q, EPS), 1.0 - EPS)
    p = min(max(p, EPS), 1.0 - EPS)
    return q * math.log(q / p) + (1.0 - q) * math.log((1.0 - q) / (1.0 - p))


def _bisect_root(fn, lo: float, hi: float, iters: int = 100) -> float:
    flo = fn(lo)
    fhi = fn(hi)
    if abs(flo) < 1e-14:
        return lo
    if abs(fhi) < 1e-14:
        return hi
    if flo * fhi > 0:
        raise ValueError("root is not bracketed")
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = fn(mid)
        if fm == 0:
            return mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def bernoulli_kl_interval(p: float, eta: float) -> Tuple[float, float]:
    """Return [l,u] = {q: kl(q||p)<=eta}."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must lie in [0,1]")
    if eta < 0:
        raise ValueError("eta must be non-negative")
    if eta == 0:
        return p, p

    p_clip = min(max(p, EPS), 1.0 - EPS)

    if bernoulli_kl(EPS, p_clip) <= eta:
        lower = 0.0
    else:
        lower = _bisect_root(lambda q: bernoulli_kl(q, p_clip) - eta, EPS, p_clip)

    if bernoulli_kl(1.0 - EPS, p_clip) <= eta:
        upper = 1.0
    else:
        upper = _bisect_root(lambda q: bernoulli_kl(q, p_clip) - eta, p_clip, 1.0 - EPS)

    return lower, upper


def mutual_information(prior: Sequence[float], q: Sequence[float]) -> float:
    z = sum(prior)
    pi = [x / z for x in prior]
    qbar = sum(w * x for w, x in zip(pi, q))
    return binary_entropy(qbar) - sum(w * binary_entropy(x) for w, x in zip(pi, q))


def robust_binary_mutual_information(
    prior: Sequence[float],
    nominal_hit: Sequence[float],
    eta: Sequence[float] | float,
) -> Tuple[float, List[float], List[Tuple[float, float]]]:
    """Worst-case I(S;Y) for rectangular Bernoulli KL ambiguity intervals.

    The KKT solution is a consensus/water-filling form
        q_s* = clip(c, [l_s,u_s])
    with c = sum_s pi_s q_s*.
    A one-dimensional bisection solves c.
    """
    if isinstance(eta, (int, float)):
        etas = [float(eta)] * len(nominal_hit)
    else:
        etas = list(eta)

    if not (len(prior) == len(nominal_hit) == len(etas)):
        raise ValueError("prior, nominal_hit and eta must have same length")

    z = sum(prior)
    pi = [x / z for x in prior]
    intervals = [bernoulli_kl_interval(p, r) for p, r in zip(nominal_hit, etas)]

    # If the intervals share a common point, nature can make Y independent of S.
    overlap_lo = max(lo for lo, _ in intervals)
    overlap_hi = min(hi for _, hi in intervals)
    if overlap_lo <= overlap_hi:
        c = 0.5 * (overlap_lo + overlap_hi)
        qstar = [c] * len(intervals)
        return 0.0, qstar, intervals

    def clip(c: float, bounds: Tuple[float, float]) -> float:
        lo, hi = bounds
        return min(max(c, lo), hi)

    def fixed_point_residual(c: float) -> float:
        return sum(w * clip(c, b) for w, b in zip(pi, intervals)) - c

    lo, hi = 0.0, 1.0
    flo, fhi = fixed_point_residual(lo), fixed_point_residual(hi)
    assert flo >= -1e-12 and fhi <= 1e-12

    for _ in range(120):
        mid = 0.5 * (lo + hi)
        fm = fixed_point_residual(mid)
        if fm > 0:
            lo = mid
        else:
            hi = mid

    c = 0.5 * (lo + hi)
    qstar = [clip(c, b) for b in intervals]
    return mutual_information(pi, qstar), qstar, intervals


def posterior_bounds(
    prior: Sequence[float],
    intervals: Sequence[Tuple[float, float]],
    observation: int,
) -> Tuple[List[float], List[float]]:
    if observation not in (0, 1):
        raise ValueError("observation must be 0 or 1")

    z = sum(prior)
    pi = [x / z for x in prior]

    if observation == 1:
        likelihood = list(intervals)
    else:
        likelihood = [(1.0 - hi, 1.0 - lo) for lo, hi in intervals]

    lows, highs = [], []
    for s, (a_s, b_s) in enumerate(likelihood):
        num_lo = pi[s] * a_s
        den_lo = num_lo + sum(
            pi[j] * likelihood[j][1] for j in range(len(pi)) if j != s
        )
        num_hi = pi[s] * b_s
        den_hi = num_hi + sum(
            pi[j] * likelihood[j][0] for j in range(len(pi)) if j != s
        )
        lows.append(0.0 if den_lo == 0 else num_lo / den_lo)
        highs.append(1.0 if den_hi == 0 else num_hi / den_hi)

    return lows, highs


def drift_bound(sigma: float, eta: float) -> float:
    return sigma * math.sqrt(2.0 * eta)


def main() -> None:
    prior = [1 / 3, 1 / 3, 1 / 3]
    h = [0.8, 0.5, 0.2]

    nominal = mutual_information(prior, h)
    r0, q0, i0 = robust_binary_mutual_information(prior, h, 0.0)
    assert abs(r0 - nominal) < 1e-10
    assert all(abs(a - b) < 1e-10 for a, b in zip(q0, h))

    previous_widths = [0.0] * len(h)
    previous_rmi = nominal
    print("eta, robust_mi, intervals")
    for eta in [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50]:
        rmi, qstar, intervals = robust_binary_mutual_information(prior, h, eta)
        widths = [u - l for l, u in intervals]
        assert all(w + 1e-12 >= old for w, old in zip(widths, previous_widths))
        assert rmi <= previous_rmi + 1e-10
        assert rmi <= nominal + 1e-10
        previous_widths = widths
        previous_rmi = rmi
        print(f"{eta:.3f}, {rmi:.8f}, {intervals}")

    eta = 0.05
    _, _, intervals = robust_binary_mutual_information(prior, h, eta)
    lo_hit, hi_hit = posterior_bounds(prior, intervals, 1)
    lo_miss, hi_miss = posterior_bounds(prior, intervals, 0)
    for lo, hi in zip(lo_hit + lo_miss, hi_hit + hi_miss):
        assert lo <= hi + 1e-12

    # Physical interpretation for the official PMFS sigma=0.5 m/s.
    sigma = 0.5
    expected = {
        0.02: 0.10,
        0.08: 0.20,
        0.125: 0.25,
        0.50: 0.50,
    }
    for eta_value, target in expected.items():
        assert abs(drift_bound(sigma, eta_value) - target) < 1e-12

    # Deliberately construct a nominally strong but highly ambiguous location A
    # and a weaker but better-calibrated location B. The robust objective should
    # be allowed to reverse the nominal ranking.
    p2 = [0.5, 0.5]
    A = [0.95, 0.05]
    B = [0.75, 0.25]
    nominal_A = mutual_information(p2, A)
    nominal_B = mutual_information(p2, B)
    robust_A, _, _ = robust_binary_mutual_information(p2, A, 0.50)
    robust_B, _, _ = robust_binary_mutual_information(p2, B, 0.02)
    assert nominal_A > nominal_B
    assert robust_A < robust_B

    print()
    print("nominal_A", nominal_A, "robust_A", robust_A)
    print("nominal_B", nominal_B, "robust_B", robust_B)
    print("F0_PASS")


if __name__ == "__main__":
    main()
