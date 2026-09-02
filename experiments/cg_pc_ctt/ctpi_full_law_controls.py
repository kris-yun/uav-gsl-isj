#!/usr/bin/env python3
"""Truth-blind destructive-control helpers for CTPI-FL V0.3.

These functions are not part of the inference operator.  They define complete
source-law reassignment controls in stable physical carrier-ID space so the
control itself is invariant to incidental candidate-array ordering.
"""
from __future__ import annotations

import numpy as np


def canonical_cyclic_reassignment_indices(labels: np.ndarray | list[str], shift: int) -> np.ndarray:
    """Map each physical target source to a wrong response law using stable IDs."""
    ids = np.asarray(labels, dtype=str)
    if ids.ndim != 1 or ids.size < 2 or len(set(ids.tolist())) != ids.size:
        raise ValueError("CTPI_CANONICAL_LABELS")
    if not 1 <= shift < ids.size:
        raise ValueError("CTPI_CYCLIC_SHIFT")
    canonical = np.argsort(ids, kind="mergesort")
    source_for_target = np.empty(ids.size, dtype=np.int64)
    for pos, target_idx in enumerate(canonical):
        source_for_target[target_idx] = canonical[(pos + int(shift)) % ids.size]
    return source_for_target


def transport_break_strength_for_permutation(
    radius: np.ndarray, permutation: np.ndarray, member_count: int,
) -> float:
    """Mean normalized empirical-law separation destroyed by reassignment."""
    r = np.asarray(radius, dtype=np.int64)
    pi = np.asarray(permutation, dtype=np.int64)
    if r.ndim != 2 or r.shape[0] != r.shape[1] or pi.shape != (r.shape[0],):
        raise ValueError("CTPI_BREAK_SHAPE")
    if set(pi.tolist()) != set(range(r.shape[0])):
        raise ValueError("CTPI_BREAK_PERMUTATION")
    if member_count < 1:
        raise ValueError("CTPI_BREAK_MEMBER_COUNT")
    vals = r[np.arange(r.shape[0]), pi].astype(np.float64)
    return float(np.mean(vals) / float(member_count))


def selftest() -> None:
    labels = np.asarray(["k03", "k01", "k04", "k02"])
    for shift in range(1, len(labels)):
        pi1 = canonical_cyclic_reassignment_indices(labels, shift)
        assert not np.any(pi1 == np.arange(len(labels)))
        order = np.asarray([2, 0, 3, 1])
        labels2 = labels[order]
        pi2 = canonical_cyclic_reassignment_indices(labels2, shift)
        pairs1 = {(labels[i], labels[pi1[i]]) for i in range(len(labels))}
        pairs2 = {(labels2[i], labels2[pi2[i]]) for i in range(len(labels2))}
        assert pairs1 == pairs2
    radius = np.asarray([[0,1,2,3],[1,0,2,2],[2,2,0,1],[3,2,1,0]])
    pi = canonical_cyclic_reassignment_indices(labels, 1)
    b = transport_break_strength_for_permutation(radius, pi, 3)
    assert 0.0 <= b <= 1.0
    print("CTPI_FULL_LAW_CONTROLS_SELFTEST=PASS")


if __name__ == "__main__":
    selftest()
