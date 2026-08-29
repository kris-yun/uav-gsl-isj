#!/usr/bin/env python3
"""Exact reference semantics for the native PMFS ExpectedValue(..., 0.05) estimator.

The formal closed-loop primary point estimate remains the C++ implementation in
Common/Utils/Math.cpp. This Python function mirrors its *selection cardinality*
and probability-weighted coordinate mean for offline/reference checks.

Important: confidence=0.05 means the highest-probability 5% of grid *cells*, not
5% cumulative posterior mass. Native std::sort does not define a stable tie
order, so formal OFF/ON confirmation must use the native C++ evaluator. Offline
Python uses a deterministic cell-id tie break and reports ties.
"""
from __future__ import annotations
import math
import numpy as np


def selected_cell_count(n_cells: int, confidence: float = 0.05) -> int:
    if n_cells <= 0 or not (0.0 < confidence <= 1.0):
        raise ValueError("invalid PMFS ExpectedValue cardinality input")
    # C++: for (int i=0; i<data.size()*confidence; ++i).
    # For positive non-integral bounds this executes ceil(bound) iterations.
    return min(n_cells, int(math.ceil(n_cells * confidence - 1e-15)))


def expected_value_top_fraction(probability, xy, confidence: float = 0.05,
                                cell_id=None):
    p = np.asarray(probability, dtype=np.float64)
    q = np.asarray(xy, dtype=np.float64)
    if p.ndim != 1 or q.shape != (len(p), 2) or len(p) == 0:
        raise ValueError("probability must be [N] and xy [N,2]")
    if not np.all(np.isfinite(p)) or np.any(p < 0) or not np.all(np.isfinite(q)):
        raise ValueError("non-finite/negative PMFS estimator input")
    if p.sum() <= 0:
        raise ValueError("zero posterior mass")
    ids = np.arange(len(p)).astype(str) if cell_id is None else np.asarray(cell_id).astype(str)
    if ids.shape != p.shape or len(set(ids.tolist())) != len(ids):
        raise ValueError("cell_id must be unique [N]")
    k = selected_cell_count(len(p), confidence)
    order = np.lexsort((ids, -p))
    chosen = order[:k]
    mass = float(p[chosen].sum())
    if not mass > 0:
        raise ValueError("top PMFS cells have zero total probability")
    estimate = np.sum(q[chosen] * p[chosen, None], axis=0) / mass
    boundary = float(p[chosen[-1]])
    tied_boundary = int(np.sum(np.isclose(p, boundary, rtol=0.0, atol=0.0)))
    return estimate, {
        "selected_cells": int(k),
        "selected_mass": mass,
        "boundary_probability": boundary,
        "boundary_tie_count": tied_boundary,
        "python_tie_break": "cell_id_lexicographic",
        "formal_closed_loop_evaluator": "native_cpp_Common_Utils_Math_ExpectedValue",
    }


def localization_error_top_fraction(probability, xy, true_xy, confidence: float = 0.05,
                                    cell_id=None) -> tuple[float, dict]:
    estimate, meta = expected_value_top_fraction(probability, xy, confidence, cell_id)
    truth = np.asarray(true_xy, dtype=np.float64)
    if truth.shape != (2,) or not np.all(np.isfinite(truth)):
        raise ValueError("true_xy must be finite [2]")
    return float(np.linalg.norm(estimate - truth)), meta
