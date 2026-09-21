# TNQC V4 partition-measure gate correction
Date: 2026-09-21

Authoritative code freeze for this correction:
`725dae6de2f58b766bc309fd40a9c5722429fb8a`

This document supersedes the **gate measure** in
`docs/TNQC_V3_FINAL_LEAF_FREEZE_20260921.md`. V3 correctly removed
subdivided ancestors, but a second audit found that equal weighting of
terminal leaves still makes the gate depend on adaptive quadtree partition
density.

No House01/02/03 300-s truth result was inspected before this correction.

## 1. Remaining V3 problem

PMFS assigns one terminal leaf score to every free source cell covered by that
leaf. A leaf containing 12 free cells therefore carries 12 times the
cell-level hypothesis measure of a leaf containing one free cell.

An unweighted leaf concordance nevertheless gives both leaves one vote.
Native PMFS refinement can split a promising region into many small leaves,
so an unweighted gate can over-represent highly refined regions even after
subdivided ancestors have been removed.

This is not a source-truth issue; it is a mismatch between the gate's measure
and the posterior's source-space measure.

## 2. V4 definition

Let the terminal active free leaves be
(mathcal B_u^{m leaf}={s_1,ldots,s_M}).

For leaf (i), let

[
m_i = |{	ext{free PMFS source cells represented by leaf }i}|.
]

For its two quotient channels write

[
a_i=q_{m aff}(s_i),qquad o_i=q_{m ord}(s_i).
]

Over valid non-tied leaf pairs,

[
C_u^{m cell}
=
rac{
sum_{i<j}m_i m_j,
operatorname{sgn}(a_i-a_j)
operatorname{sgn}(o_i-o_j)}
{
sum_{i<j}m_i m_j
}.
]

The frozen evidence remains

[
g_u=max(0,C_u^{m cell}),
qquad
e_i=g_u a_i.
]

The same non-negative (g_u) is still shared by the entire terminal bank, so
the ranking-safety guarantee is unchanged:

[
e_i-e_j=g_u(a_i-a_j).
]

Local order can attenuate or abstain; it cannot reverse the main affine
quotient ordering.

## 3. Exact replication equivalence

The measure weighting has a direct interpretation and is not an arbitrary
hyperparameter.

Imagine expanding each leaf (i) into (m_i) identical copies, one for every
free source cell it represents. Compute ordinary unweighted candidate-order
concordance on that expanded cell-level bank.

Pairs between copies of the same leaf have equal (a) and (o), hence are
ties and are ignored. Between leaves (i) and (j), there are exactly
(m_i m_j) cross-leaf pairs, all with the same sign product.

Therefore the expanded-bank numerator and denominator are exactly

[
sum_{i<j}m_i m_j,
operatorname{sgn}(a_i-a_j)operatorname{sgn}(o_i-o_j)
]

and

[
sum_{i<j}m_i m_j,
]

respectively. Thus

[
C_{m expanded}=C_u^{m cell}.
]

Both the C++ and Python standalone tests now lock this equivalence.

## 4. Source-blindness

The V4 measure uses only occupancy geometry and the already frozen terminal
partition.

It does not use:

- source truth;
- distance to truth;
- posterior rank;
- TNQC score magnitude;
- native score magnitude;
- House outcome;
- fitted coefficients.

For an online terminal free quadtree leaf, the C++ measure is
`size.x * size.y`. Such a leaf is homogeneous free space
(`value==1`), so this equals its represented free-cell count.

The Python replay reconstructs the final partition and counts exactly how many
free cells map to each terminal candidate ID.

## 5. Audits retained in the 300-s replay

The authoritative gate is now:

`candidate_gate_scope =
final_partition_leaf_candidates_free_cell_measure_weighted`

The replay additionally reports, but does not use for inference:

1. the same terminal leaves with **unit** leaf weights;
2. the old gate over **all evaluated candidates** including search history.

This exposes how much either partition density or ancestor contamination would
have changed (g_u), without using source truth.

## 6. Unchanged main method

V4 does not change:

- the canonical hit-logit representation;
- (q_{m aff});
- local spatial-order (q_{m ord});
- the evidence bound ([-1,1]);
- the exponential tilt (L_{m PMFS}exp(e_i));
- PMFS native quadtree refinement;
- support/confidence rules;
- 300-s endpoint;
- House/seed set;
- advancement thresholds.

It only makes the shared auxiliary gate use the same source-space measure as
the terminal PMFS posterior.

## 7. 300-s gate

The command remains:

```bash
python3 reference/test_tnqc_vgr_fixed_trajectory_replay.py
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

For every House/seed, the case is valid only when:

- native posterior reconstruction passes;
- reconstructed Python native top-5% error agrees with the C++ PMFS terminal
  `RESULT IS: Error=` within the frozen 0.011 m rounding tolerance;
- the replay declares the V4 partition-measure final-leaf gate scope.

The six-case development GO rule remains:

- pooled error reduction >= 10%;
- >= 4/6 paired improvements;
- worst pair degradation <= 25%;
- no false-confident collapse.

Integrity-invalid cases are still run to completion so the aggregate contains
all six diagnostics; execution/file failures still abort.

## 8. Claim boundary inherited from V3

The exact quotient theorem remains conditional on fixed support/weights and
positive-affine actions on the supported PMFS **hit-logit fields**.

The archived 240-s `gas_ppm` screens remain concentration-space mechanism
evidence only. They are not a substitute for the V4 online-representation
300-s replay.

## 9. Status

**TNQC V4 METHOD FROZEN BEFORE 300-S TRUTH / PARTITION-MEASURE GATE
IMPLEMENTED / AUTHORITATIVE VGR 300-S REPLAY PENDING / CLOSED LOOP HOLD.**
