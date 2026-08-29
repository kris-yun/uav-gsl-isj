#!/usr/bin/env python3
import numpy as np
import torch

from pf_snre_final_core import ConditionedMomentSetDirectNRE, direct_posterior
from pf_snre_spatial_eval import (
    expand_region_mass_to_cells, posterior_mean_xy, spatial_energy_score,
    hpd_cell_mask, deterministic_kcenter,
)


def main():
    torch.manual_seed(1)
    model = ConditionedMomentSetDirectNRE().eval()
    n, b, m = 3, 7, 8
    obs = torch.rand(n, b, 10)
    pred = torch.rand(n, b, m, 10)
    ctx = torch.rand(n, b, 6)
    cand = torch.rand(n, 5)
    bm = torch.ones(n, b, dtype=torch.bool)
    mm = torch.ones(n, m, dtype=torch.bool)
    with torch.no_grad():
        a = model(obs, pred, ctx, cand, bm, mm)
        member_perm = torch.tensor([3, 1, 7, 0, 4, 6, 2, 5])
        b_member = model(obs, pred[:, :, member_perm], ctx, cand, bm, mm[:, member_perm])
        block_perm = torch.tensor([5, 0, 6, 1, 4, 2, 3])
        b_block = model(obs[:, block_perm], pred[:, block_perm], ctx[:, block_perm],
                        cand, bm[:, block_perm], mm)
    assert torch.max(torch.abs(a - b_member)).item() < 1e-6
    assert torch.max(torch.abs(a - b_block)).item() < 1e-6

    q = direct_posterior(np.array([0.25, 0.75]), np.zeros(2))
    assert np.allclose(q, [0.25, 0.75])
    ptr = np.array([0, 1, 4])
    cell = expand_region_mass_to_cells(q, ptr)
    assert np.allclose(cell, [0.25, 0.25, 0.25, 0.25])
    xy = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    assert np.allclose(posterior_mean_xy(cell, xy), [0.5, 0.5])
    assert spatial_energy_score(cell, xy, [0.5, 0.5]) >= 0
    assert hpd_cell_mask(cell, 0.9).sum() == 4

    ids = np.array(["b", "a", "c"])
    pts = np.array([[0, 0], [1, 0], [10, 0]], float)
    sel = deterministic_kcenter(pts, ids, 2)
    assert ids[sel[0]] == "a" and ids[sel[1]] == "c"
    print("PF_SNRE_FINAL_SELFTEST PASS")


if __name__ == "__main__":
    main()
