# Source-to-Sensor Transfer 143-Candidate Gate — 2026-09-24

Decision: **NO_GO_143_CANDIDATE_TRANSFER_GATE**

## Corrected frozen timing

The C0.5 ten snapshots correspond to approximately:
55.0997, 85.0993, 115.0988, 142.2995, 167.3010,
192.3025, 217.3041, 242.3056, 267.3071, 292.3086 s.

All final ranks below use this corrected timing.

## Setup

- Train: S1-W1 A/B, S2-W1 A/B, S1-W2 A/B
- Holdout: S2-W2 A/B
- Two frozen House02 PMFS UAV navigation trajectories
- 142 frozen PMFS quadtree candidates + exact S2 reference
- Nearest real quadtree candidate: `quadtree_1_30_3_5`, 0.6708208 m from S2

## 143-candidate result

Exact S2 ranks, nav0-A / nav0-B / nav1-A / nav1-B:

### Linear transfer
- MSE: **3 / 22 / 19 / 25**
- temporal correlation: **4 / 3 / 11 / 9**

### Nonlinear transfer
- MSE: **3 / 38 / 7 / 24**
- temporal correlation: **9 / 5 / 3 / 4**

No all-four Top3 gate passes.

## Discrete path-action / Onsager-Machlup proxy

A source-blind AR(1) residual law was fitted on the same training combinations
only and used as a discrete path action on the 143 candidates.

### Linear mean model
- exact S2 action rank: **9 / 27 / 22 / 27**
- nearest-quadtree action rank: **20 / 26 / 1 / 16**

### Nonlinear mean model
- exact S2 action rank: **8 / 31 / 3 / 18**
- nearest-quadtree action rank: **1 / 29 / 2 / 12**

Decision: **NO_GO_OM_143_GATE**.

## Scientific interpretation

The earlier pairwise S1-vs-S2 signal was a necessary condition only.
It collapses in the many-source inverse problem.

The central limitation is now identifiable:
only two distinct training source locations are available, yet the model is asked
to identify a continuous two-dimensional source-to-sensor transfer law over 142
quadtree candidates. The source-coordinate dependence is underdetermined.

Observed failure modes:
- distant sources can have similar temporal shape;
- low-amplitude candidates can win MSE;
- temporal correlation is not spatially identifying;
- a generic residual path action does not restore identifiability.

## Stop rule

STOP:
- direct observation-space source-to-sensor regression;
- this Onsager-Machlup/AR residual-action implementation;
- closed-loop escalation from either signal.

Any next learned source-coordinate mechanism must be tested on a genuinely
multi-source intervention bank with held-out source positions and must face the
many-candidate rank gate early. Pairwise discrimination, field MSE, or cosine
are no longer sufficient evidence.
