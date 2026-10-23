"""Cost-aware source challenges with a paid, posterior-independent floor.

The cost-ratio LP follows nonhomogeneous-cost active hypothesis testing.
The challenger escape and persistent coverage mixture are explicit engineering
choices, not an implementation of a finite-sample theorem from that paper.
KL values refer to the installed predictive channel, not an unknown world.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog
from scipy.special import rel_entr


@dataclass(frozen=True)
class Allocation:
    probabilities: np.ndarray
    resource_fractions: np.ndarray
    observations_per_cost: np.ndarray
    value: float
    expected_cost: float
    status: str


@dataclass(frozen=True)
class PlanResult:
    probabilities: np.ndarray
    action: int | None
    info: dict[str, Any]


def _distribution(values, shape, name):
    p = np.asarray(values, dtype=float)
    if p.shape != shape or not np.isfinite(p).all() or np.any(p < 0):
        raise ValueError(f"{name} must be a finite nonnegative array of shape {shape}")
    if not np.allclose(p.sum(axis=-1), 1.0, atol=1e-9, rtol=0):
        raise ValueError(f"{name} distributions must sum to one")
    return p


def pairwise_kl(predictives: np.ndarray) -> np.ndarray:
    """Return exact installed-model KL with axes [action, source, opponent].

    Zero probabilities are not clipped: a support mismatch can give infinity.
    The planner reports that case and uses a pair challenge instead of feeding
    infinity to a linear-program solver.
    """
    p = np.asarray(predictives, dtype=float)
    if p.ndim != 3 or p.shape[1] < 2 or p.shape[2] < 2:
        raise ValueError("predictives must have axes [action,source,outcome]")
    _distribution(p, p.shape, "predictives")
    divergence = rel_entr(p[:, :, None, :], p[:, None, :, :]).sum(axis=-1)
    return np.maximum(divergence, 0.0)


def cost_aware_allocation(divergences: np.ndarray, costs: np.ndarray) -> Allocation:
    """Maximize min_j E[D_j(A)] / E[c(A)] for finite divergences.

    The solver variable z is a *resource fraction*.  The equivalent original
    variable is y=z/c, with c.T@y=1.  Sampling frequencies are y/sum(y), never z.
    Scaling the constraint coefficients avoids treating weak positive KL as
    zero merely because it is below a linear solver's absolute tolerance.
    """
    d = np.asarray(divergences, dtype=float)
    c = np.asarray(costs, dtype=float)
    if d.ndim != 2 or min(d.shape) < 1:
        raise ValueError("divergences must have axes [action,opponent]")
    if c.shape != (d.shape[0],) or not np.isfinite(c).all() or np.any(c <= 0):
        raise ValueError("costs must be positive and finite")
    if not np.isfinite(d).all() or np.any(d < 0):
        raise ValueError("the LP requires finite nonnegative divergences")
    rates = d / c[:, None]
    scale = float(rates.max())
    if scale == 0:
        probabilities = np.full(len(c), 1.0 / len(c))
        expected_cost = float(probabilities @ c)
        y = probabilities / expected_cost
        return Allocation(probabilities, c * y, y, 0.0, expected_cost, "all_zero")
    scaled_rates = rates / scale
    a = len(c)
    result = linprog(
        np.r_[np.zeros(a), -1.0],
        A_ub=np.column_stack((-scaled_rates.T, np.ones(d.shape[1]))),
        b_ub=np.zeros(d.shape[1]),
        A_eq=np.array([np.r_[np.ones(a), 0.0]]),
        b_eq=np.array([1.0]),
        bounds=[(0.0, None)] * (a + 1),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"cost allocation LP failed: {result.message}")
    z = np.maximum(result.x[:a], 0.0)
    z /= z.sum()
    y = z / c
    probabilities = y / y.sum()
    expected_cost = float(probabilities @ c)
    # Recompute the achieved objective rather than trusting an auxiliary LP v.
    value = float(np.min(probabilities @ d) / expected_cost)
    return Allocation(probabilities, z, y, value, expected_cost, "optimal")


class CoveragePlanner:
    """Complete legal-source planning with an explicit challenge escape.

    ``source_posterior`` selects only the incumbent. It never prunes sources,
    weights pair KL, scales the exploration floor, or triggers termination.
    ``coverage`` is fixed before this call and must not be derived from the
    current posterior. Uniform coverage is the default. With ``rng=None`` the
    caller samples ``PlanResult.probabilities``; supplying an RNG also returns
    a sampled action and its mixture-component label.
    """

    def __init__(
        self,
        epsilon: float = 0.2,
        coverage: np.ndarray | None = None,
        challenger: int | None = None,
        rng: np.random.Generator | None = None,
        zero_tolerance: float = 1e-12,
    ):
        if not np.isfinite(epsilon) or not 0 <= epsilon <= 1:
            raise ValueError("epsilon must be in [0,1]; zero is a no-coverage ablation")
        if not np.isfinite(zero_tolerance) or zero_tolerance < 0:
            raise ValueError("zero_tolerance must be finite and nonnegative")
        self.epsilon = float(epsilon)
        self.coverage = None if coverage is None else np.asarray(coverage, dtype=float).copy()
        self.challenger = challenger
        self.rng = rng
        self.zero_tolerance = float(zero_tolerance)

    def plan(self, channel, predictives, source_posterior, step, *, challenger=None, exploit_mask=None) -> PlanResult:
        a, s, _, o = channel.probabilities.shape
        p = _distribution(predictives, (a, s, o), "predictives")
        posterior = _distribution(source_posterior, (s,), "source_posterior")
        costs = np.asarray(channel.costs, dtype=float)
        if costs.shape != (a,) or not np.isfinite(costs).all() or np.any(costs <= 0):
            raise ValueError("every action must have a positive finite full cost")
        if not isinstance(step, (int, np.integer)) or isinstance(step, (bool, np.bool_)) or step < 0:
            raise ValueError("step must be a nonnegative integer")
        nu = np.full(a, 1.0 / a) if self.coverage is None else _distribution(self.coverage, (a,), "coverage").copy()
        mask = np.ones(a, dtype=bool) if exploit_mask is None else np.asarray(exploit_mask)
        if mask.shape != (a,) or mask.dtype.kind != "b":
            raise ValueError("exploit_mask must be a boolean vector with one entry per action")
        incumbent = int(np.argmax(posterior))
        opponents = [j for j in range(s) if j != incumbent]
        selected_challenger = self.challenger if challenger is None else challenger
        explicit = selected_challenger is not None
        if explicit:
            if not isinstance(selected_challenger, (int, np.integer)) or isinstance(selected_challenger, (bool, np.bool_)):
                raise ValueError("challenger must be a source index")
            selected_challenger = int(selected_challenger)
            if selected_challenger not in opponents:
                raise ValueError("challenger must be a legal source different from the incumbent")

        kl = pairwise_kl(p)
        d = kl[:, incumbent, opponents]
        zero_pairs = [
            [i, j] for i in range(s) for j in range(i + 1, s)
            if np.all(kl[:, i, j] <= self.zero_tolerance)
            and np.all(kl[:, j, i] <= self.zero_tolerance)
        ]
        allocation = None
        lp_status = "empty_exploit_mask" if not mask.any() else "support_singular"
        if mask.any() and np.isfinite(d[mask]).all():
            local_allocation = cost_aware_allocation(d[mask], costs[mask])
            full_probabilities = np.zeros(a)
            full_resource = np.zeros(a)
            full_rates = np.zeros(a)
            full_probabilities[mask] = local_allocation.probabilities
            full_resource[mask] = local_allocation.resource_fractions
            full_rates[mask] = local_allocation.observations_per_cost
            allocation = Allocation(
                full_probabilities, full_resource, full_rates,
                local_allocation.value, local_allocation.expected_cost, local_allocation.status,
            )
            lp_status = allocation.status
        positive_lp = allocation is not None and allocation.value > self.zero_tolerance
        reason = "full_cost_maxmin"
        exploitation = None
        challenge_scores = None

        if positive_lp and not explicit:
            exploitation = allocation.probabilities.copy()
        else:
            if not explicit:
                useful = [
                    j for j in opponents
                    if np.any(np.minimum(kl[:, incumbent, j], kl[:, j, incumbent]) / costs > self.zero_tolerance)
                ]
                rotation = useful if useful else opponents
                selected_challenger = rotation[int(step) % len(rotation)]
            challenge_scores = np.minimum(
                kl[:, incumbent, selected_challenger], kl[:, selected_challenger, incumbent]
            ) / costs
            best = float(np.max(challenge_scores))
            if best > self.zero_tolerance:
                if np.isinf(best):
                    tied = np.flatnonzero(np.isinf(challenge_scores))
                else:
                    tied = np.flatnonzero(np.isclose(challenge_scores, best, rtol=1e-10, atol=0.0))
                chosen = int(tied[np.argmin(costs[tied])])
                exploitation = np.zeros(a)
                exploitation[chosen] = 1.0
                reason = "explicit_challenge" if explicit else (
                    lp_status + "_challenge" if allocation is None else "zero_maxmin_challenge"
                )
                if not mask[chosen]:
                    reason = "tube_escape_challenge"
            else:
                exploitation = nu.copy()
                reason = "indistinguishable_pair_coverage"

        probabilities = (1.0 - self.epsilon) * exploitation + self.epsilon * nu
        expected_cost = float(probabilities @ costs)
        positive_actions = probabilities > 0
        achieved_pair_rates = (probabilities[positive_actions] @ d[positive_actions]) / expected_cost
        sampled_action = None
        coverage_draw = None
        if self.rng is not None:
            coverage_draw = bool(self.rng.random() < self.epsilon)
            draw_distribution = nu if coverage_draw else exploitation
            sampled_action = int(self.rng.choice(a, p=draw_distribution))
        info = {
            "reason": reason,
            "incumbent": incumbent,
            "challenger": selected_challenger,
            "legal_sources": list(range(s)),
            "lp_opponents": opponents,
            "lp_status": lp_status,
            "lp_action_mask": mask.tolist(),
            "escaped_exploit_mask": bool(np.any(exploitation[~mask] > 0)),
            "lp_value_per_cost": None if allocation is None else allocation.value,
            "lp_resource_fractions": None if allocation is None else allocation.resource_fractions.tolist(),
            "exploitation_probabilities": exploitation.tolist(),
            "coverage_probabilities": nu.tolist(),
            "coverage_probability_floor": (self.epsilon * nu).tolist(),
            "coverage_fraction_of_draws": self.epsilon,
            "coverage_expected_cost_per_step": float(self.epsilon * (nu @ costs)),
            "expected_total_cost_per_step": expected_cost,
            "coverage_draw": coverage_draw,
            "pairwise_kl": kl.tolist(),
            "zero_pairs": zero_pairs,
            "challenge_score_per_cost": None if challenge_scores is None else challenge_scores.tolist(),
            "achieved_incumbent_pair_rates": achieved_pair_rates.tolist(),
            "planning_law": "installed predictive model; not a calibrated real-world KL bound",
            "no_automatic_stopping": True,
        }
        return PlanResult(probabilities.copy(), sampled_action, info)
