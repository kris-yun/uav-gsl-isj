#!/usr/bin/env python3
"""Selftests for the frozen CTPI M2 forecast-only law."""
from __future__ import annotations

import numpy as np

from ctpi_m2_future_forecast import (
    baseline_source_probability,
    calibrated_source_probability,
    evaluate_confirmatory_gate,
    fit_calibration_table,
    mixture_probability,
)


def main() -> int:
    np.testing.assert_allclose(
        baseline_source_probability(np.arange(9, dtype=np.int64)),
        (np.arange(9) + 0.5) / 9.0,
    )

    posterior = np.asarray([[0.8, 0.2], [0.7, 0.3], [0.2, 0.8], [0.1, 0.9]])
    frozen = posterior.copy()
    counts = np.asarray([[0, 8], [1, 7], [2, 6], [3, 5]], dtype=np.int64)
    observed = np.asarray([0, 0, 1, 1], dtype=np.int8)
    fit = fit_calibration_table(posterior, counts, observed)
    table = np.asarray(fit["table"])
    assert np.array_equal(posterior, frozen), "M2 mutated the M1 posterior"
    assert np.all(np.diff(table) >= 0.0)
    assert fit["source_truth_access"] is False
    source = calibrated_source_probability(counts, table)
    mixture = mixture_probability(posterior, source)
    assert mixture.shape == observed.shape and np.all((mixture > 0.0) & (mixture < 1.0))

    source_perm = np.asarray([1, 0])
    permuted = mixture_probability(
        posterior[:, source_perm],
        calibrated_source_probability(counts[:, source_perm], table),
    )
    np.testing.assert_allclose(permuted, mixture, atol=1e-15)

    # A deliberately useful fixed table must pass the complete mechanical Gate
    # on 30 x 15 synthetic transitions; no truth-source label is accepted.
    events = 30 * 15
    houses = np.repeat(np.asarray(["H01", "H02", "H03"]), 10 * 15)
    tapes = np.asarray([f"{h}_{i:02d}" for h in ("H01", "H02", "H03")
                        for i in range(10) for _ in range(15)])
    y = np.tile(np.asarray([0, 1, 1], dtype=np.int8), events // 3)
    post = np.where(y[:, None] == 0, np.asarray([[0.9, 0.1]]),
                    np.asarray([[0.1, 0.9]])).astype(np.float64)
    k = np.tile(np.asarray([[0, 8]], dtype=np.int64), (events, 1))
    useful = np.asarray([0.02, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 0.98])
    # Vary actions while retaining the same mixture calibration direction.
    k[1::2] = np.asarray([1, 7])
    report = evaluate_confirmatory_gate(post, k, y, tapes, houses, useful)
    assert set(report["criteria"]) == {
        "pooled_nll_strictly_lower", "pooled_brier_strictly_lower",
        "paired_sign_support", "ece_not_worse", "no_stable_reverse_house",
        "finite_interior_probability", "at_least_three_table_values",
        "source_variation_every_house", "visited_action_variation_every_house",
    }
    assert report["truth_source_argument_present"] is False
    assert report["pass"] and report["verdict"] == "CTPI_M2_PREDICTIVE_GATE_PASS"

    collapsed = np.full(9, 0.5)
    failed = evaluate_confirmatory_gate(post, k, y, tapes, houses, collapsed)
    assert not failed["criteria"]["at_least_three_table_values"]
    assert failed["verdict"] == "CTPI_M2_PREDICTIVE_GATE_NO_GO"
    print("CTPI_M2_FUTURE_FORECAST_SELFTEST=PASS")
    print("CTPI_M2_FORECAST_CORE_OWNERSHIP_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
