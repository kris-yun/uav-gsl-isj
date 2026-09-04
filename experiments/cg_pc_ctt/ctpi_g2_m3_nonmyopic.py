#!/usr/bin/env python3
"""Auditable Bayesian design operators for CTPI-G2 M3.

This module deliberately consumes an already-frozen Bernoulli observation law
``P(Y=1 | source carrier, action, history)``.  It does not turn a deterministic
concentration prediction into a likelihood, fit a sensor model, or alter M1/M2.

Array convention throughout is ``[action, source]``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


PAIR_TOL = 1.0e-12


def normalized_posterior(value: np.ndarray) -> np.ndarray:
    posterior = np.asarray(value, dtype=np.float64)
    if posterior.ndim != 1 or posterior.size < 2:
        raise ValueError("CTPI_G2_M3_POSTERIOR_SHAPE")
    if np.any(posterior < 0.0) or not np.isfinite(posterior).all():
        raise ValueError("CTPI_G2_M3_POSTERIOR_VALUE")
    mass = float(np.sum(posterior))
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("CTPI_G2_M3_POSTERIOR_MASS")
    return posterior / mass


def bernoulli_likelihood(value: np.ndarray, source_count: int | None = None) -> np.ndarray:
    likelihood = np.asarray(value, dtype=np.float64)
    if likelihood.ndim != 2 or likelihood.shape[0] < 1 or likelihood.shape[1] < 2:
        raise ValueError("CTPI_G2_M3_LIKELIHOOD_SHAPE")
    if source_count is not None and likelihood.shape[1] != int(source_count):
        raise ValueError("CTPI_G2_M3_LIKELIHOOD_SOURCE_COUNT")
    if np.any((likelihood < 0.0) | (likelihood > 1.0)) or not np.isfinite(likelihood).all():
        raise ValueError("CTPI_G2_M3_LIKELIHOOD_VALUE")
    return likelihood


def entropy(posterior: np.ndarray) -> float:
    p = normalized_posterior(posterior)
    positive = p > 0.0
    return float(-np.sum(p[positive] * np.log(p[positive])))


def binary_entropy(probability: np.ndarray | float) -> np.ndarray:
    p = np.asarray(probability, dtype=np.float64)
    if np.any((p < 0.0) | (p > 1.0)) or not np.isfinite(p).all():
        raise ValueError("CTPI_G2_M3_BINARY_ENTROPY_INPUT")
    result = np.zeros_like(p)
    interior = (p > 0.0) & (p < 1.0)
    result[interior] = -(
        p[interior] * np.log(p[interior])
        + (1.0 - p[interior]) * np.log1p(-p[interior])
    )
    return result


@dataclass(frozen=True)
class BinaryBranches:
    probability: np.ndarray  # [observation], ordered y=0, y=1
    posterior: np.ndarray  # [observation, action, source]


def posterior_branches(posterior: np.ndarray, likelihood_y1: np.ndarray) -> BinaryBranches:
    """Return exact ``y=0`` and ``y=1`` posterior branches for every action.

    A zero-probability branch is represented by the unchanged prior.  Its value
    is irrelevant because the corresponding predictive probability is exactly
    zero, while this convention keeps every returned array finite and auditable.
    """
    pi = normalized_posterior(posterior)
    q1 = bernoulli_likelihood(likelihood_y1, pi.size)
    q = np.stack([1.0 - q1, q1], axis=0)
    probability = np.einsum("yas,s->ya", q, pi)
    branches = np.empty_like(q)
    for y in range(2):
        numerator = q[y] * pi[None, :]
        positive = probability[y] > 0.0
        branches[y, positive] = numerator[positive] / probability[y, positive, None]
        branches[y, ~positive] = pi
    if not np.isfinite(branches).all():
        raise RuntimeError("CTPI_G2_M3_BRANCH_NONFINITE")
    np.testing.assert_allclose(np.sum(branches, axis=2), 1.0, atol=PAIR_TOL, rtol=0.0)
    return BinaryBranches(probability=probability, posterior=branches)


def myopic_eid(posterior: np.ndarray, likelihood_y1: np.ndarray) -> np.ndarray:
    """Exact one-step ``I(S;Y_a)`` in nats for all actions."""
    pi = normalized_posterior(posterior)
    q1 = bernoulli_likelihood(likelihood_y1, pi.size)
    mixture = q1 @ pi
    score = binary_entropy(mixture) - binary_entropy(q1) @ pi
    if np.any(score < -PAIR_TOL) or not np.isfinite(score).all():
        raise RuntimeError("CTPI_G2_M3_MYOPIC_EID_INVALID")
    return np.maximum(score, 0.0)


@dataclass(frozen=True)
class Horizon2Result:
    value: np.ndarray  # [first_action]
    immediate: np.ndarray  # [first_action]
    branch_probability: np.ndarray  # [observation, first_action]
    branch_best_action: np.ndarray  # [observation, first_action]
    branch_best_value: np.ndarray  # [observation, first_action]


def horizon2_eid(
    posterior: np.ndarray,
    likelihood_y1: np.ndarray,
    *,
    first_feasible: np.ndarray | None = None,
    second_feasible: np.ndarray | None = None,
    allow_repeat: bool = False,
) -> Horizon2Result:
    """Exact finite-horizon-two EID with explicit observation branching.

    ``second_feasible`` may be ``[action]`` or ``[first_action, action]``.  The
    latter supports frozen movement/reachability constraints that depend on the
    first action.  No expected-observation posterior is formed anywhere.
    """
    pi = normalized_posterior(posterior)
    q1 = bernoulli_likelihood(likelihood_y1, pi.size)
    action_count = q1.shape[0]
    first = np.ones(action_count, dtype=np.bool_) if first_feasible is None else np.asarray(first_feasible, dtype=np.bool_)
    if first.shape != (action_count,) or not np.any(first):
        raise ValueError("CTPI_G2_M3_FIRST_FEASIBLE")
    if second_feasible is None:
        second = np.ones((action_count, action_count), dtype=np.bool_)
    else:
        supplied = np.asarray(second_feasible, dtype=np.bool_)
        if supplied.shape == (action_count,):
            second = np.broadcast_to(supplied, (action_count, action_count)).copy()
        elif supplied.shape == (action_count, action_count):
            second = supplied.copy()
        else:
            raise ValueError("CTPI_G2_M3_SECOND_FEASIBLE")
    if not allow_repeat:
        np.fill_diagonal(second, False)

    immediate = myopic_eid(pi, q1)
    branches = posterior_branches(pi, q1)
    branch_best_action = np.full((2, action_count), -1, dtype=np.int64)
    branch_best_value = np.zeros((2, action_count), dtype=np.float64)

    for y in range(2):
        for first_action in range(action_count):
            allowed = second[first_action]
            if not np.any(allowed):
                continue
            future = myopic_eid(branches.posterior[y, first_action], q1)
            best_value = float(np.max(future[allowed]))
            finalists = np.flatnonzero(allowed & (np.abs(future - best_value) <= PAIR_TOL))
            branch_best_action[y, first_action] = int(finalists[0])
            branch_best_value[y, first_action] = best_value

    value = immediate + np.sum(branches.probability * branch_best_value, axis=0)
    value[~first] = -np.inf
    if np.any(~np.isfinite(value[first])):
        raise RuntimeError("CTPI_G2_M3_H2_VALUE_INVALID")
    return Horizon2Result(
        value=value,
        immediate=immediate,
        branch_probability=branches.probability,
        branch_best_action=branch_best_action,
        branch_best_value=branch_best_value,
    )


def marginalize_uniform_free_placements(
    placement_action_probability: np.ndarray,
    carrier_placements: Sequence[Sequence[int]],
    free_placement: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute ``P(Y=1|S,a)=sum_u P(Y=1|u,a) P(u|S)``.

    Every free placement listed for a carrier receives equal weight.  Obstacle
    placements are excluded before normalization.  The returned likelihood is
    ``[action, carrier]`` and the audit matrix is ``[carrier, placement]``.
    """
    placement_probability = np.asarray(placement_action_probability, dtype=np.float64)
    if placement_probability.ndim != 2:
        raise ValueError("CTPI_G2_M3_PLACEMENT_ACTION_SHAPE")
    if np.any((placement_probability < 0.0) | (placement_probability > 1.0)) or not np.isfinite(placement_probability).all():
        raise ValueError("CTPI_G2_M3_PLACEMENT_ACTION_VALUE")
    free = np.asarray(free_placement, dtype=np.bool_)
    placement_count, action_count = placement_probability.shape
    if free.shape != (placement_count,):
        raise ValueError("CTPI_G2_M3_FREE_PLACEMENT_SHAPE")

    weights = np.zeros((len(carrier_placements), placement_count), dtype=np.float64)
    for carrier, members in enumerate(carrier_placements):
        indices = np.asarray(list(members), dtype=np.int64)
        if indices.ndim != 1 or indices.size == 0:
            raise ValueError("CTPI_G2_M3_CARRIER_PLACEMENTS_EMPTY")
        if np.any(indices < 0) or np.any(indices >= placement_count):
            raise ValueError("CTPI_G2_M3_CARRIER_PLACEMENT_INDEX")
        if np.unique(indices).size != indices.size:
            raise ValueError("CTPI_G2_M3_CARRIER_PLACEMENT_DUPLICATE")
        eligible = indices[free[indices]]
        if eligible.size == 0:
            raise ValueError("CTPI_G2_M3_CARRIER_NO_FREE_PLACEMENT")
        weights[carrier, eligible] = 1.0 / float(eligible.size)
    np.testing.assert_allclose(np.sum(weights, axis=1), 1.0, atol=PAIR_TOL, rtol=0.0)
    likelihood = placement_probability.T @ weights.T
    return bernoulli_likelihood(likelihood, len(carrier_placements)), weights


def predicted_concentration_exploit_scores(
    posterior: np.ndarray, source_action_concentration: np.ndarray,
) -> np.ndarray:
    """Old offline exploit: ``E[C(a)|pi] = sum_s pi_s C_s(a)``.

    This is neither posterior-MAP navigation nor measured-concentration chase.
    ``source_action_concentration`` uses shape ``[source, action]``.
    """
    pi = normalized_posterior(posterior)
    concentration = np.asarray(source_action_concentration, dtype=np.float64)
    if concentration.shape[0] != pi.size or concentration.ndim != 2:
        raise ValueError("CTPI_G2_M3_EXPLOIT_SHAPE")
    if np.any(concentration < 0.0) or not np.isfinite(concentration).all():
        raise ValueError("CTPI_G2_M3_EXPLOIT_VALUE")
    return pi @ concentration

