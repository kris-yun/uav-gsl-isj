#!/usr/bin/env python3
"""Parameter-frozen CTPI inference and active-sensing reference operators.

The three load-bearing roles are deliberately separated:

* M1 CREL supplies member-level route encounter counts.
* M2 converts the complete empirical count law into source evidence.
* M3 selects a feasible action by posterior-weighted predictive information.

No source truth, outcome-tuned temperature, posterior blend, neural model, or
candidate-specific nuisance fit enters this module.
"""
from __future__ import annotations

import argparse
import math

import numpy as np

from ctpi_full_law_core import count_histograms, f00_qbar


JEFFREYS_CATEGORICAL_ALPHA = 0.5
PAIR_TOL = 1.0e-12


def _normalized_prior(prior: np.ndarray) -> np.ndarray:
    q = np.asarray(prior, dtype=np.float64)
    if q.ndim != 1 or q.size < 2 or np.any(q < 0.0) or not np.isfinite(q).all():
        raise ValueError("CTPI_PRIOR_INPUT")
    total = float(np.sum(q))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("CTPI_PRIOR_MASS")
    return q / total


def posterior_from_log_score(prior: np.ndarray, log_score: np.ndarray) -> np.ndarray:
    """Normalize q0(s) exp(log_score(s)) without a blend or temperature."""
    q = _normalized_prior(prior)
    score = np.asarray(log_score, dtype=np.float64)
    if score.shape != q.shape or not np.isfinite(score).all():
        raise ValueError("CTPI_LOG_SCORE_INPUT")
    shifted = np.log(q) + score
    shifted -= float(np.max(shifted))
    mass = np.exp(shifted)
    total = float(np.sum(mass))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("CTPI_POSTERIOR_MASS")
    result = mass / total
    if abs(float(np.sum(result)) - 1.0) > 1.0e-12:
        raise RuntimeError("CTPI_POSTERIOR_NORMALIZATION")
    return result


def f00_mean_count_log_score(
    counts: np.ndarray, observed_hit_count: int, stop_count: int,
) -> np.ndarray:
    """Frozen M1-only mean-projection score used by F00."""
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2 or not 0 <= int(observed_hit_count) <= int(stop_count):
        raise ValueError("CTPI_F00_SCORE_INPUT")
    q = f00_qbar(k, int(stop_count))
    h = int(observed_hit_count)
    n = int(stop_count)
    return h * np.log(q) + (n - h) * np.log1p(-q)


def full_law_categorical_log_score(
    counts: np.ndarray,
    observed_hit_count: int,
    stop_count: int,
    *,
    alpha: float = JEFFREYS_CATEGORICAL_ALPHA,
) -> np.ndarray:
    """M2 full-law log score for the observed cumulative encounter count.

    Each source has one empirical categorical law over K=0..N from its
    coherent transport members.  A symmetric Jeffreys prior is integrated
    analytically.  This is a source-independent finite-ensemble predictive
    law, not a fitted likelihood temperature.
    """
    k = np.asarray(counts, dtype=np.int64)
    n = int(stop_count)
    h = int(observed_hit_count)
    if k.ndim != 2 or k.shape[1] < 1 or n < 1 or not 0 <= h <= n:
        raise ValueError("CTPI_FULL_LAW_SCORE_INPUT")
    if not math.isclose(float(alpha), JEFFREYS_CATEGORICAL_ALPHA,
                        rel_tol=0.0, abs_tol=0.0):
        raise ValueError("CTPI_FULL_LAW_ALPHA_NOT_FROZEN")
    hist = count_histograms(k, n).astype(np.float64)
    probability = (hist[:, h] + alpha) / (
        float(k.shape[1]) + alpha * float(n + 1)
    )
    if np.any(probability <= 0.0) or np.any(probability >= 1.0) or not np.isfinite(probability).all():
        raise RuntimeError("CTPI_FULL_LAW_PROBABILITY")
    return np.log(probability)


def f00_posterior(
    prior: np.ndarray, counts: np.ndarray, observed_hit_count: int, stop_count: int,
) -> np.ndarray:
    return posterior_from_log_score(
        prior, f00_mean_count_log_score(counts, observed_hit_count, stop_count)
    )


def full_law_posterior(
    prior: np.ndarray, counts: np.ndarray, observed_hit_count: int, stop_count: int,
) -> np.ndarray:
    return posterior_from_log_score(
        prior, full_law_categorical_log_score(counts, observed_hit_count, stop_count)
    )


