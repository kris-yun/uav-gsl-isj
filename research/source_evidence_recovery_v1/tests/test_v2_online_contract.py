"""Focused independent online-contract audit using synthetic tiny models.

These checks establish execution and evidence-accounting properties only.
They are not localization-performance or physical-model qualification tests.
"""
from dataclasses import asdict
import importlib

import numpy as np
import pytest
import torch

from gsl_recovery.m1_neural import NeuralConfig, NeuralJointGenerator
from gsl_recovery.m1_neural.teacher import PhysicalBank, PrivilegedPhysicalTeacher
from gsl_recovery.m2_replay import ReplayEngine
from gsl_recovery.navigation.v2_session import ActiveSessionV2
from gsl_recovery.types import Action, Mechanism, Observation, observation_to_dict


SOURCES = [[0.0, 0.0], [1.0, 0.0]]


def tiny_model(**overrides):
    torch.manual_seed(123)
    options = dict(hidden=6, geometry_width=3, query_width=4, modes=2)
    options.update(overrides)
    return NeuralJointGenerator(NeuralConfig(**options))


def make_session(*, variant="B", m2_variant="Bprime", model=None):
    return ActiveSessionV2(
        tiny_model() if model is None else model,
        SOURCES, [Mechanism(), Mechanism("sensor_offset", onset=1, magnitude=0.7)],
        seed=12, draws=8, eig_draws=2, wall_seconds=15,
        max_flips=0, variant=variant, m2_variant=m2_variant,
    )


def plan_request():
    blocks = [
        [Action(0.2, 0.3, time=1.0), Action(0.3, 0.3, time=2.0)],
        [Action(0.8, 0.3, time=1.0), Action(0.9, 0.3, time=2.0)],
    ]
    return {"op": "plan", "navigation_qualified": True,
            "action_blocks": [[asdict(a) for a in block] for block in blocks]}


def committed_observations(plan):
    return [observation_to_dict(Observation(
        f"online_{k}", Action(**action), (0.1, -0.1), float(k % 2),
    )) for k, action in enumerate(plan["actions"])]


def test_online_boundary_rejects_oracle_fields_before_any_evidence_changes():
    session = make_session()
    request = plan_request()
    request["future_true_wind"] = [[1.0, 0.0]]
    with pytest.raises(ValueError, match="privileged request"):
        session.request(request)
    assert session.pending is None and len(session.ledger) == 0
    plan = session.request(plan_request())
    observations = committed_observations(plan)
    observations[0]["true_source"] = SOURCES[1]
    with pytest.raises(ValueError, match="privileged observation"):
        session.request({"op": "observe", "observations": observations})
    assert len(session.ledger) == 0
    assert session.pending is not None and not session.pending.consumed


@pytest.mark.parametrize("overrides", [
    {"scope": "NUMERICAL_ONLY"}, {"time_semantics": "record_index"},
])
def test_numerical_or_index_clock_model_cannot_enter_online_loop(overrides):
    with pytest.raises(ValueError, match="BLOCKED_NONPHYSICAL"):
        make_session(model=tiny_model(**overrides))


def test_privileged_teacher_cannot_enter_online_loop():
    points = np.array([
        [[0, 0, 1, 0, 0.2, 0.0, 0.0]],
        [[0, 0, 1, 0, -0.2, 0.0, 0.0]],
    ], dtype=np.float32)
    bank = PhysicalBank(points, np.zeros(2, dtype=np.float32), {
        "split": "train", "source_independent_exogenous": True,
        "wind_units": "m/s", "position_units": "m", "time_units": "s",
        "scope": "ENGINEERING_ONLY", "static_wind": True,
        "world_ids": ["fixture_0", "fixture_1"],
    })
    teacher = PrivilegedPhysicalTeacher(bank, tiny_model().config, field_width=3)
    with pytest.raises(ValueError, match="BLOCKED_ONLINE_TEACHER"):
        make_session(model=teacher)


def test_neural_suffix_replay_equals_full_recomputation_without_double_counting():
    model = tiny_model().double()
    mechanisms = [Mechanism(), Mechanism("sensor_offset", onset=1, magnitude=0.7),
                  Mechanism("detection_loss", onset=2, magnitude=0.3)]
    history = [Observation(f"replay_{k}", Action(0.2+0.1*k, 0.3, time=k),
                           (0.1*(-1)**k, -0.1), float(k % 2)) for k in range(4)]
    engine = ReplayEngine(model, SOURCES, mechanisms)
    result = engine.infer(history, "Bprime")
    expected = np.array([[model.log_prob(history, s, m) for m in mechanisms] for s in SOURCES])
    np.testing.assert_allclose(result.log_likelihood, expected, rtol=0, atol=1e-10)
    assert max(abs(row["full_recompute_error"]) for row in result.records) < 1e-10
    # Repeating a query uses fixed original priors, not the previous posterior.
    np.testing.assert_array_equal(engine.infer(history, "Bprime").joint_posterior,
                                  result.joint_posterior)
    assert result.joint_posterior.sum() == pytest.approx(1.0)


def test_m3_direct_cluster_transfer_is_not_overwritten_by_full_eig(monkeypatch):
    module = importlib.import_module("gsl_recovery.m3_planner.joint_eig")
    def forbidden(*args, **kwargs):
        raise AssertionError("M3 B must retain its own cluster objective")
    monkeypatch.setattr(module, "full_observation_eig", forbidden)
    session = make_session(variant="B")
    result = session.request(plan_request())
    assert session.pending.variant == "B"
    assert result["reason"] == "max_score"
    assert result["full_observation_eig"] == []
    assert not result["counterevidence_test_reserved"]


def test_direct_m2_transfer_can_finish_observe_and_report_its_actual_scope():
    session = make_session(variant="B", m2_variant="B")
    plan = session.request(plan_request())
    result = session.request({"op": "observe", "observations": committed_observations(plan)})
    assert result["op"] == "update" and result["observations"] == 2
    assert result["diagnosis_added_as_evidence"] is False
    assert session.pending is None and session.round == 1
    # Exact suffix replacement is not a property of the direct-transfer B.
    assert result["maximum_suffix_replay_discrepancy"] is None


def test_cli_endpoint_ablation_passes_no_directional_to_real_training_config(monkeypatch, capsys):
    from gsl_recovery import v2_cli
    from gsl_recovery.m1_neural import training
    seen = []
    def capture(manifest, out, config, targets, resume, override):
        seen.append(config)
        return {"status": "CAPTURED_CONFIG_ONLY"}
    monkeypatch.setattr(training, "train_student", capture)
    base = ["train-student", "--manifest", "unused.json", "--out", "unused",
            "--variant", "projected_evidence"]
    assert v2_cli.main(base + ["--no-directional"]) == 0
    assert seen[-1].directional is False
    assert seen[-1].variant == "projected_evidence"
    assert v2_cli.main(base) == 0
    assert seen[-1].directional is True
    capsys.readouterr()
