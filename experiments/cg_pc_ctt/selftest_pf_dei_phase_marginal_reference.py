#!/usr/bin/env python3
"""Deterministic selftest for PF-DEI phase-marginalized dynamic-event reference."""
from __future__ import annotations

import numpy as np
import pf_dei_phase_marginal_reference as pf


def _context(cid, y, good_member=None):
    y = np.asarray(y, dtype=np.int8)
    S, M, J, B, T = 2, 8, y.shape[0], y.shape[1], 32
    I = np.empty((J, B, 2), dtype=float)
    for j in range(J):
        base = 10 * j
        for b in range(B):
            I[j, b] = [base + 2 * b, base + 2 * b + 2]
    x = np.zeros((S, M, J, T), dtype=np.int8)
    for m in range(M):
        for j in range(J):
            for b in range(B):
                a, e = map(int, I[j, b])
                v = int(y[j, b])
                if good_member is not None and m >= 4 and m != good_member and b == 0:
                    v = 1 - v
                x[0, m, j, a:e] = v
                x[1, m, j, a:e] = 1 - int(y[j, b])
    return {"id": cid, "sim_occupancy": x, "observed_tape": y,
            "block_intervals_steps": I,
            "phase_indices": np.asarray([0], dtype=int)}


def test_order_not_frequency():
    y = np.asarray([[0, 0, 1, 1]], dtype=np.int8)
    S, M, J, T = 2, 8, 1, 16
    I = np.asarray([[[0, 2], [2, 4], [4, 6], [6, 8]]], dtype=float)
    x = np.zeros((S, M, J, T), dtype=np.int8)
    a = [0, 0, 1, 1]
    b = [0, 1, 0, 1]
    for m in range(M):
        for k, v in enumerate(a): x[0, m, 0, 2*k:2*k+2] = v
        for k, v in enumerate(b): x[1, m, 0, 2*k:2*k+2] = v
    dynamic, _ = pf.context_source_evidence(x, y, I, [0])
    static = pf.frequency_source_evidence(x, y)
    assert dynamic[0] > dynamic[1]
    assert abs(static[0] - static[1]) < 1e-12


def test_phase_contract_is_explicit():
    y = np.asarray([[0, 1, 1, 0]], dtype=np.int8)
    c = _context("phase", y)
    try:
        pf.context_source_evidence(c["sim_occupancy"], c["observed_tape"],
                                   c["block_intervals_steps"], [])
    except ValueError:
        pass
    else:
        raise AssertionError("empty timing-derived phase set must be rejected")
    try:
        pf.context_source_evidence(c["sim_occupancy"], c["observed_tape"],
                                   c["block_intervals_steps"], [100])
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-support phase must be rejected")


def test_context_specific_member_marginalization():
    ys = [
        np.asarray([[0,0,1,1],[1,1,0,0]], dtype=np.int8),
        np.asarray([[0,1,1,1],[1,0,0,0]], dtype=np.int8),
        np.asarray([[0,0,0,1],[1,1,1,0]], dtype=np.int8),
    ]
    contexts = [_context("m4", ys[0], 4), _context("m5", ys[1], 5),
                _context("m6", ys[2], 6)]
    d = pf.loco_dynamic_diagnostic(contexts, np.asarray([0.5, 0.5]))
    assert d.transfer_pass


def test_semimarkov_null_is_finite_and_order_sensitive():
    train = [np.asarray([0,0,1,1,1,0,0,0], dtype=np.int8),
             np.asarray([1,1,0,0,1,1,0,0], dtype=np.int8)]
    h1 = [np.asarray([0,0,0,1,1,1,1,0], dtype=np.int8)]
    h2 = [np.asarray([0,1,0,1,0,1,0,1], dtype=np.int8)]
    s1 = pf.jeffreys_semimarkov_null_predictive(train, h1)
    s2 = pf.jeffreys_semimarkov_null_predictive(train, h2)
    assert np.isfinite(s1) and np.isfinite(s2)
    assert abs(s1 - s2) > 1e-9


def test_full_predictive_contract_and_permutations():
    patterns = [
        np.asarray([[0,0,1,1],[1,1,0,0]], dtype=np.int8),
        np.asarray([[0,1,1,1],[1,0,0,0]], dtype=np.int8),
        np.asarray([[0,0,0,1],[1,1,1,0]], dtype=np.int8),
        np.asarray([[0,1,0,1],[1,0,1,0]], dtype=np.int8),
    ]
    contexts = [_context(f"c{i}", y) for i, y in enumerate(patterns)]
    q0 = np.asarray([0.5, 0.5])
    d = pf.loco_dynamic_diagnostic(contexts, q0)
    assert d.core_predictive_pass and d.positive_transfer_contexts == 4
    assert all(f.absolute_gain > 0 for f in d.folds)
    d2 = pf.loco_dynamic_diagnostic(list(reversed(contexts)), q0)
    assert d2.core_predictive_pass
    assert sorted(round(f.source_transfer_gain, 12) for f in d.folds) == sorted(round(f.source_transfer_gain, 12) for f in d2.folds)
    c = contexts[0]
    perm = np.asarray([1, 0])
    e, _ = pf.context_source_evidence(c["sim_occupancy"], c["observed_tape"], c["block_intervals_steps"], c["phase_indices"])
    ep, _ = pf.context_source_evidence(c["sim_occupancy"][perm], c["observed_tape"], c["block_intervals_steps"], c["phase_indices"])
    assert np.allclose(e, ep[np.argsort(perm)])
    mperm = np.asarray([0,1,2,3,6,4,7,5])
    em, _ = pf.context_source_evidence(c["sim_occupancy"][:, mperm], c["observed_tape"], c["block_intervals_steps"], c["phase_indices"])
    assert np.allclose(e, em)


def test_member_loo_live():
    patterns = [
        np.asarray([[0,0,1,1],[1,1,0,0]], dtype=np.int8),
        np.asarray([[0,1,1,1],[1,0,0,0]], dtype=np.int8),
        np.asarray([[0,0,0,1],[1,1,1,0]], dtype=np.int8),
        np.asarray([[0,1,0,1],[1,0,1,0]], dtype=np.int8),
    ]
    contexts = [_context(f"c{i}", y) for i, y in enumerate(patterns)]
    result = pf.pf_dei_run_diagnostic(contexts, np.asarray([0.5, 0.5]))
    assert result["full"].core_predictive_pass
    assert result["member_loo_pass"] and result["pf_dei_pass"]


def main():
    test_order_not_frequency()
    test_phase_contract_is_explicit()
    test_context_specific_member_marginalization()
    test_semimarkov_null_is_finite_and_order_sensitive()
    test_full_predictive_contract_and_permutations()
    test_member_loo_live()
    print("PF_DEI_PHASE_MARGINAL_REFERENCE_SELFTEST PASS")


if __name__ == "__main__":
    main()
