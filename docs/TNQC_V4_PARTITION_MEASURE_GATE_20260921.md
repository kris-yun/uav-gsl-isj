# TNQC V4 partition-measure final-leaf gate
Date: 2026-09-21

> **Historical correction retained.** V4's terminal-leaf free-cell measure and
> exact cell-expansion equivalence remain part of the current method, but V5
> supersedes the V4 normalization of local-order support:
> `docs/TNQC_V5_SUPPORT_COVERAGE_GATE_20260921.md`.

V4 code checkpoint:
`725dae6de2f58b766bc309fd40a9c5722429fb8a`

V4 superseded the **gate measure** of V3. The main quotient representation,
claim boundary, final-leaf restriction, endpoint audits, and 300-s benchmark
remain unchanged.

No House01/02/03 300-s truth outcome was inspected before this correction.

## 1. Why V3 final-leaf-only was still incomplete

PMFS copies one terminal leaf score to every free source cell covered by that
leaf. A leaf covering 12 free cells therefore represents 12 cell-level source
hypotheses; a leaf covering one free cell represents one.

An unweighted concordance gives both leaves one vote. Because native PMFS
adaptively refines promising regions, an unweighted leaf gate can over-count
densely refined regions even after subdivided ancestors are removed.

The correction must therefore use the same source-space measure as the PMFS
terminal posterior.

## 2. V4 gate

Let the terminal active free leaves be `s_1,...,s_M`.

For each leaf:

- `a_i = q_aff(s_i)`;
- `o_i = q_ord(s_i)`;
- `m_i = number of free PMFS source cells represented by leaf i`.

For valid, non-tied leaf pairs define:

`C_cell = [sum_(i<j) m_i*m_j*sign(a_i-a_j)*sign(o_i-o_j)] /
          [sum_(i<j) m_i*m_j]`.

Then:

`g = max(0, C_cell)`

`e_i = g * a_i`.

Because one common non-negative `g` multiplies every terminal candidate,

`e_i - e_j = g*(a_i-a_j)`.

Thus the order auxiliary can attenuate or abstain but cannot reverse the
continuous quotient ordering.

## 3. Exact cell-expansion equivalence

The `m_i*m_j` factor is not a tuned hyperparameter.

Expand each leaf `i` into `m_i` identical copies, one per represented
free source cell, and compute ordinary unweighted concordance on that expanded
bank.

- copies from the same leaf tie in both channels and are ignored;
- leaves `i` and `j` generate exactly `m_i*m_j` cross-leaf pairs;
- every such cross-leaf pair has the same sign product.

Therefore the expanded cell-level statistic is **exactly equal** to the V4
measure-weighted leaf statistic.

C++ and Python tests both lock this equivalence.

## 4. Source-blind measure

The measure uses only occupancy geometry and the native terminal partition.

It does not use:

- source truth or truth distance;
- native score or posterior rank;
- TNQC score magnitude;
- House outcome;
- fitted parameters.

For an online terminal free quadtree leaf, C++ uses
`size.x * size.y`. A terminal node with `value==1` is homogeneous free
space, so this is its free-cell multiplicity.

The Python replay independently reconstructs the final partition and counts
the free cells owned by each terminal candidate ID.

## 5. Required replay scope

The authoritative replay must emit:

`candidate_gate_scope =
final_partition_leaf_candidates_free_cell_measure_weighted`

It additionally records two source-blind diagnostics that cannot control
inference:

1. terminal leaves with unit weights;
2. all evaluated candidates, including subdivided ancestors, with unit
   weights.

These show separately how much partition-density bias and ancestor
contamination would have changed the gate.

## 6. Unchanged method components

V4 does not alter:

- observed/predicted PMFS hit-logit fields;
- confidence/support masks;
- `q_aff`;
- local spatial-order `q_ord`;
- evidence bound `[-1,1]`;
- `L_PMFS * exp(e_i)`;
- native PMFS quadtree refinement;
- 300-s House benchmark;
- advancement thresholds.

It changes only the measure used by the shared auxiliary gate.

## 7. Authoritative 300-s run

Run:

```bash
python3 reference/test_tnqc_vgr_fixed_trajectory_replay.py
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

Every House/seed must pass:

- native posterior reconstruction;
- C++ endpoint anchor within 0.011 m;
- V4 partition-measure gate scope.

Only then evaluate the frozen development rule:

- pooled top-5% error reduction >= 10%;
- at least 4/6 paired cases improve;
- no pair degrades by more than 25%;
- no false-confident collapse.

An integrity-invalid replay writes its JSON and the runner continues through
the remaining frozen cases so the aggregate gives a complete six-case
diagnosis. Execution/file failures still abort.

No equation, measure, threshold, support rule, or candidate scope may be
changed after the six House truth outcomes are seen.

## 8. Closed-loop boundary

The fixed-trajectory replay tests inference on the native trajectory.

A later fused closed loop may additionally alter future motion through PMFS
posterior/planner state. Native within-update quadtree refinement remains
frozen. Those feedback effects are tested only after an explicit offline GO.

## 9. Status

**V4 PARTITION-MEASURE RESULT RETAINED / V5 SUPPORT-COVERAGE NORMALIZATION
AUTHORITATIVE / VGR 300-S REPLAY PENDING / CLOSED LOOP HOLD.**
