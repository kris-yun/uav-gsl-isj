import json

import numpy as np
import pytest

from gsl_recovery.types import Action, Mechanism, Observation
from gsl_recovery.m3_codebook import (
    CorruptionChannel, JointCodebookBuilder, SoftCodebook, encode_word,
)
from gsl_recovery.m3_planner import RobustCounterEvidencePlanner
from gsl_recovery.m3_planner.diagnostics import (
    LAYER_ORDER, diagnose_counterevidence_layers,
)


def _actions(length):
    return tuple(Action(float(i), 0.0, time=float(i + 1)) for i in range(length))


def _delta(word):
    p = np.zeros(2 ** len(word))
    p[encode_word(word)] = 1.0
    return p


class _ScalarCorrelated:
    def sample_future(self, history, actions, source, mechanism, rng):
        # Every trajectory is entirely zero or entirely one: independent
        # per-position sampling would create invalid mixed codewords.
        bit = float(rng.random() < 0.4)
        return [Observation(f"pred_{i}", a, (0.0, 0.0), bit)
                for i, a in enumerate(actions)]


class _BatchCorrelated:
    def __init__(self):
        self.calls = []

    def sample_future(self, *args, **kwargs):
        raise AssertionError("Batch-capable generator must not use scalar rollout")

    def sample_future_batch(self, history, actions, source, mechanism, *, draws, rng):
        self.calls.append((tuple(source), mechanism.kind, draws))
        bits = (rng.random(draws) < 0.4).astype(float)
        return [[Observation(f"pred_{i}", a, (0.0, 0.0), float(bit))
                 for i, a in enumerate(actions)] for bit in bits]


def test_batch_rollout_preserves_joint_law_draws_and_confidence_bound():
    kwargs = dict(history=[], action_blocks=[_actions(3), _actions(2)],
                  sources=[[0, 0], [1, 0]], mechanisms=[Mechanism()],
                  draws=80, delta=0.003)
    batch = _BatchCorrelated()
    actual = JointCodebookBuilder(batch).build(**kwargs, rng=np.random.default_rng(8))
    scalar = JointCodebookBuilder(_ScalarCorrelated()).build(
        **kwargs, rng=np.random.default_rng(8))
    assert len(batch.calls) == 4
    assert all(call[2] == 80 for call in batch.calls)
    for book, expected in zip(actual, scalar):
        assert np.array_equal(book.probabilities, expected.probabilities)
        assert np.array_equal(book.tv_radius, expected.tv_radius)
        assert book.confidence_failure_probability == expected.confidence_failure_probability == 0.003
        assert book.draws == expected.draws == 80
        assert np.all(book.probabilities[..., 1:-1] == 0)


def test_batch_cannot_bypass_source_support_budget():
    generator = _BatchCorrelated()
    with pytest.raises(RuntimeError, match="BLOCKED_CODEBOOK_BUDGET"):
        JointCodebookBuilder(generator).build(
            [], [_actions(3)], [[0, 0], [1, 0]], [Mechanism()],
            draws=100, max_rollout_observations=599)
    assert generator.calls == []


@pytest.mark.parametrize("failure", ["count", "length", "missing"])
def test_malformed_joint_batch_is_rejected(failure):
    class BadBatch(_BatchCorrelated):
        def sample_future_batch(self, history, actions, source, mechanism, *, draws, rng):
            batch = super().sample_future_batch(history, actions, source, mechanism,
                                                draws=draws, rng=rng)
            if failure == "count":
                return batch[:-1]
            if failure == "length":
                batch[0] = batch[0][:-1]
            if failure == "missing":
                batch[0][0] = Observation("missing", actions[0], (0.0, 0.0), np.nan)
            return batch
    with pytest.raises(ValueError, match="future batch|trajectory length|finite available"):
        JointCodebookBuilder(BadBatch()).build(
            [], [_actions(3)], [[0, 0]], [Mechanism()], draws=10)


def test_batch_wall_budget_applies_after_sampling_not_only_before_call(monkeypatch):
    import time
    clock = iter((0.0, 0.0, 1.0))
    monkeypatch.setattr(time, "perf_counter", lambda: next(clock))
    with pytest.raises(RuntimeError, match="BLOCKED_CODEBOOK_WALL_TIME"):
        JointCodebookBuilder(_BatchCorrelated()).build(
            [], [_actions(3)], [[0, 0]], [Mechanism()], draws=10, wall_seconds=0.5)


def _check_legal(report, alpha):
    assert tuple(report["layers"]) == LAYER_ORDER
    assert report["risk_budget_spent"] == 0
    assert report["action_taken"] is False
    assert report["nested_lp_power_within_numerical_tolerance"]
    for layer in report["layers"].values():
        assert layer["alpha"] == alpha
        assert layer["null_risk_bound"] <= alpha + 2e-7
    # Evidence receipts must remain portable, with no ndarray or NaN values.
    json.dumps(report, allow_nan=False)


