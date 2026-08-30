#!/usr/bin/env python3
"""Regression tests for the frozen model-free cross-wind diagnosis."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from cross_wind_native_first_passage_diagnosis import (
    deterministic_permutation,
    exact_midrank,
    exact_sign_test,
    full_distances,
    predictive_cdf,
    survival_distances,
)


def main() -> int:
    labels = np.asarray([
        [[0, 80], [10, 80]],
        [[2, 80], [12, 80]],
        [[4, 80], [14, 80]],
        [[6, 80], [16, 80]],
        [[8, 80], [18, 80]],
        [[10, 80], [20, 80]],
    ], dtype=np.int16)
    cdf = predictive_cdf(labels)
    assert cdf.shape == (2, 2, 80)
    full_early = full_distances(cdf, np.asarray([1, 80]))
    full_late = full_distances(cdf, np.asarray([19, 80]))
    assert int(np.argmin(full_early)) == 0
    assert int(np.argmin(full_late)) == 1
    survival_early = survival_distances(labels, np.asarray([1, 80]))
    survival_late = survival_distances(labels, np.asarray([19, 80]))
    assert np.array_equal(survival_early, survival_late)
    assert exact_midrank(np.asarray([0.0, 1.0, 1.0, 2.0]), 1) == 2.5
    sign = exact_sign_test(np.asarray([1, 1, 2, 3]), np.asarray([2, 2, 2, 1]))
    assert sign == {"wins": 2, "losses": 1, "ties": 1, "one_sided_exact_p": 0.5}
    first = deterministic_permutation(1, 6, 17, 3)
    second = deterministic_permutation(1, 6, 17, 3)
    other = deterministic_permutation(2, 6, 17, 3)
    assert np.array_equal(first, second) and not np.array_equal(first, other)
    assert np.array_equal(np.sort(first), np.arange(80))
    print("CROSS_WIND_NATIVE_FIRST_PASSAGE_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

