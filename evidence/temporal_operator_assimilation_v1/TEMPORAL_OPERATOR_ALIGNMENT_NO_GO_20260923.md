# Temporal operator-alignment / data-assimilation pre-audit — authoritative R2

Date: 2026-09-23  
Status: **NO-GO for the proposed PMFS temporal-misalignment mechanism**

## Mother idea

NeurIPS 2025 FlowDAS argues that stochastic PDE systems benefit from stepwise data assimilation in which observations are incorporated consistently with the evolving dynamics rather than only through a one-shot reconstruction. This suggests a concrete PMFS failure hypothesis: the measured probability map accumulates historical information, whereas a source update compares that accumulated evidence with a forward field generated under the current operator state.

Before training a stochastic-interpolant data-assimilation model, this pre-audit asks whether **temporally matching evidence increments to the contemporaneous PMFS forward operator** improves true-source identity.

## Frozen test

All six authoritative R2 House x seed runs, source updates 1–5.

- use authoritative final-partition leaf candidates;
- use cells with positive confidence in all five updates (126–140 per run), permitting exact operator-time permutation controls;
- anchor each final source hypothesis by its Native sampled source point and map it to the finest candidate region at each update;
- confidence is monotone on this common support in all six runs;
- decompose confidence into nonnegative increments: update 1 uses c1 and later updates use c_u-c_(u-1);
- each confidence increment is compared with the measured probability and candidate forward probability from the **same** update using a Native-style factor `1 - delta_c * |p-q|`;
- sum log factors over update x cell to obtain the time-aligned score.

Controls:
1. **fixed-final-operator sequential**: the same evidence increments, but use update-5 forward probabilities at every update;
2. authoritative Native final-leaf score.

### Exact destructive null

Enumerate all 5! = 120 permutations of the five forward-operator time labels while preserving all measured evidence, all simulated values, and every candidate identity. Only temporal alignment is changed.

A temporal-alignment mechanism requires the identity ordering to be unusually favorable for the true source (p <= 0.05).

## Results

| run | N | Native final | fixed final operator | time-aligned | exact permutation p |
|---|---:|---:|---:|---:|---:|
| House01 seed0 | 123 | 68.0 | 60.5 | 66.0 | 0.8500 |
| House01 seed1 | 121 | 61.0 | 76.0 | 79.5 | 0.8833 |
| House02 seed0 | 123 | 62.0 | 84.0 | 81.0 | 0.2833 |
| House02 seed1 | 119 | 60.0 | 95.0 | 97.0 | 0.6333 |
| House03 seed0 | 160 | 80.5 | 89.0 | 154.0 | 1.0000 |
| House03 seed1 | 160 | 80.5 | 92.0 | 88.0 | 0.0833 |

Summary:
- time-aligned beats fixed-final sequential control: **2/6**;
- time-aligned beats authoritative Native final-leaf rank: **1/6**;
- exact temporal-permutation gate: **0/6**.

## Verdict

The current evidence does not support temporal operator mismatch as the load-bearing cause of PMFS source-identity failure. Correct update ordering is not privileged under the exact permutation null, and one House03 run is strongly worsened.

Therefore do not advance directly to a FlowDAS/DAISI-style learned stochastic-interpolant assimilation model on the basis of this mechanism. A future data-assimilation route would need a genuinely new latent state observable or richer raw temporal field data, not merely sequentially reweighting the existing PMFS update snapshots.

Machine-readable results: `TEMPORAL_OPERATOR_ALIGNMENT_PREAUDIT_R2.csv`.
