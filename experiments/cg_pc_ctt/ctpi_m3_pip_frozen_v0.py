#!/usr/bin/env python3
"""Frozen M3 Predictive Information Planning (PIP) reference for CTPI.

F10 consumes the raw finite-8 transport probability; F11 consumes the frozen
TSDC committor.  Both arms use the same posterior-weighted binary mutual
information objective and the same deterministic tie-break.
"""
from __future__ import annotations

import argparse
import numpy as np

PAIR_TOL = 1.0e-12
MEMBER_COUNT = 8
TSDC_MODULE_SHA256 = "854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7"


def _normalized(posterior: np.ndarray) -> np.ndarray:
    p = np.asarray(posterior, dtype=np.float64)
    if p.ndim != 1 or p.size < 2 or np.any(p < 0.0) or not np.isfinite(p).all():
        raise ValueError("CTPI_M3_POSTERIOR")
    z = float(p.sum())
    if not np.isfinite(z) or z <= 0.0:
        raise ValueError("CTPI_M3_POSTERIOR_MASS")
    return p / z


def binary_entropy(probability: np.ndarray | float) -> np.ndarray:
    p = np.asarray(probability, dtype=np.float64)
    if np.any((p < 0.0) | (p > 1.0)) or not np.isfinite(p).all():
        raise ValueError("CTPI_M3_ENTROPY_INPUT")
    out = np.zeros_like(p)
    m = (p > 0.0) & (p < 1.0)
    out[m] = -(p[m] * np.log(p[m]) + (1.0 - p[m]) * np.log1p(-p[m]))
    return out


def raw_probability(action_source_hit_count: np.ndarray) -> np.ndarray:
    k = np.asarray(action_source_hit_count)
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M3_MEMBER_HIT_COUNT")
    return (k.astype(np.float64) + 0.5) / float(MEMBER_COUNT + 1)


def information_scores(source_posterior: np.ndarray,
                       action_source_probability: np.ndarray) -> np.ndarray:
    """I(S;Y|a) for binary next-dwell detector event, in nats."""
    pi = _normalized(source_posterior)
    q = np.asarray(action_source_probability, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != pi.size or np.any((q <= 0.0) | (q >= 1.0)) or not np.isfinite(q).all():
        raise ValueError("CTPI_M3_ACTION_SOURCE_PROBABILITY")
    mixture = q @ pi
    score = binary_entropy(mixture) - binary_entropy(q) @ pi
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("CTPI_M3_INFORMATION_INVALID")
    return np.maximum(score, 0.0)


def choose_information_action(source_posterior: np.ndarray,
                              action_source_probability: np.ndarray,
                              feasible: np.ndarray,
                              travel_cost: np.ndarray) -> tuple[int, np.ndarray]:
    """Information first; existing travel cost is tie-break only; then index."""
    score = information_scores(source_posterior, action_source_probability)
    allowed = np.asarray(feasible, dtype=np.bool_)
    cost = np.asarray(travel_cost, dtype=np.float64)
    if allowed.shape != score.shape or cost.shape != score.shape or not np.any(allowed):
        raise ValueError("CTPI_M3_FEASIBILITY")
    if np.any(cost < 0.0) or not np.isfinite(cost).all():
        raise ValueError("CTPI_M3_TRAVEL_COST")
    best = float(np.max(score[allowed]))
    tied = allowed & (np.abs(score - best) <= PAIR_TOL)
    best_cost = float(np.min(cost[tied]))
    finalists = np.flatnonzero(tied & (np.abs(cost - best_cost) <= PAIR_TOL))
    if finalists.size == 0:
        raise RuntimeError("CTPI_M3_NO_FINALIST")
    return int(finalists[0]), score


def f10_probabilities(action_source_hit_count: np.ndarray) -> np.ndarray:
    return raw_probability(action_source_hit_count)


def f11_probabilities(action_source_hit_count: np.ndarray,
                      decision_sensor_state_ppm: float,
                      tsdc_module) -> np.ndarray:
    k = np.asarray(action_source_hit_count)
    if k.ndim != 2:
        raise ValueError("CTPI_M3_ACTION_SOURCE_SHAPE")
    return np.asarray(tsdc_module.predict_committor(k, float(decision_sensor_state_ppm)), dtype=np.float64)


def selftest() -> None:
    pi = np.asarray([0.5, 0.5])
    k = np.asarray([[4, 4], [0, 8], [2, 6]], dtype=np.int64)
    p10 = f10_probabilities(k)
    s10 = information_scores(pi, p10)
    assert s10[1] > s10[0] + 1e-12
    choice, score = choose_information_action(pi, p10, np.ones(3, dtype=bool), np.asarray([1., 3., 2.]))
    assert choice == int(np.argmax(score))
    qflat = np.full((3, 2), 0.25)
    np.testing.assert_allclose(information_scores(pi, qflat), 0.0, atol=1e-15)
    perm = np.asarray([1, 0])
    np.testing.assert_allclose(information_scores(pi[perm], p10[:, perm]), s10, atol=1e-15)
    print("CTPI_M3_PIP_FROZEN_V0_SELFTEST=PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if not args.selftest:
        ap.error("run --selftest")
    selftest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
