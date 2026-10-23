"""Six numerical falsification tests for the V2 teacher projection.

These check identities of a normalized finite bank, not native GADEN teacher
quality, physical differentiation, or a gas-localization improvement claim.
"""

import math

import pytest
import torch

from gsl_recovery.m1_distill.projection import (
    ConditionalEvidenceProjector,
    ProjectionQualificationError,
)


DTYPE = torch.float64


def source(x=0.0):
    return torch.tensor([float(x), 0.0], dtype=DTYPE)


def uniform_prior(s):
    return s.new_zeros(2)


def causal_atom(history, s, mechanism):
    """Each token denotes an observed event of its own Bernoulli variable."""
    h = torch.stack((torch.sigmoid(s[0]), s.new_tensor(0.3)))
    y = s.new_tensor([0.9, 0.1])
    out = s.new_zeros(2)
    for token in history:
        if token == "h":
            out = out + h.log()
        elif token == "not_h":
            out = out + torch.log1p(-h)
        elif token == "y":
            out = out + y.log()
        elif token == "not_y":
            out = out + torch.log1p(-y)
        else:
            raise ValueError(token)
    return out


def projector(**kwargs):
    return ConditionalEvidenceProjector(
        causal_atom, uniform_prior, derivative_valid=True, **kwargs
    )


def test_mixture_before_log_and_conditional_normalization():
    model = projector()
    out = model.project(["h"], ["y"], source())
    assert out.log_prob.exp().item() == pytest.approx(0.6, abs=1e-12)
    assert out.history_weights.tolist() == pytest.approx([0.625, 0.375])
    arithmetic = 0.625 * 0.9 + 0.375 * 0.1
    geometric = math.exp(0.625 * math.log(0.9) + 0.375 * math.log(0.1))
    assert arithmetic - geometric > 0.1
    total = sum(model.conditional_log_prob(["h"], [v], source()).exp().item()
                for v in ("y", "not_y"))
    assert total == pytest.approx(1.0, abs=1e-12)
    assert model.marginal_log_prob([], source()).item() == pytest.approx(0.0)
    empty = model.project(["h"], [], source())
    assert empty.log_prob.item() == pytest.approx(0.0, abs=1e-12)
    assert empty.score.tolist() == pytest.approx([0.0, 0.0], abs=1e-12)


def test_full_minus_history_derivative_includes_filter_and_path_integral():
    model = projector()
    out = model.project(["h"], ["y"], source())
    # d log(.9 sigmoid(s)+.03) - d log(sigmoid(s)+.3) at s=0.
    assert out.score[0].item() == pytest.approx(0.15625, abs=1e-12)
    assert out.score[1].item() == pytest.approx(0.0, abs=1e-12)
    epsilon = 1e-5
    finite_diff = (model.conditional_log_prob(["h"], ["y"], source(epsilon))
                   - model.conditional_log_prob(["h"], ["y"], source(-epsilon))) / (2 * epsilon)
    assert out.score[0].item() == pytest.approx(finite_diff.item(), abs=1e-9)
    # A frozen belief sees only source-independent emissions and incorrectly
    # gives zero.  Omitting the history normalizer incorrectly gives .46875.
    assert abs(out.score[0].item() - 0.0) > 0.1
    assert abs(out.score[0].item() - 0.46875) > 0.3
    path = model.line_integral(["h"], ["y"], source(-1), source(1), order=12)
    assert path.defect.item() < 1e-10
    assert path.status == "OK_FINITE_BANK"
    reverse = model.pair_endpoint(["h"], ["y"], source(1), source(-1))
    assert reverse.item() == pytest.approx(-path.endpoint.item(), abs=1e-12)


def test_source_dependent_prior_gradient_is_not_detached():
    def prior(s):
        return torch.stack((torch.nn.functional.logsigmoid(s[0]),
                            torch.nn.functional.logsigmoid(-s[0])))

    def atom(history, s, mechanism):
        return len(history) * s.new_tensor([0.9, 0.1]).log()

    model = ConditionalEvidenceProjector(atom, prior, derivative_valid=True)
    result = model.project([], ["y"], source())
    assert result.log_prob.exp().item() == pytest.approx(0.5)
    assert result.score[0].item() == pytest.approx(0.4, abs=1e-12)

    detached = ConditionalEvidenceProjector(atom, lambda s: prior(s).detach(), derivative_valid=True)
    assert detached.score([], ["y"], source())[0].item() == pytest.approx(0.0)


