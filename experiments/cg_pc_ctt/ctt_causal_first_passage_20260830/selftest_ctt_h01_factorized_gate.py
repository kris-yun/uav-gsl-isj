#!/usr/bin/env python3
"""Contract tests for the frozen factorized first-passage model and scores."""

from __future__ import annotations

import numpy as np
import torch

from train_eval_ctt_h01_wind_factorized_first_passage import (
    Factorized,
    INPUT_DIM,
    factorized_loss,
    likelihood_parts,
    rank,
    sign_test,
)


def main() -> int:
    torch.manual_seed(20260835)
    values = torch.randn(17, INPUT_DIM)
    labels = torch.tensor([0, 1, 17, 79, 80, 80, 5, 8, 13, 21, 34, 55, 80, 3, 9, 80, 40])
    model = Factorized()
    probability = model.probabilities(values)
    assert probability.shape == (17, 81)
    assert float(torch.max(torch.abs(probability.sum(1) - 1.0))) < 1e-6
    assert bool(torch.all(probability >= 0.0))
    total, survival, phase = factorized_loss(model, values, labels)
    assert all(bool(torch.isfinite(item)) for item in (total, survival, phase))

    candidate = np.stack([probability[:4].detach().numpy()] * 3)
    observed = np.asarray([0, 17, 80, 3])
    full, ever, conditional_phase = likelihood_parts(candidate, observed)
    assert np.allclose(full, ever + conditional_phase)
    assert rank(np.asarray([2.0, 2.0, 1.0]), 0) == 1.5
    result = sign_test([1, 2, 3, 4], [4, 3, 2, 1])
    assert (result["wins"], result["losses"], result["ties"]) == (2, 2, 0)
    print("CTT_H01_FACTORIZED_GATE_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