def test_nominal_response_overlap_is_reported_without_physical_impossibility_claim():
    p = np.array([[_delta([0, 0, 0])], [_delta([0, 0, 0])]])
    book = SoftCodebook(_actions(3), p, exact=True)
    before = book.probabilities.copy()
    report = diagnose_counterevidence_layers(book, 0, [1], alpha=0.03)
    _check_legal(report, 0.03)
    assert report["fallback_for_this_block"]
    assert report["bottleneck"]["cause"] == "nominal_model_response_overlap"
    assert report["pairwise_necessary_bounds"]["closest_clean_pair"]["clean_tv_distance"] == 0
    assert "not_physical_identifiability" in report["scope"]
    assert np.array_equal(book.probabilities, before)


def test_mechanism_uncertainty_is_distinguished_from_nominal_separation():
    zero, one = _delta([0, 0, 0]), _delta([1, 1, 1])
    p = np.array([[zero, one], [one, one]])
    book = SoftCodebook(_actions(3), p, exact=True)
    report = diagnose_counterevidence_layers(book, 0, [1], alpha=0.025)
    _check_legal(report, 0.025)
    assert report["layers"]["nominal_clean"]["power_bound"] > 0.999999
    assert report["layers"]["all_mechanisms_clean"]["power_bound"] <= 0.025 + 1e-7
    assert report["bottleneck"]["cause"] == "declared_mechanism_ambiguity"
    witness = report["pairwise_necessary_bounds"]["closest_clean_pair"]
    assert witness["null_mechanism"] == 1 and witness["clean_tv_distance"] == 0


def test_corruption_overlap_is_distinguished_without_changing_error_budget():
    p = np.array([[_delta([0, 0])], [_delta([1, 1])]])
    channel = CorruptionChannel(max_flips=1)
    book = SoftCodebook(_actions(2), p, exact=True)
    report = diagnose_counterevidence_layers(book, 0, [1], channel=channel, alpha=0.01)
    _check_legal(report, 0.01)
    assert report["layers"]["all_mechanisms_clean"]["power_bound"] > 0.999999
    assert report["layers"]["all_mechanisms_corruption"]["power_bound"] <= 0.01 + 1e-7
    assert report["bottleneck"]["cause"] == "declared_corruption_budget"
    assert channel.max_flips == 1


def test_sampling_tv_bottleneck_has_explicit_ambiguity_intersection_witness():
    p = np.array([[_delta([0, 0, 0])], [_delta([1, 1, 1])]])
    book = SoftCodebook(_actions(3), p, tv_radius=0.6, draws=8,
                        confidence_failure_probability=0.01)
    report = diagnose_counterevidence_layers(book, 0, [1], alpha=0.04)
    _check_legal(report, 0.04)
    assert report["layers"]["all_mechanisms_corruption"]["power_bound"] > 0.999999
    assert report["bottleneck"]["cause"] == "tv_uncertainty_or_conservative_tv_lp"
    witness = report["pairwise_necessary_bounds"]["closest_tv_ambiguity_pair"]
    assert witness["tv_balls_intersect"]
    assert witness["tv_pair_power_upper_bound"] == 0.04
    assert report["layers"]["all_mechanisms_corruption_tv"]["power_bound"] <= 0.04 + 1e-7
    assert np.all(book.tv_radius == 0.6)


def test_fourth_layer_agrees_with_actual_planner_at_its_reserved_alpha():
    p = np.array([[_delta([0, 0, 0, 0, 0])], [_delta([1, 1, 1, 1, 1])]])
    book = SoftCodebook(_actions(5), p, exact=True, cost=5.0)
    channel = CorruptionChannel(max_flips=1, max_erasures=1)
    planner = RobustCounterEvidencePlanner(2, channel=channel, total_alpha=0.05)
    alpha = planner.risk.next_alpha()
    report = diagnose_counterevidence_layers(book, 0, [1], channel=channel, alpha=alpha)
    assert planner.risk.spent == 0  # The diagnostic has no risk-ledger side effect.
    plan = planner.plan([book], [0.99, 0.01])
    _check_legal(report, alpha)
    assert not report["fallback_for_this_block"]
    assert plan.test is not None and plan.reason == "max_score"
    full = report["layers"]["all_mechanisms_corruption_tv"]
    assert full["power_bound"] == pytest.approx(plan.test.alternative_power_bound)
    assert full["null_risk_bound"] == pytest.approx(plan.test.null_risk_bound)
    assert full["cost_adjusted_gain"] == pytest.approx(plan.score)


@pytest.mark.parametrize("challengers", [[], [0], [1, 1], [2], [0.5]])
def test_diagnostic_does_not_silently_change_hypotheses(challengers):
    p = np.array([[_delta([0])], [_delta([1])]])
    book = SoftCodebook(_actions(1), p, exact=True)
    with pytest.raises(ValueError):
        diagnose_counterevidence_layers(book, 0, challengers)
