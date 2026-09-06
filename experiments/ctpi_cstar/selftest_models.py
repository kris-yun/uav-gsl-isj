from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from m1_picr.model import PICRModel, picr_pair_losses
from m2_cpo.model import CPOResidualOperator, cpo_first_passage_nll, cpo_brier


def main():
    torch.manual_seed(7)

    # PICR arbitrary-candidate posterior and causal pair-loss shape checks.
    b, t, n = 4, 12, 9
    history = torch.randn(b, t, 8)
    history[..., 0] = torch.rand(b, t) * 2.0
    history[..., 1] = torch.rand(b, t)
    valid = torch.ones(b, t, dtype=torch.bool)
    valid[0, -2:] = False  # right padding only
    candidates = torch.randn(b, n, 2)
    candidate_valid = torch.ones(b, n, dtype=torch.bool)
    candidate_valid[:, 0] = False

    m1 = PICRModel(
        d_model=32, nhead=4, layers=2,
        z_source_dim=16, z_nuisance_dim=8,
    )
    out = m1(history, candidates, valid, candidate_valid)
    assert out.source_posterior.shape == (b, n)
    assert torch.allclose(
        out.source_posterior.sum(dim=-1), torch.ones(b), atol=1e-6
    )
    assert torch.all(out.candidate_support[:, 0] == 0)
    assert not bool(out.abstain.any())

    out2 = m1(
        history + 0.01 * torch.randn_like(history),
        candidates, valid, candidate_valid
    )
    losses = picr_pair_losses(
        out, out2, torch.tensor([True, True, False, False])
    )
    assert all(torch.isfinite(value) for value in losses.values())

    # Regression: left padding is rejected instead of allowing version-specific
    # fully-masked attention rows / NaNs.
    bad_valid = valid.clone()
    bad_valid[0] = False
    bad_valid[0, 2:] = True
    try:
        m1(history, candidates, bad_valid, candidate_valid)
    except ValueError as exc:
        assert "RIGHT_PAD_REQUIRED" in str(exc)
    else:
        raise AssertionError("PICR_LEFT_PADDING_WAS_NOT_REJECTED")

    # Regression: no valid candidate support is an explicit abstention, not an
    # apparently valid uniform source belief.
    none_valid = candidate_valid.clone()
    none_valid[1] = False
    out3 = m1(history, candidates, valid, none_valid)
    assert bool(out3.abstain[1])
    assert not bool(out3.valid_source_belief[1])
    assert torch.allclose(
        out3.source_posterior[1], torch.full((n,), 1.0 / n), atol=1e-6
    )

    # Load-bearing zS regression. Force zS to the same zero vector for every
    # history, keep the candidate set fixed, and flip only wind. The posterior
    # must remain unchanged. This specifically rejects the reviewed shortcut in
    # which candidate-relative wind/pose features bypassed zS.
    bypass = PICRModel(
        d_model=32, nhead=4, layers=1,
        z_source_dim=16, z_nuisance_dim=8,
    )
    for p in bypass.source_proj.parameters():
        p.data.zero_()
    h1 = torch.zeros(1, 8, 8)
    h1[..., 0] = 0.5
    h1[..., 2] = 1.0
    h1[..., 4] = torch.linspace(-1.0, 1.0, 8)
    h2 = h1.clone()
    h2[..., 2] = -1.0
    c = torch.tensor([[[-1.0, 0.0], [1.0, 0.0]]])
    v = torch.ones(1, 8, dtype=torch.bool)
    o1 = bypass(h1, c, v)
    o2 = bypass(h2, c, v)
    assert torch.allclose(o1.source_representation, o2.source_representation, atol=1e-7)
    assert torch.allclose(o1.source_posterior, o2.source_posterior, atol=1e-7)

    # CPO hazard -> first-passage -> encounter-CDF/route-committor checks.
    horizon, feature_dim = 10, 14
    features = torch.randn(b, horizon, feature_dim)
    prior_hazard_logit = torch.randn(b, horizon)
    prior_logppm_mean = torch.randn(b, horizon)
    m2 = CPOResidualOperator(
        feature_dim=feature_dim, d_model=32, nhead=4, layers=2
    )
    cpo = m2(features, prior_hazard_logit, prior_logppm_mean)
    assert cpo.first_hit_prob.shape == (b, horizon + 1)
    assert torch.allclose(
        cpo.first_hit_prob.sum(dim=-1), torch.ones(b), atol=1e-6
    )
    assert torch.all(
        cpo.encounter_cdf[:, 1:] >= cpo.encounter_cdf[:, :-1] - 1e-7
    )
    assert torch.allclose(
        cpo.route_committor, 1.0 - cpo.first_hit_prob[:, -1], atol=1e-6
    )
    targets = torch.tensor([0, 3, horizon, 7])
    assert torch.isfinite(cpo_first_passage_nll(cpo, targets))
    assert torch.isfinite(cpo_brier(cpo, targets))

    print("CSTAR_MODEL_SHAPE_AND_REVIEW_REGRESSION_SELFTEST PASS")


if __name__ == "__main__":
    main()
