"""Independent integration/qualification audit for the V2 neural path.

All data below are explicitly synthetic engineering fixtures.  No assertion
in this file is evidence of House/GADEN or lake-side localization improvement.
"""

from dataclasses import asdict, replace
from pathlib import Path
import json

import numpy as np
import pytest
import torch

from gsl_recovery.m1_neural.model import Geometry, NeuralConfig, NeuralJointGenerator
from gsl_recovery.m1_neural.teacher import PhysicalBank, PrivilegedPhysicalTeacher
from gsl_recovery.m1_neural.training import (
    TrainConfig, build_targets, sha256, train_student, train_teacher, write_dataset,
)
from gsl_recovery.types import Action, Mechanism, Observation, observation_to_dict


def tiny_config(**changes):
    base = dict(hidden=8, geometry_width=4, query_width=6, modes=2)
    base.update(changes)
    return NeuralConfig(**base)


def wind_bank(*, native_claim=False, static=True):
    points = np.array([
        [[0, 0, 1, 0, 0.5, 0.1, 0], [1, 0, 1, 1, 0.6, 0.1, 0]],
        [[0, 0, 1, 0, -0.5, -0.1, 0], [1, 0, 1, 1, -0.6, -0.1, 0]],
    ], dtype=np.float32)
    metadata = {
        "split": "train", "source_independent_exogenous": True,
        "wind_units": "m/s", "position_units": "m", "time_units": "s",
        "scope": "PHYSICALLY_QUALIFIED_TRAIN" if native_claim else "ENGINEERING_ONLY",
        "static_wind": static, "world_ids": ["synthetic_world_0", "synthetic_world_1"],
    }
    if native_claim:
        # Deliberately self-attested strings: never an instrumented simulator
        # derivative qualification.  The native-gradient gate must reject.
        metadata.update({key: "0" * 64 for key in (
            "physics_qualification_sha256", "readout_contract_sha256", "world_lineage_sha256")})
    return PhysicalBank(points, np.zeros(2, dtype=np.float32), metadata)


def observed_history():
    return [
        Observation("h0", Action(0.2, 0.4, 1, time=0), (0.2, -0.1), 0.0),
        Observation("h1", Action(0.5, 0.3, 1, time=1), (-0.1, 0.2), 1.0),
    ]


def make_training_fixture(tmp_path):
    cfg = tiny_config()
    bank = wind_bank()
    bank_path = tmp_path / "bank"
    bank.save(bank_path)
    records = []
    for j, s in enumerate(([0.0, 0.0], [1.0, 0.0])):
        observations = []
        for k in range(4):
            wind = (0.5, 0.1) if j == 0 else (-0.5, -0.1)
            observations.append(Observation(f"fixture_{j}_{k}", Action(0.2 + 0.1*k, 0.3, 1, time=k), wind, float((j+k) % 2)))
        records.append({
            "id": f"fixture_{j}", "source": s, "world_index": j,
            "mechanism": asdict(Mechanism()),
            "observations": [observation_to_dict(o) for o in observations],
            "metadata": {
                "split": "train", "training_allowed": True, "scope": "ENGINEERING_ONLY",
                "lineage_group": f"independent_fixture_{j}",
                "bank_world_id": bank.metadata["world_ids"][j],
            },
        })
    manifest = write_dataset(tmp_path / "data", records, cfg, Geometry.empty(), [[0, 0], [1, 0]])
    # The generated target fixture tests artifact plumbing, not teacher fit.
    torch.manual_seed(4)
    teacher = PrivilegedPhysicalTeacher(bank, cfg, Geometry.empty(), field_width=4)
    teacher.training_receipt = {
        "manifest_sha256": sha256(manifest), "status": "ENGINEERING_FIXTURE_UNTRAINED",
    }
    teacher_path = tmp_path / "teacher"
    teacher.save(teacher_path)
    return manifest, bank_path, teacher_path


def test_teacher_projection_matches_neural_conditional_and_finite_difference():
    torch.manual_seed(5)
    teacher = PrivilegedPhysicalTeacher(wind_bank(), tiny_config(), field_width=4).double()
    history = observed_history()
    prefix, future = history[:1], history[1:]
    s = torch.tensor([0.3, -0.1], dtype=torch.float64)
    result = teacher.projector().project(prefix, future, s)
    direct = teacher.conditional_log_prob_torch(prefix, future, s)
    assert result.log_prob.item() == pytest.approx(direct.item(), abs=1e-10)
    h = 1e-5
    for d in range(2):
        change = torch.zeros(2, dtype=torch.float64)
        change[d] = h
        finite = (teacher.conditional_log_prob_torch(prefix, future, s+change)
                  - teacher.conditional_log_prob_torch(prefix, future, s-change)) / (2*h)
        assert result.score[d].item() == pytest.approx(finite.item(), abs=2e-7)


def test_masked_placeholder_values_do_not_enter_likelihood_or_future_state():
    torch.manual_seed(6)
    model = NeuralJointGenerator(tiny_config())
    masked_nan = Observation("missing", Action(0.2, 0.3, time=0), (float("nan"), float("nan")), float("nan"), (False, False), False)
    masked_other = replace(masked_nan, wind=(1e8, -1e8), gas=1e8)
    observed = Observation("next", Action(0.4, 0.3, time=1), (0.1, 0.2), 1.0)
    s = [0.0, 0.0]
    assert model.log_prob([masked_nan], s) == pytest.approx(0.0, abs=1e-6)
    left = model.log_prob([masked_nan, observed], s)
    right = model.log_prob([masked_other, observed], s)
    assert left == pytest.approx(right, abs=1e-7)
    # This is fixed-mask observed-data normalization, not a claim that the
    # whole GRU trajectory equals integrating a fully observed trajectory.
    mass = 0.0
    for gas in (0.0, 1.0):
        q = replace(observed, wind=(float("nan"), float("nan")), wind_available=(False, False), gas=gas)
        mass += np.exp(model.conditional_log_prob_torch([masked_nan], [q], s).detach().item())
    assert mass == pytest.approx(1.0, abs=2e-6)


