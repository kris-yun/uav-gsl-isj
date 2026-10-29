#!/usr/bin/env python3
"""Exact finite certificates for V59 theoretical qualifications.

These are deliberately synthetic probability models, not plume simulations,
native V49/V57 replays, or evidence of biological-controller superiority.
The root agent owns the separate adaptive wind/gas policy-tree experiment.
Only Python's standard library is required. All logarithms are natural.
"""
from __future__ import annotations

import itertools
import json
import math
import random
from collections import defaultdict
from pathlib import Path


def entropy(probabilities):
    return -sum(p * math.log(p) for p in probabilities if p > 0)


def mutual_information(joint):
    """joint maps (target_label, observation_label) to joint mass."""
    px, py = defaultdict(float), defaultdict(float)
    for (x, y), mass in joint.items():
        px[x] += mass
        py[y] += mass
    return sum(
        mass * math.log(mass / (px[x] * py[y]))
        for (x, y), mass in joint.items() if mass > 0
    )


def deterministic_information(states, mass, target, observation):
    joint = defaultdict(float)
    for state, p in zip(states, mass):
        joint[(target(state), observation(state))] += p
    return mutual_information(joint)


def binary_entropy(p):
    return entropy([p, 1 - p])


def symmetric_actions():
    values = {}
    for name, error, reflected in [
        ("left", 0.1, False), ("right", 0.1, True), ("stay", 0.5, False)
    ]:
        joint = defaultdict(float)
        for s, y in itertools.product(range(2), repeat=2):
            expected = 1 - s if reflected else s
            joint[s, y] = 0.5 * (1 - error if y == expected else error)
        values[name] = mutual_information(joint)
    assert abs(values["left"] - values["right"]) < 1e-12
    assert values["left"] > 0 and abs(values["stay"]) < 1e-12
    return {
        "source_entropy_nat": math.log(2),
        "source_MI_nat": values,
        "claim": "Mirror symmetry permits equal positive EIG; it does not imply zero EIG.",
    }


def efe_identity(seed=190729, repetitions=256):
    rng = random.Random(seed)
    max_source_error = max_full_error = max_uniform_error = 0.0
    states = list(itertools.product(range(3), range(2), range(2)))
    for _ in range(repetitions):
        # A generic current joint posterior can be correlated after history.
        raw = [rng.random() + 0.03 for _ in states]
        belief = [x / sum(raw) for x in raw]
        channels = []
        for _state in states:
            raw_y = [rng.random() + 0.03 for _ in range(4)]
            channels.append([x / sum(raw_y) for x in raw_y])
        pref_raw = [rng.random() + 0.03 for _ in range(4)]
        pref = [x / sum(pref_raw) for x in pref_raw]
        sy = defaultdict(float)
        full_y = defaultdict(float)
        py = [0.0] * 4
        ps = [0.0] * 3
        for idx, (state, mass, channel) in enumerate(zip(states, belief, channels)):
            s = state[0]
            ps[s] += mass
            for y, likelihood in enumerate(channel):
                sy[s, y] += mass * likelihood
                full_y[idx, y] += mass * likelihood
                py[y] += mass * likelihood
        source_mi = mutual_information(sy)
        full_mi = mutual_information(full_y)
        risk = sum(py[y] * math.log(py[y] / pref[y]) for y in range(4))
        # Source ambiguity marginalizes W,Q under b(W,Q|S), rather than
        # pretending these nuisances have been observed.
        source_ambiguity = sum(
            ps[s] * entropy([sy[s, y] / ps[s] for y in range(4)])
            for s in range(3)
        )
        full_ambiguity = sum(b * entropy(ch) for b, ch in zip(belief, channels))
        preference_cost = -sum(py[y] * math.log(pref[y]) for y in range(4))
        max_source_error = max(
            max_source_error, abs(risk + source_ambiguity + source_mi - preference_cost)
        )
        max_full_error = max(
            max_full_error, abs(risk + full_ambiguity + full_mi - preference_cost)
        )
        uniform_risk = sum(p * math.log(4 * p) for p in py)
        max_uniform_error = max(
            max_uniform_error, abs(uniform_risk + source_ambiguity + source_mi - math.log(4))
        )
    assert max(max_source_error, max_full_error, max_uniform_error) < 1e-12
    return {
        "seed": seed, "finite_joint_models": repetitions,
        "max_source_EFE_identity_error": max_source_error,
        "max_full_latent_EFE_identity_error": max_full_error,
        "max_uniform_preference_EFE_plus_MI_minus_constant_error": max_uniform_error,
        "claim": "Exact risk+ambiguity equals preference cross entropy minus the MI for the specified latent target.",
    }