def test_shared_latent_mode_preserves_future_joint_correlation():
    def atom(history, s, mechanism):
        p = s.new_tensor([0.9, 0.1])
        result = s.new_zeros(2)
        for value in history:
            result = result + (p.log() if value else torch.log1p(-p))
        return result

    model = ConditionalEvidenceProjector(atom, uniform_prior, derivative_valid=True)
    p11 = model.conditional_log_prob([], [1, 1], source()).exp().item()
    p1 = model.conditional_log_prob([], [1], source()).exp().item()
    p_second = model.conditional_log_prob([1], [1], source()).exp().item()
    assert p11 == pytest.approx(0.41, abs=1e-12)
    assert p1 == pytest.approx(0.5, abs=1e-12)
    assert p_second == pytest.approx(0.82, abs=1e-12)
    assert abs(p11 - p1 * p1) > 0.15
    total = sum(model.conditional_log_prob([], [a, b], source()).exp().item()
                for a in (0, 1) for b in (0, 1))
    assert total == pytest.approx(1.0, abs=1e-12)


def test_source_independent_world_prior_does_not_imply_shared_filtered_belief():
    # S and Z have independent fair priors, H = S XOR Z.  Conditioning on H=0
    # makes opposite candidate sources imply opposite hidden world states.
    def atom(history, s, mechanism):
        candidate = int(round(float(s[0].detach())))
        values = s.new_tensor([1.0, 0.0] if candidate == 0 else [0.0, 1.0])
        return values.log() if history else s.new_zeros(2)

    model = ConditionalEvidenceProjector(atom, uniform_prior, derivative_valid=False)
    a = model.posterior_weights(["h=0"], source(0))
    b = model.posterior_weights(["h=0"], source(1))
    assert a.tolist() == [1.0, 0.0]
    assert b.tolist() == [0.0, 1.0]
    with pytest.raises(ProjectionQualificationError, match="BLOCKED"):
        model.score([], ["h=0"], source(0))
    # Finite-source likelihood comparisons remain defined under non-smoothness.
    assert model.pair_endpoint([], ["h=0"], source(0), source(1)).item() == pytest.approx(0.0)


def test_identical_source_ratios_do_not_determine_future_information_gain():
    p = torch.tensor([[0.6, 0.3, 0.1], [0.2, 0.4, 0.4]], dtype=DTYPE)
    q = torch.tensor([[0.72, 0.135, 0.145], [0.24, 0.18, 0.58]], dtype=DTYPE)
    assert torch.allclose(p.sum(dim=1), torch.ones(2, dtype=DTYPE))
    assert torch.allclose(q.sum(dim=1), torch.ones(2, dtype=DTYPE))
    assert torch.allclose(p[0] / p[1], q[0] / q[1])

    def eig(law):
        mixture = law.mean(dim=0)
        return (0.5 * law * (law / mixture).log()).sum().item()

    assert eig(p) == pytest.approx(0.10409468018270994, abs=1e-12)
    assert eig(q) == pytest.approx(0.1342724061199999, abs=1e-12)
    assert eig(q) - eig(p) > 0.03


def test_projection_boundary_receipts_and_zero_support_are_explicit():
    low = projector(min_ess=1.9).project(["h"], ["y"], source())
    assert low.status == "LOW_ESS"
    assert low.as_record()["full_ess"] < 1.9
    model = projector(domain_validator=lambda s: bool(s[0] >= 0))
    with pytest.raises(ProjectionQualificationError, match="outside"):
        model.line_integral(["h"], ["y"], source(-1), source(1))

    impossible = ConditionalEvidenceProjector(
        lambda h, s, m: s.new_full((2,), -float("inf")),
        uniform_prior,
        derivative_valid=True,
    )
    assert torch.isneginf(impossible.conditional_log_prob([], ["y"], source()))
    with pytest.raises(ProjectionQualificationError, match="zero support"):
        impossible.project([], ["y"], source())
