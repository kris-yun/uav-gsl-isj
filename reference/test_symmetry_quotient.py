#!/usr/bin/env python3
"""Deterministic invariance checks for the symmetry-quotient interpretation.

This is a mechanism test, not a localization benchmark.
"""

import math


def _logadd(a: float, b: float) -> float:
    if a == -math.inf:
        return b
    if b == -math.inf:
        return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def log_elementary_symmetric(log_weights, k: int) -> float:
    dp = [-math.inf] * (k + 1)
    dp[0] = 0.0
    for lw in log_weights:
        for j in range(k, 0, -1):
            dp[j] = _logadd(dp[j], dp[j - 1] + lw)
    return dp[k]


def conditional_loglik(y, psi) -> float:
    k = sum(y)
    return sum(yi * pi for yi, pi in zip(y, psi)) - log_elementary_symmetric(psi, k)


def bernoulli_loglik(y, psi, beta: float) -> float:
    total = 0.0
    for yi, pi in zip(y, psi):
        z = beta + pi
        if yi:
            total += -math.log1p(math.exp(-z)) if z >= 0 else z - math.log1p(math.exp(z))
        else:
            total += -z - math.log1p(math.exp(-z)) if z >= 0 else -math.log1p(math.exp(z))
    return total


def rotate(v, angle):
    c, s = math.cos(angle), math.sin(angle)
    return c * v[0] - s * v[1], s * v[0] + c * v[1]


def wind_relative(displacement, wind):
    norm = math.hypot(*wind)
    if norm <= 0.0:
        raise ValueError("wind vector must be non-zero")
    ux, uy = wind[0] / norm, wind[1] / norm
    r_parallel = displacement[0] * ux + displacement[1] * uy
    r_perp = abs(displacement[0] * uy - displacement[1] * ux)
    return r_parallel, r_perp


def test_common_logit_shift_quotient():
    psi = [
        -1.70, 0.55, 1.22, -0.18, 0.91,
        -0.63, 0.07, -1.31, 1.68, -0.42,
        0.23, 0.77, -0.88, 1.05, -1.12,
        0.36, -0.29, 1.41, -0.51, 0.11,
    ]
    y = [1 if i in {1, 4, 8, 11, 17} else 0 for i in range(len(psi))]
    betas = [-10.0, -3.0, 0.0, 2.5, 9.0]

    conditional = [conditional_loglik(y, [p + b for p in psi]) for b in betas]
    unconditional = [bernoulli_loglik(y, psi, b) for b in betas]

    conditional_spread = max(conditional) - min(conditional)
    unconditional_spread = max(unconditional) - min(unconditional)

    assert conditional_spread < 1e-10, conditional_spread
    assert unconditional_spread > 1.0, unconditional_spread

    return {
        "conditional_shift_spread": conditional_spread,
        "unconditional_shift_spread": unconditional_spread,
    }


def test_so2_wind_frame_invariance():
    displacement = (1.7, -0.4)
    wind = (0.3, 0.8)
    reference = wind_relative(displacement, wind)
    worst = 0.0

    for angle in (0.1, 0.7, 1.9, -2.4):
        transformed = wind_relative(rotate(displacement, angle), rotate(wind, angle))
        worst = max(
            worst,
            abs(reference[0] - transformed[0]),
            abs(reference[1] - transformed[1]),
        )

    assert worst < 1e-12, worst
    return {"so2_invariance_max_abs_error": worst}


def main():
    out = {}
    out.update(test_common_logit_shift_quotient())
    out.update(test_so2_wind_frame_invariance())
    print("SYMMETRY_QUOTIENT_MECHANISM_TEST_V1 PASS")
    for key, value in out.items():
        print(f"{key}={value:.17g}")


if __name__ == "__main__":
    main()
