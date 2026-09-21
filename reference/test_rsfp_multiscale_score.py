#!/usr/bin/env python3
"""Deterministic algebra tests for RSFP V1 multiscale scoring."""
from __future__ import annotations

import math

from rsfp_vgr_fixed_trajectory_replay import (
    DEFAULT_FACTORS,
    candidate_multiscale,
    evidence_variants,
)
from tnqc_vgr_fixed_trajectory_replay import Cell


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def build(sign: float = 1.0, scale: float = 1.7, offset: float = 0.4):
    cells = {}
    alignment = {}
    idx = 0
    for j in range(32):
        for i in range(32):
            # Nonseparable deterministic spatial field.
            obs = (
                0.07 * i
                - 0.05 * j
                + 0.35 * math.sin(0.31 * i)
                + 0.22 * math.cos(0.27 * j)
            )
            pred_logit = sign * scale * obs + offset
            p = sigmoid(pred_logit)
            cells[idx] = Cell(
                cell_index=idx,
                grid_i=i,
                grid_j=j,
                x=float(i),
                y=float(j),
                logodds=obs,
                probability=sigmoid(obs),
                confidence=1.0,
            )
            alignment[idx] = (sigmoid(obs), 1.0, p)
            idx += 1
    return cells, alignment


def main():
    cells, aligned = build(sign=1.0)
    ms = candidate_multiscale(aligned, cells, DEFAULT_FACTORS)
    for factor in DEFAULT_FACTORS:
        assert ms[factor]["valid"], ms[factor]
        assert abs(ms[factor]["canonical_cosine"] - 1.0) < 1e-10, ms[factor]

    ev = evidence_variants(ms, DEFAULT_FACTORS)
    assert ev["valid_all_scales"]
    assert abs(ev["fine_only"] - 1.0) < 1e-10
    assert abs(ev["coarse_only"] - 1.0) < 1e-10
    assert abs(ev["mean_only"] - 1.0) < 1e-10
    assert abs(ev["fixed_only"] - 1.0) < 1e-10

    # Reversing the canonical field should reverse evidence at every scale.
    cells2, reversed_alignment = build(sign=-1.0, scale=1.3, offset=-0.7)
    ms2 = candidate_multiscale(
        reversed_alignment, cells2, DEFAULT_FACTORS
    )
    for factor in DEFAULT_FACTORS:
        assert ms2[factor]["valid"], ms2[factor]
        assert ms2[factor]["canonical_cosine"] < -0.999999999, ms2[factor]

    ev2 = evidence_variants(ms2, DEFAULT_FACTORS)
    assert ev2["fixed_only"] <= ev2["mean_only"] + 1e-15
    assert -1.0 <= ev2["fixed_only"] <= 1.0

    print("RSFP_MULTISCALE_SCORE_TEST_PASS")


if __name__ == "__main__":
    main()
