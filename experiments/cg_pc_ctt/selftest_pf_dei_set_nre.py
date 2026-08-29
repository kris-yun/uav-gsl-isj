#!/usr/bin/env python3
from __future__ import annotations

import inspect
import json

import numpy as np
import torch

from pf_dei_set_nre import ConditionedDeepSetNRE, residual_corrected_posterior


def main() -> None:
    torch.manual_seed(3101)
    torch.use_deterministic_algorithms(True)
    model = ConditionedDeepSetNRE().eval()
    n, b, m = 3, 11, 7
    obs = torch.rand(n, b, 10)
    pred = torch.rand(n, b, m, 10)
    ctx = torch.rand(n, b, 6)
    cand = torch.rand(n, 12)
    bmask = torch.ones(n, b, dtype=torch.bool)
    bmask[1, -2:] = False
    mmask = torch.ones(n, m, dtype=torch.bool)
    with torch.no_grad():
        base = model(obs, pred, ctx, cand, bmask, mmask)
        member_perm = torch.tensor([4, 0, 6, 2, 1, 5, 3])
        member = model(obs, pred[:, :, member_perm], ctx, cand, bmask, mmask[:, member_perm])
        block_perm = torch.tensor([8, 1, 10, 0, 7, 3, 6, 5, 2, 9, 4])
        block = model(obs[:, block_perm], pred[:, block_perm], ctx[:, block_perm], cand,
                      bmask[:, block_perm], mmask)
    member_err = float(torch.max(torch.abs(base - member)))
    block_err = float(torch.max(torch.abs(base - block)))

    q = np.asarray([1e-49, 0.2, 0.3, 0.5 - 1e-49], dtype=np.float64)
    p = residual_corrected_posterior(q, np.asarray([100.0, -2.0, 0.0, 1.0]))
    heldout_checks = []
    for heldout in range(8):
        members = [m for m in range(8) if m != heldout]
        heldout_checks.append(len(members) == 7 and heldout not in members)
    source = inspect.getsource(ConditionedDeepSetNRE).lower()
    forbidden = [name for name in ("conv1d", "transformer", "attention", "lstm", "gru") if name in source]
    result = {
        "member_permutation_max_abs": member_err,
        "block_permutation_max_abs": block_err,
        "strict_leave_one_member_out_all_8": all(heldout_checks),
        "residual_posterior_sum": float(p.sum()),
        "residual_posterior_finite": bool(np.all(np.isfinite(p))),
        "tiny_pmfs_support_preserved_positive": bool(p[0] > 0),
        "forbidden_architecture_tokens": forbidden,
        "pass": bool(member_err <= 1e-6 and block_err <= 1e-6 and all(heldout_checks)
                     and np.isclose(p.sum(), 1.0) and np.all(np.isfinite(p))
                     and p[0] > 0 and not forbidden),
    }
    if not result["pass"]:
        raise SystemExit("PF_DEI_SET_NRE_SELFTEST_FAIL " + json.dumps(result, sort_keys=True))
    print("PF_DEI_SET_NRE_SELFTEST_PASS " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
