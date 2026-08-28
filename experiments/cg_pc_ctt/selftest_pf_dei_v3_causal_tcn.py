#!/usr/bin/env python3

from __future__ import annotations

import torch

from pf_dei_v3_causal_tcn import initialize_frozen_model
from pf_dei_v3_schema import DILATIONS, FEATURE_NAMES, INPUT_DIM


def main() -> int:
    assert INPUT_DIM == 16
    assert DILATIONS == (1, 2, 4, 8, 16, 32, 64, 128, 256)
    forbidden = ("truth", "source_z", "latent_placement", "localization_error", "future")
    assert not any(token in name for name in FEATURE_NAMES for token in forbidden)

    model = initialize_frozen_model(1701).eval()
    torch.manual_seed(7)
    x = torch.randn(3, 96, INPUT_DIM)
    mask = torch.ones(3, 96, dtype=torch.bool)
    with torch.no_grad():
        score = model(x, mask)
    assert score.shape == (3,) and torch.isfinite(score).all()

    # Strict causality: future changes cannot alter hidden representations at
    # or before the cut, despite the 9-block receptive field.
    changed = x.clone()
    changed[:, 61:, :] = torch.randn_like(changed[:, 61:, :]) * 100.0
    with torch.no_grad():
        before = model.encode_sequence(x)
        after = model.encode_sequence(changed)
    assert torch.equal(before[:, :61], after[:, :61])

    # Padding cannot alter a shorter sequence's score when masked.
    short = x[:1, :70]
    short_mask = torch.ones(1, 70, dtype=torch.bool)
    padded = torch.cat((short, torch.randn(1, 26, INPUT_DIM)), dim=1)
    padded_mask = torch.cat((short_mask, torch.zeros(1, 26, dtype=torch.bool)), dim=1)
    with torch.no_grad():
        short_score = model(short, short_mask)
        padded_score = model(padded, padded_mask)
    assert torch.allclose(short_score, padded_score, rtol=1e-6, atol=1e-7), (short_score, padded_score)

    # Frozen initialization must be exact for the same model seed and differ
    # for independent authorized seeds.
    a = initialize_frozen_model(1701).state_dict()
    b = initialize_frozen_model(1701).state_dict()
    c = initialize_frozen_model(1702).state_dict()
    assert all(torch.equal(a[key], b[key]) for key in a)
    assert any(not torch.equal(a[key], c[key]) for key in a)
    try:
        initialize_frozen_model(0)
    except ValueError as exc:
        assert str(exc) == "PF_DEI_V3_UNAUTHORIZED_MODEL_SEED"
    else:
        raise AssertionError("unauthorized seed accepted")

    print("PF_DEI_V3_CAUSAL_TCN_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
