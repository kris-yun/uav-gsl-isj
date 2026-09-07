"""Self-test for the normalized M2->M1 observation-law boundary."""
from __future__ import annotations

from pathlib import Path
import sys
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cstar_reference import CPORouteLaw
from m1_picr.route_law_score import innovation_loglik, score_route_laws


def main():
    law = CPORouteLaw.from_hazards([0.2, 0.3, 0.4], [0.0, 0.1, 0.2], [0.5, 0.5, 0.5])
    values = torch.tensor([0.0, 0.1, 0.2])
    valid = torch.tensor([True, True, True])
    exact = innovation_loglik(values, torch.tensor(law.logppm_mean),
                              torch.tensor(law.logppm_scale), valid, rho=0.6)
    assert torch.isfinite(exact)
    # A valid zero is scored; only an invalid block is neutral at the M1 layer.
    zero = innovation_loglik(torch.zeros(3), torch.tensor(law.logppm_mean),
                             torch.tensor(law.logppm_scale), valid, rho=0.0)
    assert torch.isfinite(zero) and float(zero) != 0.0
    scored = score_route_laws([law, law], [law, law], values, valid)
    assert torch.allclose(scored.posterior, torch.tensor([0.5, 0.5]), atol=1e-6)
    missing = torch.tensor([False, False, False])
    assert float(innovation_loglik(values, torch.tensor(law.logppm_mean),
                                   torch.tensor(law.logppm_scale), missing)) == 0.0
    print("CSTAR_M1_ROUTE_LAW_SCORE_SELFTEST PASS")


if __name__ == "__main__":
    main()