def nuisance_target_mismatch():
    states = list(itertools.product(range(2), range(2), range(4)))
    mass = [1 / len(states)] * len(states)
    actions = {"source_measurement": lambda t: t[0], "release_measurement": lambda t: t[2]}
    result = {}
    for name, obs in actions.items():
        result[name] = {
            "source_MI_nat": deterministic_information(states, mass, lambda t: t[0], obs),
            "all_latent_MI_nat": deterministic_information(states, mass, lambda t: t, obs),
        }
    assert result["release_measurement"]["source_MI_nat"] == 0
    assert result["release_measurement"]["all_latent_MI_nat"] > result["source_measurement"]["all_latent_MI_nat"]
    return {
        "prior": "S~Bernoulli(1/2), W~Bernoulli(1/2), Q~Uniform({0,1,2,3}), mutually independent",
        "equal_cost_one_step_actions": result,
        "source_target_choice": "source_measurement",
        "all_latent_target_choice": "release_measurement",
        "claim": "The all-latent objective can strictly prefer information unrelated to source location.",
    }


def nonidentifiability_and_synergy():
    states = list(itertools.product(range(2), range(2), range(2)))
    mass = [1 / len(states)] * len(states)
    source = lambda t: t[0]
    masked = lambda t: t[0] ^ t[1]
    wind = lambda t: t[1]
    source_masked = deterministic_information(states, mass, source, masked)
    source_wind = deterministic_information(states, mass, source, wind)
    source_joint = deterministic_information(states, mass, source, lambda t: (wind(t), masked(t)))
    # An exhaustive depth-3 deterministic policy family with two actions.
    # A0 returns X=S XOR W; A1 returns X XOR Q. Every possible transcript
    # depends only on (X,Q), which is independent of S under this prior.
    def transcript(state, policy):
        node, tr = 0, []
        x, q = masked(state), state[2]
        for _ in range(3):
            action = policy[node]
            y = x if action == 0 else x ^ q
            tr.append((action, y))
            node = 2 * node + 1 + y
        return tuple(tr)
    mis = []
    for policy in itertools.product(range(2), repeat=7):
        mis.append(deterministic_information(states, mass, source, lambda t: transcript(t, policy)))
    max_mi = max(mis)
    assert abs(source_masked) < 1e-12 and abs(source_wind) < 1e-12
    assert abs(source_joint - math.log(2)) < 1e-12
    assert abs(max_mi) < 1e-12
    return {
        "masked_gas_source_MI_nat": source_masked,
        "wind_source_MI_nat": source_wind,
        "joint_wind_masked_gas_source_MI_nat": source_joint,
        "wrongly_conditioning_on_known_wind_MI_nat": math.log(2),
        "nonidentifiable_policy_family_depth": 3,
        "nonidentifiable_policy_trees_exhaustively_evaluated": len(mis),
        "maximum_source_MI_in_nonidentifiable_family_nat": max_mi,
        "claim": "Complementary observations may be informative jointly; an unidentifiable legal channel family remains uninformative under every adaptive policy.",
    }