def test_bernoulli_sampling_and_density_use_the_same_clamped_probability():
    model = NeuralJointGenerator(tiny_config())
    with torch.no_grad():
        for p in model.emission.parameters():
            p.zero_()
        model.emission[-1].bias[4] = -100.0
    s = model.tensor([0.0, 0.0])
    h, _ = model.initial_state(s)
    action = Action(0.1, 0.1)
    q = model._query(s, action, None)
    params = model._emission_parameters(h, q, None, 0, action)
    obs = Observation("binary", action, (0.0, 0.0), 1.0, (False, False), True)
    event_mass = model._log_emission(params, obs).exp()
    assert torch.allclose(event_mass, params[2], rtol=1e-5, atol=0.0)


def test_censored_readout_atom_mass_and_sampling_are_consistent():
    model = NeuralJointGenerator(tiny_config(gas_model="censored_lognormal", gas_lod=1.0))
    with torch.no_grad():
        for p in model.emission.parameters():
            p.zero_()
    action = Action(0.2, 0.1)
    mechanism = Mechanism("detection_loss", magnitude=0.25)
    s = model.tensor([0.0, 0.0])
    h, _ = model.initial_state(s)
    params = model._emission_parameters(h, model._query(s, action, None), mechanism, 0, action)
    obs = Observation("zero", action, (0.0, 0.0), 0.0, (False, False), True)
    assert model._log_emission(params, obs).exp().tolist() == pytest.approx([0.625, 0.625], abs=1e-6)
    rollouts = model.sample_future_batch([], [action], [0.0, 0.0], mechanism, draws=2000, rng=np.random.default_rng(8))
    gas = np.array([row[0].gas for row in rollouts])
    assert np.mean(gas == 0) == pytest.approx(0.625, abs=0.04)
    assert np.all((gas == 0) | (gas > 1.0))


def test_student_checkpoint_is_self_contained_and_teacher_cannot_load_as_student(tmp_path):
    torch.manual_seed(9)
    model = NeuralJointGenerator(tiny_config())
    expected = model.log_prob(observed_history(), [0.1, 0.2])
    checkpoint = tmp_path / "student"
    model.save(checkpoint)
    loaded = NeuralJointGenerator.load(checkpoint)
    assert loaded.log_prob(observed_history(), [0.1, 0.2]) == pytest.approx(expected, abs=1e-7)
    assert not hasattr(loaded, "bank")
    assert "physical_points" not in loaded.state_dict()
    teacher = PrivilegedPhysicalTeacher(wind_bank(), tiny_config(), field_width=4)
    teacher.save(tmp_path / "teacher")
    with pytest.raises(ValueError, match="format"):
        NeuralJointGenerator.load(tmp_path / "teacher")


def test_native_derivative_requires_more_than_self_attested_bank_metadata():
    teacher = PrivilegedPhysicalTeacher(wind_bank(native_claim=True), tiny_config(), field_width=4)
    with pytest.raises(ValueError, match="BLOCKED"):
        teacher.projector(require_native=True)


def test_each_world_requires_its_own_time_support():
    bank = wind_bank(static=False)
    bank.points[1, :, 3] += 10.0
    with pytest.raises(ValueError, match="[Tt][Ii][Mm][Ee]|SUPPORT"):
        teacher = PrivilegedPhysicalTeacher(bank, tiny_config(), field_width=4)
        teacher._field_weights(Action(0.2, 0.1, time=5.0))


def test_target_artifact_serializes_nonleaf_path_tensors(tmp_path):
    manifest, _, teacher_path = make_training_fixture(tmp_path)
    out = tmp_path / "targets"
    report = build_targets(manifest, teacher_path, out, count=2, seed=10, order=2)
    data = json.loads((out / "targets.json").read_text())
    assert report["count"] == 2
    assert len(data["targets"]) == 2
    for row in data["targets"]:
        assert np.isfinite(row["projected_pair"])
        assert isinstance(row["path_certificate"], dict)


def test_resume_rejects_changed_target_labels_with_same_dataset(tmp_path):
    manifest, _, teacher_path = make_training_fixture(tmp_path)
    targets = tmp_path / "targets"
    build_targets(manifest, teacher_path, targets, count=2, seed=11, order=2)
    out = tmp_path / "fit"
    config = TrainConfig(epochs=1, batch_size=2, target_batch=1, variant="projected_evidence", wall_seconds=60)
    train_student(manifest, out, config, targets=targets)
    payload = json.loads((targets / "targets.json").read_text())
    payload["targets"][0]["projected_pair"] += 1.0
    (targets / "targets.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="[Tt]arget|[Ii]dentity|[Cc]heckpoint"):
        train_student(manifest, out, replace(config, epochs=2), targets=targets, resume=out / "resume")


def test_teacher_resume_rejects_changed_physical_bank(tmp_path):
    manifest, bank_path, _ = make_training_fixture(tmp_path)
    config = TrainConfig(epochs=1, batch_size=2, wall_seconds=60)
    out = tmp_path / "teacher_fit"
    train_teacher(manifest, bank_path, out, config)
    changed = PhysicalBank.load(bank_path)
    changed.points[:, :, 4] += 1.0
    changed.save(bank_path)
    with pytest.raises(ValueError, match="[Bb]ank|[Ii]dentity|[Cc]heckpoint"):
        train_teacher(manifest, bank_path, out, replace(config, epochs=2), resume=out / "resume")
