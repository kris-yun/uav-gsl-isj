# Pseudo-Markovian Probability-Flow GSL v1 — Frozen Pre-Data Charter

Date: 2026-09-24
Branch: `research/pseudo-markovian-probflow-v1`
Status: **CANDIDATE — MULTI-SOURCE RANK GATE REQUIRED BEFORE ANY CLOSED LOOP**

## Why this branch exists

The 143-candidate gate killed:
- direct source-to-sensor regression;
- a discrete Onsager-Machlup / AR residual-action score.

Corrected-time exact-S2 ranks were poor and unstable across two UAV paths and A/B plume realizations.

The central data limitation is now explicit:

> only two distinct source locations (S1,S2) were available for learning a continuous 2-D source-location dependence over 142 PMFS candidates.

Pairwise S1-vs-S2 discrimination was therefore an underpowered necessary condition, not evidence of source identifiability.

## Scientific parent idea

Primary top-journal parent:
- **Data-driven Mori-Zwanzig modeling of Lagrangian particle dynamics in turbulent flows**, PNAS, 2026, DOI 10.1073/pnas.2525390123.

Newest reduction mechanism being tested:
- **Surrogate Trajectories Along Probability Flows: Pseudo Markovian Alternative to Mori Zwanzig**, 2026, arXiv:2601.00015.

Core idea:
high-dimensional stochastic plume dynamics are projected onto resolved UAV observables, but instead of using an explicit history kernel, construct a time-dependent conditional drift/diffusion whose surrogate trajectories preserve the resolved marginal probability flow.

This project must NOT claim Mori-Zwanzig, probability-flow reduction, Green functions, or backward transport themselves as novel.

Target novelty, only if the gate passes:

> candidate-conditioned pseudo-Markovian probability-flow closure for turbulent gas source localization, producing a PMFS-style source probability map directly from causal sparse UAV observations.

## Prior-art boundaries

Occupied:
- Poisson/Green-function sparse GSL: EUSIPCO 2024, DOI 10.23919/EUSIPCO63174.2024.10715286.
- learned backward/Schrodinger-bridge chemical source localization: arXiv:2607.26892.

Therefore this branch is NOT a generic Green-function or backward-transport proposal.

## Minimal source-position intervention bank

Use the frozen 142-candidate House02 PMFS manifest.

Existing training anchors:
- S1 = (-2.242730141, -2.200880051)
- S2 = (-4.342730045,  2.899120331)

Additional candidates selected source-blind by farthest-point sampling from the 142 PMFS centers, with S1/S2 as initial anchors:

1. F1 train: `quadtree_24_35_3_1` = ( 2.2572698593,  3.1991205215)
2. F2 holdout: `quadtree_25_14_2_1` = ( 2.5572700500, -3.1008796692)
3. F3 train: `quadtree_1_1_5_4`   = (-4.3427300453, -6.4008798599)
4. F4 holdout: `quadtree_15_6_2_3` = (-0.4427299500, -5.2008800507)
5. F5 train: `quadtree_16_25_5_2` = ( 0.1572699547,  0.4991202354)
6. F6 holdout: `quadtree_14_35_5_1` = (-0.4427299500,  3.1991205215)

New GADEN cells required:
- 6 new source positions
- W1/W2
- plume realizations A/B
- total 24 new realizations

Training source positions:
S1, S2, F1, F3, F5.

Never used for tuning:
F2, F4, F6.

## Observation paths

Do NOT reuse a source-conditioned PMFS closed-loop path for the decisive held-out-source gate.

Before opening any held-out concentration output, generate and freeze two occupancy-only, source-blind single-UAV coverage trajectories.

They may use only:
- occupancy/free space;
- UAV motion constraints;
- fixed random seed if needed.

They may NOT use:
- gas;
- source;
- holdout plume;
- oracle wind.

## Primary gate

For each held-out source F2/F4/F6, evaluate:
- W1/W2;
- A/B;
- both frozen source-blind UAV paths.

Total: 24 held-out ranking cases.

Candidate set in every case:
the same frozen 142 PMFS quadtree candidates.

Primary endpoint:
**truth-source candidate rank**.

PASS requires, before any closed-loop work:
- truth candidate Top3 in all 24 cases;
- rank-1 in at least 18/24 cases (75%);
- median truth rank = 1;
- clear improvement over the frozen direct-transfer baseline;
- no parameter or architecture choice made from F2/F4/F6 outcomes.

FAIL:
**STOP_PSEUDO_MARKOVIAN_PROBFLOW_MAINLINE**.

## Secondary mechanism checks

Only if the primary rank gate passes:
- calibrated observation marginal likelihood;
- temporal probability-flow consistency;
- source-label permutation destroys the gain;
- estimated-wind rather than oracle-wind deployment path;
- computation scales to batched PMFS candidates.

Field MSE is not a pass criterion.

## Stop rule

Do not:
- return to M4 field corrections;
- report pairwise source classification as evidence;
- use S2-only navigation for held-out-source confirmation;
- enter ROS/closed loop before the 24-case many-source rank gate passes.
