#!/usr/bin/env python3
"""Frozen reference for CTPI M3 PIP V0.

PIP = Predictive Information Planning.

M3 never updates the M1 source posterior and never refits M2.  It receives a
frozen source posterior and a feasible candidate-action response table, then
selects the action with maximal expected information about source identity.
The information is the posterior-weighted Jensen-Shannon divergence of the
source-conditioned Bernoulli detection predictions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

from ctpi_m2_tsdc_frozen_v0 import action_information_scores, binary_entropy

PAIR_TOL = 1e-12
TIE_TOL = 1e-15
MEMBER_COUNT = 8


def _validate_posterior(source_posterior: np.ndarray) -> np.ndarray:
    pi = np.asarray(source_posterior, dtype=np.float64)
    if pi.ndim != 1 or np.any(pi < 0.0) or not np.isfinite(pi).all():
        raise ValueError("PIP_POSTERIOR")
    if abs(float(np.sum(pi)) - 1.0) > PAIR_TOL:
        raise ValueError("PIP_POSTERIOR_MASS")
    return pi


def raw_transport_information_scores(source_posterior: np.ndarray,
                                     action_source_probability: np.ndarray) -> np.ndarray:
    """Comparator I(S;Y|a) using raw finite-8 transport event probabilities."""
    pi = _validate_posterior(source_posterior)
    q = np.asarray(action_source_probability, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != len(pi):
        raise ValueError("PIP_RAW_ACTION_SOURCE_SHAPE")
    if np.any(q <= 0.0) or np.any(q >= 1.0) or not np.isfinite(q).all():
        raise ValueError("PIP_RAW_PROBABILITY")
    mixture = q @ pi
    score = binary_entropy(mixture) - binary_entropy(q) @ pi
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("PIP_RAW_INFORMATION")
    return np.maximum(score, 0.0)


def finite8_counts_from_raw_probability(action_source_probability: np.ndarray) -> np.ndarray:
    q = np.asarray(action_source_probability, dtype=np.float64)
    raw = q * float(MEMBER_COUNT + 1) - 0.5
    k = np.rint(raw).astype(np.int64)
    if (
        np.max(np.abs(raw - k)) > 1e-9
        or np.any(k < 0)
        or np.any(k > MEMBER_COUNT)
    ):
        raise ValueError("PIP_RAW_NOT_FINITE8_JEFFREYS")
    return k


def stable_argmax(scores: np.ndarray) -> int:
    """Return the first maximum in the pre-frozen candidate order."""
    value = np.asarray(scores, dtype=np.float64)
    if value.ndim != 1 or len(value) == 0 or not np.isfinite(value).all():
        raise ValueError("PIP_ARGMAX")
    maximum = float(np.max(value))
    candidates = np.flatnonzero(value >= maximum - TIE_TOL)
    if len(candidates) == 0:
        raise RuntimeError("PIP_ARGMAX_EMPTY")
    return int(candidates[0])


@dataclass(frozen=True)
class ActionDecision:
    candidate_ids: tuple[int, ...]
    raw_scores: np.ndarray
    tsdc_scores: np.ndarray
    raw_selected_id: int
    tsdc_selected_id: int
    historical_next_id: int


def decide(source_posterior: np.ndarray,
           action_source_probability: np.ndarray,
           decision_sensor_state_ppm: float,
           candidate_ids: Sequence[int]) -> ActionDecision:
    """Score and select one action without truth, future observation, or tuning."""
    pi = _validate_posterior(source_posterior)
    q = np.asarray(action_source_probability, dtype=np.float64)
    ids = tuple(int(v) for v in candidate_ids)
    if len(ids) != q.shape[0] or len(set(ids)) != len(ids):
        raise ValueError("PIP_CANDIDATE_IDS")
    if len(ids) < 1:
        raise ValueError("PIP_NO_CANDIDATES")
    raw_scores = raw_transport_information_scores(pi, q)
    k = finite8_counts_from_raw_probability(q)
    tsdc_scores = action_information_scores(pi, k, float(decision_sensor_state_ppm))
    raw_index = stable_argmax(raw_scores)
    tsdc_index = stable_argmax(tsdc_scores)
    return ActionDecision(
        candidate_ids=ids,
        raw_scores=raw_scores,
        tsdc_scores=tsdc_scores,
        raw_selected_id=ids[raw_index],
        tsdc_selected_id=ids[tsdc_index],
        historical_next_id=ids[0],
    )


def selftest() -> None:
    pi = np.asarray([0.5, 0.5], dtype=np.float64)
    raw = np.asarray([
        [(4.0 + 0.5) / 9.0, (4.0 + 0.5) / 9.0],
        [(2.0 + 0.5) / 9.0, (6.0 + 0.5) / 9.0],
        [(0.0 + 0.5) / 9.0, (8.0 + 0.5) / 9.0],
    ], dtype=np.float64)
    result = decide(pi, raw, 0.0, [7, 8, 9])
    assert result.raw_selected_id == 9
    assert result.tsdc_selected_id == 9
    assert result.raw_scores[2] > result.raw_scores[1] > result.raw_scores[0]
    assert result.tsdc_scores[2] > result.tsdc_scores[1] > result.tsdc_scores[0]
    tie = np.tile(raw[0], (3, 1))
    tied = decide(pi, tie, 0.2, [11, 12, 13])
    assert tied.raw_selected_id == 11 and tied.tsdc_selected_id == 11
    forbidden = {
        "truth", "truth_source", "localization_error", "planner_reward",
        "fit", "fit_dev_mle", "source_posterior_update",
    }
    assert forbidden.isdisjoint(globals())
    print("CTPI_M3_PIP_FROZEN_V0_SELFTEST=PASS")


if __name__ == "__main__":
    selftest()
