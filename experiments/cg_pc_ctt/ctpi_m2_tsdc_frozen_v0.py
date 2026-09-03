#!/usr/bin/env python3
"""Frozen CTPI M2 TSDC V0 runtime operator.

TSDC = Transport-Sensor Detection Committor.

This file is CONFIRM/RUNTIME SAFE: it contains no fitting routine.  The three
coefficients are frozen from the spent 60-world DEV set and MUST NOT be changed
using fresh confirmatory outcomes.
"""
from __future__ import annotations

from typing import Sequence
import numpy as np
from scipy.special import expit

MEMBER_COUNT = 8
THRESHOLD_PPM = 0.1
PAIR_TOL = 1e-12
TSDC_BETA_V0 = np.asarray([
    -1.1915279295661385,
     1.0423583775118566,
     2.9896670550884170,
], dtype=np.float64)


def transport_coordinate(member_hit_count: np.ndarray) -> np.ndarray:
    """Jeffreys finite-ensemble transport log-odds from K in {0,...,8}."""
    k = np.asarray(member_hit_count)
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("TSDC_MEMBER_HIT_COUNT")
    p = (k.astype(np.float64) + 0.5) / float(MEMBER_COUNT + 1)
    return np.log(p / (1.0 - p))


def detector_state_coordinate(decision_sensor_state_ppm: np.ndarray | float) -> np.ndarray:
    """Causal detector-memory coordinate available before issuing the action.

    The allowed state is the measured sensor state at the end of the most recent
    completed sensing window (or 0 for the first action).  Any value sampled after
    the candidate action begins, including transit/arrival/pre-stop measurements,
    is forbidden.
    """
    m = np.asarray(decision_sensor_state_ppm, dtype=np.float64)
    if np.any(m < 0.0) or not np.isfinite(m).all():
        raise ValueError("TSDC_DECISION_SENSOR_STATE")
    return np.log1p(m / THRESHOLD_PPM)


def predict_committor(member_hit_count: np.ndarray,
                      decision_sensor_state_ppm: np.ndarray | float,
                      beta: Sequence[float] = TSDC_BETA_V0) -> np.ndarray:
    """P(next dwell measured detector hit | source, action, causal sensor state)."""
    b = np.asarray(beta, dtype=np.float64)
    if b.shape != (3,) or not np.array_equal(b, TSDC_BETA_V0):
        raise ValueError("TSDC_BETA_NOT_FROZEN_V0")
    r_k = np.asarray(transport_coordinate(member_hit_count), dtype=np.float64)
    r_m = np.asarray(detector_state_coordinate(decision_sensor_state_ppm), dtype=np.float64)
    r_k, r_m = np.broadcast_arrays(r_k, r_m)
    shape = r_k.shape
    x = np.column_stack([r_k.reshape(-1), r_m.reshape(-1)])
    eta = b[0] + x @ b[1:]
    q = expit(eta).reshape(shape)
    if np.any(q <= 0.0) or np.any(q >= 1.0) or not np.isfinite(q).all():
        raise RuntimeError("TSDC_COMMITTOR_RANGE")
    return q


def binary_entropy(p: np.ndarray | float) -> np.ndarray:
    q = np.asarray(p, dtype=np.float64)
    if np.any(q < 0.0) or np.any(q > 1.0) or not np.isfinite(q).all():
        raise ValueError("TSDC_ENTROPY")
    out = np.zeros_like(q)
    interior = (q > 0.0) & (q < 1.0)
    out[interior] = -(q[interior] * np.log(q[interior]) +
                      (1.0 - q[interior]) * np.log1p(-q[interior]))
    return out


def action_information_scores(source_posterior: np.ndarray,
                              action_source_hit_count: np.ndarray,
                              decision_sensor_state_ppm: float) -> np.ndarray:
    """M3-facing posterior-weighted I(S;Y|action) without changing M1 posterior."""
    pi = np.asarray(source_posterior, dtype=np.float64)
    k = np.asarray(action_source_hit_count)
    if pi.ndim != 1 or np.any(pi < 0.0) or not np.isfinite(pi).all():
        raise ValueError("TSDC_POSTERIOR")
    if abs(float(pi.sum()) - 1.0) > 1e-12:
        raise ValueError("TSDC_POSTERIOR_MASS")
    if k.ndim != 2 or k.shape[1] != len(pi):
        raise ValueError("TSDC_ACTION_SOURCE_SHAPE")
    q = predict_committor(k, decision_sensor_state_ppm)
    mixture = q @ pi
    score = binary_entropy(mixture) - binary_entropy(q) @ pi
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("TSDC_INFORMATION")
    return np.maximum(score, 0.0)


def selftest() -> None:
    k = np.arange(9, dtype=np.int64)
    q_empty = predict_committor(k, 0.0)
    q_memory = predict_committor(k, 0.2)
    assert np.all(np.diff(q_empty) > 0.0), "transport monotonicity"
    assert np.all(q_memory > q_empty), "sensor-state monotonicity"

    bad = TSDC_BETA_V0.copy(); bad[1] = np.nextafter(bad[1], np.inf)
    try:
        predict_committor(np.asarray([4], dtype=np.int64), 0.0, bad)
        raise AssertionError("beta mutation accepted")
    except ValueError as exc:
        assert str(exc) == "TSDC_BETA_NOT_FROZEN_V0"

    posterior = np.asarray([0.5, 0.5])
    action_k = np.asarray([[4, 4], [0, 8]], dtype=np.int64)
    info = action_information_scores(posterior, action_k, 0.0)
    assert info[1] > info[0] + 1e-12

    forbidden = {"fit_dev_mle", "posterior_from_log_score", "source_posterior_update"}
    assert forbidden.isdisjoint(globals())
    print("CTPI_M2_TSDC_FROZEN_V0_SELFTEST=PASS")


if __name__ == "__main__":
    selftest()
