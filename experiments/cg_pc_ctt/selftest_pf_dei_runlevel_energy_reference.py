#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

from pf_dei_runlevel_energy_reference import (
    blocked_forward_source_transfer,
    energy_score,
    permutation_check,
    sanitize_physical_ppm,
    source_energy_scores,
    source_independent_null_score,
)


def main() -> int:
    rng = np.random.default_rng(20260828)
    T = 100
    M = 6
    S = 4
    t = np.linspace(0.0, 1.0, T)

    # One source family is coherently close to the observation in every segment;
    # rivals have distinct offsets/shapes. Transport members add coherent noise.
    y = 0.3 + 0.2 * np.sin(8.0 * np.pi * t) + 0.05 * t
    x = np.empty((S, M, T), dtype=np.float64)
    for m in range(M):
        member = 0.015 * rng.normal(size=T)
        x[0, m] = y + member
        x[1, m] = y + 0.20 + member
        x[2, m] = 0.15 + 0.10 * np.cos(4.0 * np.pi * t) + member
        x[3, m] = 0.65 - 0.10 * t + member
    q0 = np.full(S, 1.0 / S)

    scores = source_energy_scores(y, x)
    if int(np.argmin(scores)) != 0:
        raise AssertionError(scores)
    null = source_independent_null_score(y, x, q0)
    if not (scores[0] < null):
        raise AssertionError((scores[0], null))

    rows, summary = blocked_forward_source_transfer(y, x, q0)
    if not summary["predictive_pass"]:
        raise AssertionError(summary)
    if not all(r.selected_source == 0 and r.heldout_rank == 1 for r in rows):
        raise AssertionError(rows)

    p = np.asarray([2, 0, 3, 1])
    if permutation_check(y, x, q0, p) > 1e-12:
        raise AssertionError("source permutation contract failed")

    # Energy score treats the time sequence jointly. Duplicating a time sample
    # is not interpreted as an independent Bernoulli replicate; the normalized
    # multivariate distance remains finite and deterministic.
    es = energy_score(y, x[0])
    if not np.isfinite(es):
        raise AssertionError(es)

    # Tiny inverse-serialization negatives may be projected to zero, but a
    # material negative concentration must be rejected.
    a = sanitize_physical_ppm(np.asarray([0.1, -5e-6, 0.2]), 6.1e-6)
    if a[1] != 0.0:
        raise AssertionError(a)
    try:
        sanitize_physical_ppm(np.asarray([0.1, -1e-3, 0.2]), 6.1e-6)
    except ValueError:
        pass
    else:
        raise AssertionError("material negative concentration was not rejected")

    # An unrelated ensemble should not be able to beat a perfect deterministic
    # pair simply through ensemble spread correction.
    perfect = np.stack([y, y], axis=0)
    if abs(energy_score(y, perfect)) > 1e-15:
        raise AssertionError("perfect forecast did not score zero")

    print("PF_DEI_RUNLEVEL_ENERGY_REFERENCE_SELFTEST PASS")
    print(f"source0_score={scores[0]:.9g} null_score={null:.9g}")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