def binary_entropy(probability: np.ndarray | float) -> np.ndarray:
    p = np.asarray(probability, dtype=np.float64)
    if np.any((p < 0.0) | (p > 1.0)) or not np.isfinite(p).all():
        raise ValueError("CTPI_BINARY_ENTROPY_INPUT")
    result = np.zeros_like(p)
    interior = (p > 0.0) & (p < 1.0)
    result[interior] = -(
        p[interior] * np.log(p[interior]) +
        (1.0 - p[interior]) * np.log1p(-p[interior])
    )
    return result


def action_information_scores(
    posterior: np.ndarray, action_member_hits: np.ndarray,
) -> np.ndarray:
    """Posterior-weighted I(S;Y|action) for a binary next-stop observation.

    action_member_hits has shape [action, source, member].  The frozen
    Jeffreys finite-member predictive probability is used for every source and
    action.  Scores are in nats and require no localization truth.
    """
    q = _normalized_prior(posterior)
    events = np.asarray(action_member_hits)
    if events.ndim != 3 or events.shape[1] != q.size or events.shape[2] < 1:
        raise ValueError("CTPI_ACTION_EVENT_SHAPE")
    if events.dtype != np.bool_:
        if not np.all((events == 0) | (events == 1)):
            raise ValueError("CTPI_ACTION_EVENT_BINARY")
        events = events.astype(np.bool_)
    member_count = events.shape[2]
    p_hit = (np.sum(events, axis=2, dtype=np.float64) + 0.5) / float(member_count + 1)
    mixture = p_hit @ q
    conditional = binary_entropy(p_hit) @ q
    score = binary_entropy(mixture) - conditional
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("CTPI_ACTION_INFORMATION_INVALID")
    return np.maximum(score, 0.0)


def choose_information_action(
    posterior: np.ndarray,
    action_member_hits: np.ndarray,
    feasible: np.ndarray,
    travel_cost: np.ndarray,
) -> tuple[int, np.ndarray]:
    """Lexicographic M3 choice: information first, then shortest travel cost."""
    score = action_information_scores(posterior, action_member_hits)
    allowed = np.asarray(feasible, dtype=np.bool_)
    cost = np.asarray(travel_cost, dtype=np.float64)
    if allowed.shape != score.shape or cost.shape != score.shape or not np.any(allowed):
        raise ValueError("CTPI_ACTION_FEASIBILITY")
    if np.any(cost < 0.0) or not np.isfinite(cost).all():
        raise ValueError("CTPI_ACTION_COST")
    best_score = float(np.max(score[allowed]))
    tied = allowed & (np.abs(score - best_score) <= PAIR_TOL)
    best_cost = float(np.min(cost[tied]))
    finalists = np.flatnonzero(tied & (np.abs(cost - best_cost) <= PAIR_TOL))
    return int(finalists[0]), score


def selftest() -> None:
    prior = np.asarray([0.5, 0.5])
    # Identical F00 means, different complete count laws.
    counts = np.asarray([[0, 0, 2, 2], [1, 1, 1, 1]], dtype=np.int64)
    f00 = f00_posterior(prior, counts, observed_hit_count=1, stop_count=2)
    full = full_law_posterior(prior, counts, observed_hit_count=1, stop_count=2)
    np.testing.assert_allclose(f00, np.asarray([0.5, 0.5]), atol=1e-15)
    assert full[1] > full[0]

    member_perm = np.asarray([2, 0, 3, 1])
    np.testing.assert_allclose(
        full_law_posterior(prior, counts[:, member_perm], 1, 2), full, atol=1e-15
    )
    source_perm = np.asarray([1, 0])
    np.testing.assert_allclose(
        full_law_posterior(prior[source_perm], counts[source_perm], 1, 2),
        full[source_perm], atol=1e-15,
    )

    # Action 0 is source-indistinguishable; action 1 separates both sources.
    action_events = np.asarray([
        [[0, 1, 0, 1], [1, 0, 1, 0]],
        [[0, 0, 0, 0], [1, 1, 1, 1]],
    ], dtype=np.bool_)
    choice, score = choose_information_action(
        prior, action_events, np.asarray([True, True]), np.asarray([1.0, 2.0])
    )
    assert choice == 1 and score[1] > score[0] + 1e-12
    assert abs(float(np.sum(full)) - 1.0) <= 1e-15
    print("CTPI_CLOSED_LOOP_CORE_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if not args.selftest:
        parser.error("run --selftest")
    selftest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
