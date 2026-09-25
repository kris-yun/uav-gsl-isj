# DASN 0J — Neighbor-Jacobian Specificity Test and Decision

Date: 2026-09-25

Decision: **HOLD_SHARED_ERROR_NOT_SOURCE_SPECIFIC**

## Purpose

0H showed a strong same-realization pseudo-displacement signal when fresh plume residuals were projected through the source's training-half local response Jacobian J_s.

0I showed the correct J_s was stronger than most randomly reassigned source Jacobians, but the null had a broad upper tail.

0J asks a stricter question:

> Is the correct source Jacobian meaningfully better than the Jacobian of an immediately adjacent source cell?

This preserves local spatial smoothness, sensitivity scale and nearby transport structure.

## Test

For each source with an available neighbor in one of four PMFS grid directions, compare:

- actual: use J_s for that source's residual;
- neighbor mismatch: use J_neighbor for the same residual.

Odd/even views use the corresponding Jacobian from the same neighboring source.

No source is removed from the overall mechanism evidence; each directional comparison uses only sources for which that specific neighbor exists.

## Direction A

Train reps 1-8; diagnose reps 9-16.

+x neighbor:
- actual mean T_J = 0.24957;
- neighbor-J mean = 0.20962;
- delta = +0.03995;
- fraction source-wise actual > neighbor = 0.522.

-x neighbor:
- actual = 0.22895;
- neighbor = 0.25405;
- delta = -0.02510;
- fraction actual > neighbor = 0.460.

+y neighbor:
- actual = 0.26650;
- neighbor = 0.34861;
- delta = -0.08210;
- fraction actual > neighbor = 0.569.

-y neighbor:
- actual = 0.22780;
- neighbor = 0.25152;
- delta = -0.02372;
- fraction actual > neighbor = 0.493.

## Direction B

Train reps 9-16; diagnose reps 1-8.

+x:
- actual = 0.50177;
- neighbor = 0.43440;
- delta = +0.06737;
- fraction actual > neighbor = 0.503.

-x:
- actual = 0.50852;
- neighbor = 0.58991;
- delta = -0.08138;
- fraction actual > neighbor = 0.522.

+y:
- actual = 0.57390;
- neighbor = 0.57144;
- delta = +0.00245;
- fraction actual > neighbor = 0.528.

-y:
- actual = 0.52783;
- neighbor = 0.47060;
- delta = +0.05724;
- fraction actual > neighbor = 0.500.

## Interpretation

The source's exact local Jacobian is not consistently superior to a neighboring source Jacobian.

Therefore the data support a **locally smooth shared transport/error geometry**, not a uniquely source-specific 0.30 m displacement-aligned noise mechanism.

The strong 0H pseudo-displacement result is real as a projection phenomenon, but it is not specific enough to justify:
- information-limiting correlation;
- a source-displacement latent Q;
- a new covariance likelihood;
- a PASI-like non-diagonal rescue.

## What remains established

Across the full DASN screen:
- two disjoint probe views both localize;
- same-realization shared localization error is reproducible;
- pairing destruction removes it;
- common gain does not explain it;
- an equal-dimensional generic 2D factor does not fully explain it;
- it replicates across two readout families;
- it is not boundary dominated;
- local Jacobian projection produces strongly aligned pseudo-displacements;
- but neighboring Jacobians work comparably well.

## Decision boundary

This matches the preregistered HOLD case:

> reproducible shared error exists, but displacement alignment / residual non-identifiability cannot be separated.

No new likelihood, final target or closed-loop experiment is authorized from DASN.

Possible reusable scientific clue:

> the harmful stochastic component may be a coherent, spatially smooth transport deformation / plume-meandering mode rather than source-specific displacement noise.

Testing that stronger fluid-mechanistic interpretation would require a separate mechanism card; it must not be inferred from the present 30-probe data alone.