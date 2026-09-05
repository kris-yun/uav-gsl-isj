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
    valid[0, -2:] = False
    candidates = torch.randn(b, n, 2)
    support = torch.ones(b, n, t, dtype=torch.bool)
    support[:, 0, :] = False

    m1 = PICRModel(
        d_model=32, nhead=4, layers=2,
        z_source_dim=16, z_nuisance_dim=8,
    )
    out = m1(history, candidates, valid, support)
    assert out.source_posterior.shape == (b, n)
    assert torch.allclose(
        out.source_posterior.sum(dim=-1), torch.ones(b), atol=1e-6
    )
    assert torch.all(out.candidate_support[:, 0] == 0)

    out2 = m1(
        history + 0.01 * torch.randn_like(history), candidates, valid, support
    )
    losses = picr_pair_losses(
        out, out2, torch.tensor([True, True, False, False])
    )
    assert all(torch.isfinite(value) for value in losses.values())

    # CPO hazard -> first-passage -> committor contract checks.
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
        cpo.committor[:, 1:] >= cpo.committor[:, :-1] - 1e-7
    )
    assert torch.allclose(
        cpo.committor[:, -1], 1.0 - cpo.first_hit_prob[:, -1], atol=1e-6
    )
    targets = torch.tensor([0, 3, horizon, 7])
    assert torch.isfinite(cpo_first_passage_nll(cpo, targets))
    assert torch.isfinite(cpo_brier(cpo, targets))

    print("CSTAR_MODEL_SHAPE_SELFTEST PASS")


if __name__ == "__main__":
    main()
