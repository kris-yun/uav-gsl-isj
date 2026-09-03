#!/usr/bin/env python3
"""CTPI M2 TSDC reference: Transport-Sensor Detection Committor.

TSDC predicts the next measured detector event for a candidate source/action from
(1) the frozen eight-member transport ensemble and (2) the causal detector state
available at action-selection time.  It does not update the source posterior.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

MEMBER_COUNT = 8
THRESHOLD_PPM = 0.1
PAIR_TOL = 1e-12

# Frozen only after DEV.  Fresh confirmation must use these values unchanged.
DEV_BETA_V0 = np.asarray([
    -1.1915279295661385,
     1.0423583775118566,
     2.9896670550884170,
], dtype=np.float64)


def transport_coordinate(member_hit_count: np.ndarray) -> np.ndarray:
    """Finite-eight-member Jeffreys transport log-odds."""
    k = np.asarray(member_hit_count)
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("TSDC_MEMBER_HIT_COUNT")
    p = (k.astype(np.float64) + 0.5) / float(MEMBER_COUNT + 1)
    return np.log(p / (1.0 - p))


def detector_state_coordinate(measured_state_ppm: np.ndarray | float) -> np.ndarray:
    """Causal detector-memory coordinate at decision time.

    measured_state_ppm must be known before the candidate action is issued.
    Arrival/pre-stop values after the candidate transit are forbidden.
    """
    m = np.asarray(measured_state_ppm, dtype=np.float64)
    if np.any(m < 0.0) or not np.isfinite(m).all():
        raise ValueError("TSDC_DECISION_SENSOR_STATE")
    return np.log1p(m / THRESHOLD_PPM)


def feature_matrix(member_hit_count: np.ndarray,
                   decision_sensor_state_ppm: np.ndarray | float) -> np.ndarray:
    r_k = np.asarray(transport_coordinate(member_hit_count), dtype=np.float64)
    r_m = np.asarray(detector_state_coordinate(decision_sensor_state_ppm), dtype=np.float64)
    r_k, r_m = np.broadcast_arrays(r_k, r_m)
    return np.column_stack([r_k.reshape(-1), r_m.reshape(-1)])


def predict_committor(member_hit_count: np.ndarray,
                      decision_sensor_state_ppm: np.ndarray | float,
                      beta: Sequence[float] = DEV_BETA_V0) -> np.ndarray:
    """q=P(measured detector hit during next dwell | source, action, current state)."""
    b = np.asarray(beta, dtype=np.float64)
    if b.shape != (3,) or not np.isfinite(b).all():
        raise ValueError("TSDC_BETA")
    x = feature_matrix(member_hit_count, decision_sensor_state_ppm)
    eta = b[0] + x @ b[1:]
    q = expit(eta)
    if np.any(q <= 0.0) or np.any(q >= 1.0) or not np.isfinite(q).all():
        raise RuntimeError("TSDC_COMMITTOR_RANGE")
    return q


def fit_dev_mle(member_hit_count: np.ndarray,
                decision_sensor_state_ppm: np.ndarray,
                observed_next_event: np.ndarray) -> np.ndarray:
    """Unpenalized Bernoulli MLE for DEV only; no tunable hyperparameter.

    Do not call this function on a fresh confirmatory set.
    """
    x = feature_matrix(member_hit_count, decision_sensor_state_ppm)
    y = np.asarray(observed_next_event, dtype=np.float64).reshape(-1)
    if len(y) != len(x) or not np.all((y == 0.0) | (y == 1.0)):
        raise ValueError("TSDC_DEV_EVENT")
    X = np.column_stack([np.ones(len(x)), x])

    def objective(b: np.ndarray) -> tuple[float, np.ndarray]:
        eta = X @ b
        value = float(np.sum(np.logaddexp(0.0, eta) - y * eta))
        grad = X.T @ (expit(eta) - y)
        return value, grad

    fit = minimize(lambda b: objective(b)[0], np.zeros(3),
                   jac=lambda b: objective(b)[1], method="BFGS",
                   options={"gtol": 1e-10, "maxiter": 2000})
    b = np.asarray(fit.x, dtype=np.float64)
    _, grad = objective(b)
    if not np.isfinite(b).all() or np.linalg.norm(grad, ord=np.inf) > 1e-6:
        raise RuntimeError("TSDC_DEV_MLE")
    return b


def binary_entropy(p: np.ndarray | float) -> np.ndarray:
    q = np.asarray(p, dtype=np.float64)
    if np.any(q < 0.0) or np.any(q > 1.0):
        raise ValueError("TSDC_ENTROPY")
    out = np.zeros_like(q)
    m = (q > 0.0) & (q < 1.0)
    out[m] = -(q[m] * np.log(q[m]) + (1.0 - q[m]) * np.log1p(-q[m]))
    return out


def action_information_scores(source_posterior: np.ndarray,
                              action_source_hit_count: np.ndarray,
                              decision_sensor_state_ppm: float,
                              beta: Sequence[float] = DEV_BETA_V0) -> np.ndarray:
    """M3-facing I(S;Y|a) using TSDC, without changing the M1 posterior."""
    pi = np.asarray(source_posterior, dtype=np.float64)
    k = np.asarray(action_source_hit_count)
    if pi.ndim != 1 or np.any(pi < 0.0) or not np.isfinite(pi).all():
        raise ValueError("TSDC_POSTERIOR")
    if abs(float(pi.sum()) - 1.0) > 1e-12:
        raise ValueError("TSDC_POSTERIOR_MASS")
    if k.ndim != 2 or k.shape[1] != len(pi):
        raise ValueError("TSDC_ACTION_SOURCE_SHAPE")
    q = predict_committor(k, decision_sensor_state_ppm, beta).reshape(k.shape)
    mixture = q @ pi
    score = binary_entropy(mixture) - binary_entropy(q) @ pi
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("TSDC_INFORMATION")
    return np.maximum(score, 0.0)


def selftest() -> None:
    k = np.arange(9, dtype=np.int64)
    q0 = predict_committor(k, 0.0)
    q1 = predict_committor(k, 0.2)
    assert np.all(np.diff(q0) > 0.0)
    assert np.all(q1 > q0)

    posterior = np.asarray([0.5, 0.5])
    action_k = np.asarray([[4, 4], [0, 8]], dtype=np.int64)
    info = action_information_scores(posterior, action_k, 0.0)
    assert info[1] > info[0] + 1e-12
    print("CTPI_M2_TSDC_REFERENCE_SELFTEST=PASS")


if __name__ == "__main__":
    selftest()
