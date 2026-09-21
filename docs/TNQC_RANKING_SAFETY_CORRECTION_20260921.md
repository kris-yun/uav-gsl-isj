# TNQC ranking-safety correction — 2026-09-21

> **Historical correction retained for rationale.** The non-reversal idea in
> this document remains valid, but its unweighted candidate-bank measure is
> superseded by `docs/TNQC_V4_PARTITION_MEASURE_GATE_20260921.md`.
> V4 applies the same shared non-negative gate only to terminal active leaves
> and weights leaf pairs by represented free-cell measure.

## Why this correction exists

A code audit found a real flaw in the first auxiliary fusion rule.

The main TNQC affine quotient was not affected. The flaw was in the secondary
rule that attempted to let the local spatial-order quotient corroborate the
affine quotient only when both candidate-local scores had the same sign.

That condition is insufficient. Two candidates can both keep the same score
sign while their **relative order is reversed** after averaging. For example,

```
candidate A: q_aff=0.51, q_ord=0.01
candidate B: q_aff=0.50, q_ord=1.00
```

The affine channel ranks A>B, but naive 1:1 averaging gives 0.26 versus 0.75
and ranks B>A. A per-candidate sign check does not detect this.

Therefore the old per-candidate symmetry-hierarchy guard is rejected and must
not be used in the 300-s gate or closed loop.

## Corrected secondary mechanism

For one source-update candidate bank, let

[
a_i=q_{\mathrm{aff}}(s_i),\qquad
o_i=q_{\mathrm{ord}}(s_i).
]

For valid, non-tied candidate pairs define

[
C_u =
\frac{1}{|\mathcal P_u|}
\sum_{(i,j)\in\mathcal P_u}
\operatorname{sgn}(a_i-a_j)
\operatorname{sgn}(o_i-o_j).
]

The single bank-level corroboration strength is

[
g_u=\max(0,C_u),
]

and TNQC evidence is

[
e_i=g_u a_i.
]

The online fused likelihood is

[
L_{\mathrm{TNQC}}(s_i)
=L_{\mathrm{PMFS}}(s_i)\exp(e_i).
]

No source truth, posterior rank, fitted coefficient, threshold, or candidate
identifier is used in the gate.

### Ordering guarantee

For any two candidates (i,j),

[
e_i-e_j=g_u(a_i-a_j).
]

Because (g_u\ge0),

- if (g_u>0), the TNQC evidence has exactly the same candidate ordering as
  the affine quotient;
- if (g_u=0), all auxiliary evidence is neutral and TNQC abstains;
- the local-order channel can therefore attenuate or abstain, but cannot
  reverse the affine ordering.

This is the guarantee the rejected per-candidate guard did not have.

## Native candidate-bank freeze

The online implementation now deliberately keeps PMFS quadtree refinement
native within each source update:

1. PMFS evaluates/refines candidates with its historical native likelihood;
2. every native-evaluated candidate is collected;
3. after native refinement finishes, one bank concordance gate is computed
   over that complete evaluated bank;
4. the final native partition is reweighted by (e_i=g_u a_i);
5. the resulting posterior can affect subsequent movement, but TNQC does not
   choose the candidate bank on which its own evidence is computed.

This makes the online equation match the fixed-trajectory 300-s replay and
prevents self-selection of TNQC evidence.

## VGR project-data mechanism result after correction

Data:
- project branch commit
  `26e89a99532e4268c5022dca2e938bf1473377b1`;
- H01/H02/H03 x SA/SB x fast/slow;
- 12 fixed-route VGR/GADEN histories;
- 1200 samples per history to 240 s;
- gas observations binned on the actual reduced PMFS 0.3-m grid.

At 240 s:
- raw cross-transport source identity: 12/12;
- affine quotient: 12/12;
- local spatial order: 11/12;
- rejected unconditional equal fusion: 11/12;
- corrected bank gate: releases 11/12 and is **11/11 correct when released**.

The single abstention is H02/fast/SA:

[
q_{\rm aff}(SA)=-0.0214193940,quad
q_{\rm aff}(SB)=-0.0382141014,
]

so affine correctly prefers SA, while

[
q_{\rm ord}(SA)=0.757575758,quad
q_{\rm ord}(SB)=0.878787879
]

orders the candidates oppositely. Hence (C_u=-1), (g_u=0), and the
secondary mechanism abstains instead of overturning the exact quotient.

Source-blind stress:
- 100 independent positive-scale stress seeds: coverage 11/12 in every run,
  conditional accuracy 100% in every run;
- 200 independent monotone-compression stress seeds: coverage 11/12 in every
  run, conditional accuracy 100% in every run.

Frozen evidence:
`evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json`.

## Implementation locations

- `ros2_package/src/gsl_server/algorithms/PMFS/internal/TNQCScore.hpp`
  - `candidateOrderConcordance`
  - `bankEvidence`
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp`
  - complete native candidate-bank freeze
  - post-refinement bank gate application
- `reference/tnqc_vgr_fixed_trajectory_replay.py`
  - same bank-level equation
- `ros2_package/test/test_tnqc_score.cpp`
  - explicit candidate-order reversal counterexample
- `reference/test_tnqc_vgr_fixed_trajectory_replay.py`
  - Python parity counterexample

## Claim boundary

This correction establishes:
- exact main-quotient invariance at the score level;
- a mathematically ranking-safe secondary corroboration/abstention mechanism;
- positive VGR 240-s mechanism evidence.

It does **not** establish improvement of final source localization at 300 s.

The authoritative next decision remains:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

on the VGR VM for House01/02/03 x seed0/1 under the full 300-s benchmark.
Closed loop remains HOLD until that gate reports `go_for_closed_loop=true`.
