#!/usr/bin/env python3
"""Deterministic scientific-contract selftest for CG-PC-CTT V5."""
from __future__ import annotations
import numpy as np

import v4_final_reference as v4
import v5_active_sequential_reference as v5


def fixture():
    S, M, J = 4, 8, 6
    rect = np.asarray([
        [0, 0, 1, 1], [1, 0, 1, 1], [2, 0, 1, 1], [3, 0, 1, 1]
    ], dtype=np.int64)
    q0 = np.ones(S, dtype=float) / S
    r = np.asarray([1, 0, 1, 0, 1, 0], dtype=float)
    ctx = np.asarray(["c1", "c1", "c2", "c2", "c3", "c3"], dtype=object)
    p = np.empty((S, M, J), dtype=float)
    for s in range(S):
        base = (np.asarray([.90, .10, .90, .10, .90, .10])
                if s < 2 else
                np.asarray([.10, .90, .10, .90, .10, .90]))
        for m in range(M):
            p[s, m] = np.clip(base + (m - 3.5) * .002, .01, .99)
    return p, r, ctx, rect, q0


def same_partition(a, b):
    a = np.asarray(a); b = np.asarray(b)
    return np.array_equal(a[:, None] == a[None, :], b[:, None] == b[None, :])


def main():
    p, r, ctx, rect, q0 = fixture()
    build = v4.build_components(p, rect, 200)
    assert len(np.unique(build.labels)) == 2

    d = v5.context_blocked_m2(p, r, ctx, build.labels, q0, 200)
    assert d.accepted and d.reason == "ACCEPT"
    assert d.effective_contexts == 3 and d.unique_stops == 6
    assert d.informative_contexts == 3
    assert np.min(d.heldout_absolute_gain) > 0
    assert np.min(d.heldout_rival_margin) > 0

    # A contradictory third context must not be averaged away.
    r_bad = np.asarray([1, 0, 1, 0, 0, 1], dtype=float)
    bad = v5.context_blocked_m2(p, r_bad, ctx, build.labels, q0, 200)
    assert not bad.accepted
    assert bad.reason in {"CONTEXT_LOO_COMPONENT_DISAGREE", "HELDOUT_CONTEXT_RIVAL_CONTRADICTION"}

    # The old common-bias counterexample remains blocked by the absolute null.
    p_null = np.empty_like(p)
    p_null[:2, :, :] = .01
    p_null[2:, :, :] = .005
    all_hit = np.ones(6, dtype=float)
    null_dec = v5.context_blocked_m2(p_null, all_hit, ctx, np.asarray([0,0,1,1]), q0, 200)
    assert not null_dec.accepted
    assert null_dec.reason == "HELDOUT_CONTEXT_ABSOLUTE_NULL_FAIL"

    # State is cumulative but one spatial stop can enter evidence only once.
    st = v5.initialize_state(q0)
    st, a1 = v5.append_context(st, p[:, :, :2], r[:2], ["cell10", "cell11"], "c1")
    st, a2 = v5.append_context(st, p[:, :, 2:4], r[2:4], ["cell11", "cell12"], "c2")
    assert a1.tolist() == [True, True]
    assert a2.tolist() == [False, True]
    assert st.stop_key == ["cell10", "cell11", "cell12"]

    # A duplicate cell inside one incoming context is ignored rather than counted twice.
    st2 = v5.initialize_state(q0)
    st2, a_same = v5.append_context(
        st2, p[:, :, :2], r[:2], ["cell10", "cell10"], "same_context"
    )
    assert a_same.tolist() == [True, False]
    assert st2.stop_key == ["cell10"]

    # Candidate/source permutation cannot change the scientific decision.
    rng = np.random.default_rng(20260828)
    perm = rng.permutation(len(q0)); inv = np.argsort(perm)
    pb = v4.build_components(p[perm], rect[perm], 200)
    pd = v5.context_blocked_m2(p[perm], r, ctx, pb.labels, q0[perm], 200)
    assert same_partition(build.labels, pb.labels[inv])
    assert pd.accepted == d.accepted and pd.reason == d.reason
    assert np.array_equal(pd.selected_mask[inv], d.selected_mask)

    # Scoring-member permutation preserves the verdict.
    mp = np.asarray([0,1,2,3,6,4,7,5])
    mb = v4.build_components(p[:, mp], rect, 200)
    md = v5.context_blocked_m2(p[:, mp], r, ctx, mb.labels, q0, 200)
    assert md.accepted == d.accepted and md.reason == d.reason
    assert np.array_equal(md.selected_mask, d.selected_mask)

    # Recomputing q_causal from the same full ledger is idempotent: no old
    # evidence is multiplied a second time on later source updates.
    qc1, inc1 = v5.causal_posterior_from_ledger(q0, p, r, d.selected_mask, 200)
    qc2, inc2 = v5.causal_posterior_from_ledger(q0, p, r, d.selected_mask, 200)
    assert np.allclose(qc1, qc2, atol=0, rtol=0)
    assert inc1 == inc2

    # Active probe: cell 11 maximally separates the two components for every
    # scoring member; cell 10 is non-informative.
    X = 3
    cand = np.empty((4, 8, X), dtype=float)
    for s in range(4):
        for m in range(8):
            cand[s, m] = ([.5, .9, .8] if s < 2 else [.5, .1, .2])
    cell = np.asarray([10, 11, 12], dtype=np.int64)
    feasible = np.ones(X, dtype=bool)
    unvisited = np.zeros(X, dtype=bool)
    probe = v5.robust_probe_utility(
        cand, np.asarray([0,0,1,1]), q0, cell, feasible, unvisited
    )
    assert probe.available and probe.chosen_cell_id == 11
    assert probe.robust_information_gain > 0

    # Candidate-order permutation and visited exclusion have deterministic semantics.
    xp = np.asarray([2,0,1])
    probe_perm = v5.robust_probe_utility(
        cand[:, :, xp], np.asarray([0,0,1,1]), q0, cell[xp],
        feasible=np.ones(X, dtype=bool), visited=np.zeros(X, dtype=bool)
    )
    assert probe_perm.chosen_cell_id == 11
    visited = cell == 11
    probe2 = v5.robust_probe_utility(
        cand, np.asarray([0,0,1,1]), q0, cell, feasible, visited
    )
    assert probe2.available and probe2.chosen_cell_id == 12

    # Planner override is allowed only for strict robust-information dominance.
    override = v5.robust_probe_override(
        cand, np.asarray([0,0,1,1]), q0, cell, feasible, unvisited,
        native_chosen_index=0
    )
    assert override.available and override.chosen_cell_id == 11
    no_override = v5.robust_probe_override(
        cand, np.asarray([0,0,1,1]), q0, cell, feasible, unvisited,
        native_chosen_index=1
    )
    assert not no_override.available
    assert no_override.reason == "NO_STRICT_INFORMATION_GAIN_OVER_NATIVE"

    print("V5_ACTIVE_SEQUENTIAL_REFERENCE_SCIENCE_CONTRACT PASS")


if __name__ == "__main__":
    main()