def proposal_coverage_and_scoring():
    values = [0.0, 0.1, 0.2, math.log(2) - 0.06, math.log(2)]
    best, count, k = max(values), len(values), 4
    proposals = {
        "uniform_illustration": [0.2] * count,
        "focused_illustration": [0.125] * 4 + [0.5],
    }
    coverage = {}
    for name, q in proposals.items():
        regret = miss = 0.0
        for drawn in itertools.product(range(count), repeat=k):
            probability = math.prod(q[i] for i in drawn)
            regret += probability * (best - max(values[i] for i in drawn))
            if count - 1 not in drawn:
                miss += probability
        bound = (1 - q[-1]) ** k * (best - min(values))
        assert regret <= bound + 1e-12
        assert abs(miss - (1 - q[-1]) ** k) < 1e-12
        coverage[name] = {
            "assumed_optimal_policy_probability_per_draw": q[-1],
            "draws": k, "exact_miss_probability": miss,
            "exact_expected_restriction_regret_nat": regret,
            "coverage_regret_upper_bound_nat": bound,
        }
    epsilon, verified, max_excess = 0.03, 0, -math.inf
    for inclusion in itertools.product([False, True], repeat=count):
        indices = [i for i, keep in enumerate(inclusion) if keep]
        if not indices:
            continue
        restriction_gap = best - max(values[i] for i in indices)
        for signs in itertools.product([-1, 1], repeat=count):
            scores = [value + sign * epsilon for value, sign in zip(values, signs)]
            selected = max(indices, key=lambda i: scores[i])
            regret = best - values[selected]
            bound = restriction_gap + 2 * epsilon
            max_excess = max(max_excess, regret - bound)
            assert regret <= bound + 1e-12
            verified += 1
    return {
        "coverage_illustrations": coverage,
        "uniform_score_error_bound_nat": epsilon,
        "subsets_and_extreme_score_error_cases": verified,
        "maximum_regret_minus_bound_nat": max_excess,
        "claim": "Coverage and score-error bounds are conditional mathematical qualifications, not measured biological-proposal performance.",
    }


def resetting_and_coverage():
    # Poisson restart with instantaneous reset and iid renewal attempts:
    # E[T_r]=(1-L_T(r))/(r L_T(r)). No reset-time or flight overhead.
    rates = [0.1, 1.0, 2.0]
    deterministic = {str(r): math.expm1(r) / r for r in rates}
    exponential = {str(r): (1 - 1 / (1 + r)) / (r / (1 + r)) for r in rates}
    mix_rate = 0.2
    laplace = 0.5 * 0.2 / (0.2 + mix_rate) + 0.5 * 2.0 / (2.0 + mix_rate)
    mixture_reset_mean = (1 - laplace) / (mix_rate * laplace)
    mixture_original_mean = 0.5 / 0.2 + 0.5 / 2.0
    assert all(t > 1 for t in deterministic.values())
    assert all(abs(t - 1) < 1e-12 for t in exponential.values())
    assert mixture_reset_mean < mixture_original_mean
    states = list(itertools.product(range(2), repeat=2))
    mass = [0.25] * 4
    # Exact occupation of a two-site discrete target density, with a
    # source-independent masked measurement at both visited sites.
    tr = lambda t: (t[0] ^ t[1], t[0] ^ t[1])
    source_mi = deterministic_information(states, mass, lambda t: t[0], tr)
    assert abs(source_mi) < 1e-12
    return {
        "deterministic_T_equal_1_reset_means": deterministic,
        "exponential_T_mean_1_reset_means": exponential,
        "hyperexponential_original_mean": mixture_original_mean,
        "hyperexponential_restart_rate": mix_rate,
        "hyperexponential_reset_mean": mixture_reset_mean,
        "two_site_exact_occupation_error": 0.0,
        "two_site_total_source_MI_nat": source_mi,
        "claim": "Restart can help, hurt, or have no effect; occupation matching alone cannot ensure source identification.",
    }


def main():
    result = {
        "status": "PASS: exact finite certificates; no native plume/controller evidence claimed",
        "units": "nats, except abstract restart times/rates",
        "symmetric_actions": symmetric_actions(),
        "EFE_identity": efe_identity(),
        "nuisance_target_mismatch": nuisance_target_mismatch(),
        "nonidentifiability_and_synergy": nonidentifiability_and_synergy(),
        "proposal_coverage_and_scoring": proposal_coverage_and_scoring(),
        "resetting_and_coverage": resetting_and_coverage(),
    }
    target = Path(__file__).with_name("finite_certificates_results.json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
