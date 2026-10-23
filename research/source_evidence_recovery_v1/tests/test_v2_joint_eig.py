"""Full-observation EIG baselines, support accounting, and legal-history tests."""

import math

import numpy as np
import pytest

from gsl_recovery.m3_planner.joint_eig import full_observation_eig
from gsl_recovery.m3_planner.planner import joint_eig
from gsl_recovery.m3_codebook.codebook import SoftCodebook
from gsl_recovery.types import Action, Mechanism, Observation


SOURCES = [np.array([0.0, 0.0]), np.array([1.0, 0.0])]
MECHANISMS = [Mechanism()]


def exact_binary_information(probabilities, prior=(0.5, 0.5)):
    p = np.asarray(probabilities, float)
    laws = np.stack((1-p, p), axis=1)
    weights = np.asarray(prior, float)
    predictive = weights @ laws
    return float(np.sum(weights[:, None] * laws * np.log(laws / predictive[None, :])))


class BinaryGenerator:
    """Normalized finite law: deterministic zero wind and Bernoulli gas."""

    def __init__(self, probabilities, expected_history=None):
        self.probabilities = np.atleast_2d(np.asarray(probabilities, float))
        self.calls = []
        self.sampled = []
        self.expected_history = None if expected_history is None else tuple(expected_history)

    def _p(self, source, mechanism):
        return self.probabilities[int(source[0]), int(mechanism.magnitude)]

    def log_prob(self, history, source, mechanism):
        self.calls.append((int(source[0]), int(mechanism.magnitude), len(history)))
        p = self._p(source, mechanism)
        total = 0.0
        for observation in history:
            if tuple(observation.wind) != (0.0, 0.0):
                return -np.inf
            total += math.log(p if observation.gas else 1-p)
        return total

    def sample_future(self, history, actions, source, mechanism, rng):
        if self.expected_history is not None:
            assert tuple(history) == self.expected_history
        self.sampled.append((int(source[0]), int(mechanism.magnitude), len(history)))
        p = self._p(source, mechanism)
        return [Observation(f"generated_{i}", action, (0.0, 0.0), float(rng.random() < p))
                for i, action in enumerate(actions)]


class WindInformationGenerator:
    """Same gas law for every source; a wind observation distinguishes sources."""

    def log_prob(self, history, source, mechanism):
        p = 0.95 if source[0] == 0 else 0.05
        result = 0.0
        for o in history:
            if o.wind[0] not in (-1.0, 1.0) or o.wind[1] != 0.0:
                return -np.inf
            result += math.log(p if o.wind[0] > 0 else 1-p) + math.log(0.5)
        return result

    def sample_future(self, history, actions, source, mechanism, rng):
        p = 0.95 if source[0] == 0 else 0.05
        return [Observation(f"generated_{i}", a,
                            (1.0 if rng.random() < p else -1.0, 0.0),
                            float(rng.random() < 0.5)) for i, a in enumerate(actions)]


def test_full_eig_matches_exact_bernoulli_information_with_mc_error():
    model = BinaryGenerator([[0.8], [0.2]])
    result = full_observation_eig(model, [], [Action(0, 0)], SOURCES, MECHANISMS,
                                  [0.5, 0.5], [[1], [1]], draws=4000,
                                  rng=np.random.default_rng(200))
    expected = exact_binary_information([0.8, 0.2])
    assert abs(result["eig"] - expected) <= 4*result["standard_error"] + 1e-5
    assert result["log_prob_evaluations"] == 2*(4000+1)
    assert result["sample_calls"] == 4000
    assert result["evaluated_source_count"] == 2


def test_wind_can_supply_information_that_gas_word_eig_discards():
    action = Action(0, 0)
    gas_book = SoftCodebook((action,), np.array([[[0.5, 0.5]], [[0.5, 0.5]]]), exact=True)
    assert joint_eig(gas_book, [0.5, 0.5]) == pytest.approx(0.0)
    result = full_observation_eig(WindInformationGenerator(), [], [action], SOURCES,
                                  MECHANISMS, [0.5, 0.5], draws=3000,
                                  rng=np.random.default_rng(201))
    expected = exact_binary_information([0.95, 0.05])
    assert result["eig"] > 0.4
    assert abs(result["eig"] - expected) < 4*result["standard_error"] + 1e-5


def test_mechanism_is_integrated_before_source_information_ratio():
    mechanisms = [Mechanism(magnitude=0), Mechanism(magnitude=1)]
    model = BinaryGenerator([[0.05, 0.95], [0.05, 0.95]])
    result = full_observation_eig(model, [], [Action(0, 0)], SOURCES, mechanisms,
                                  [0.5, 0.5], [[0.5, 0.5], [0.5, 0.5]],
                                  draws=100, rng=np.random.default_rng(202))
    # Observation reveals mechanism but carries no source information.
    assert result["eig"] == pytest.approx(0.0, abs=1e-12)
    assert result["log_prob_evaluations"] == 4*101


def test_prefix_is_preserved_and_subtracted_once_for_each_hypothesis():
    history = [
        Observation("ACTUAL_PAST_0", Action(0, 0, time=0), (0.0, 0.0), 0),
        Observation("ACTUAL_PAST_1", Action(1, 0, time=1), (0.0, 0.0), 0),
    ]
    model = BinaryGenerator([[0.8], [0.2]], expected_history=history)
    result = full_observation_eig(model, history, [Action(2, 0, time=2)], SOURCES,
                                  MECHANISMS, [0.5, 0.5], draws=3000,
                                  rng=np.random.default_rng(203))
    expected = exact_binary_information([0.8, 0.2])
    assert abs(result["eig"] - expected) <= 4*result["standard_error"] + 1e-5
    assert len(history) == 2
    assert sum(length == 2 for _, _, length in model.calls) == 2
    assert all(length in (2, 3) for _, _, length in model.calls)
    assert all(length == 2 for _, _, length in model.sampled)


def test_zero_weight_candidates_are_evaluated_but_not_sampled():
    model = BinaryGenerator([[0.8], [0.2]])
    result = full_observation_eig(model, [], [Action(0, 0)], SOURCES, MECHANISMS,
                                  [1.0, 0.0], draws=10, rng=np.random.default_rng(204))
    assert result["eig"] == pytest.approx(0.0, abs=1e-12)
    assert result["source_sampling_counts"] == [10, 0]
    assert sum(i == 1 for i, _, _ in model.calls) == 11


def test_call_budget_blocks_before_sampling_or_support_pruning():
    model = BinaryGenerator([[0.8], [0.2]])
    with pytest.raises(RuntimeError, match="BLOCKED_FULL_OBSERVATION_EIG_BUDGET"):
        full_observation_eig(model, [], [Action(0, 0)], SOURCES, MECHANISMS,
                              [0.5, 0.5], draws=10, max_eval=21)
    assert model.calls == []
    assert model.sampled == []


def test_finite_mc_estimates_are_not_clipped_to_nonnegative():
    # One legal rare Monte Carlo realization can have negative sample mean.
    values = []
    for seed in range(30):
        result = full_observation_eig(BinaryGenerator([[0.8], [0.2]]), [],
                                      [Action(0, 0)], SOURCES, MECHANISMS,
                                      [0.5, 0.5], draws=2, rng=np.random.default_rng(seed))
        values.append(result["eig"])
    assert min(values) < 0


def test_new_module_does_not_shadow_legacy_package_function():
    import gsl_recovery.m3_planner as package
    assert callable(package.joint_eig)
    assert package.joint_eig is joint_eig
