# Zero-Simulation Wind-Anisotropy Audit — Post-LSC Cross-Wind Failure

Date: 2026-09-25

Status: **DIAGNOSTIC ONLY; NO LSC RESCUE; NO NEW PLUME RUNS**

Frozen LSC decision remains FAIL.

## Question

Did the W2 failure occur because source distinguishability is anisotropic relative to the physical transport direction, so changing wind topology rotates/deforms the local inverse-identifiability geometry?

## Existing evidence motivating the audit

On the frozen 2x4 source panel, post-hoc A/B averages show:

W0 `3,5-1_slow`:
- x-edge energy ~13.05, error ~0.0625;
- y-edge energy ~6.56, error ~0.3125.

W1 `3,5-1_fast`:
- x-edge energy ~12.49, error ~0.1458;
- y-edge energy ~7.27, error ~0.4063.

W2 `4,5-3_slow`:
- x-edge energy ~11.52, error ~0.3542;
- y-edge energy ~11.77, error ~0.1563.

Frozen inventory global speed-weighted directions are approximately:
- W0 -120.9 deg;
- W1 -118.5 deg;
- W2 +159.6 deg.

This is consistent with a rotation of which source-offset direction is more transverse/longitudinal to transport, but global wind summaries are insufficient to establish the mechanism.

## Data to read

Use only the already existing canonical House02 wind files for:
- W0 `3,5-1_slow`;
- W1 `3,5-1_fast`;
- W2 `4,5-3_slow`.

No GADEN plume simulation.
No additional seed.
No modification to LSC scores.

## Frozen local wind descriptor

For each wind and each of the ten frozen source-neighbor edges:

1. identify the two source-cell centers from `LSC_CROSSWIND_D0_SOURCE_PANEL.tsv`;
2. sample/interpolate the horizontal 3D GADEN wind vector at source height z=0.20 m for both endpoints for all 11 wind iterations;
3. average the two endpoint horizontal vectors within iteration, then average across the 11 iterations;
4. let delta_s be the unit source-pair displacement;
5. let u_hat be the normalized mean local horizontal wind;
6. define longitudinality

   L = |delta_s dot u_hat|,

and transversality

   T = sqrt(1-L^2).

Also report local mean speed, but do not tune or combine descriptors.

## Predeclared diagnostic predictions

If wind-aligned anisotropy explains the topology change:

1. W0/W1 should have similar local edge transversality patterns;
2. W2 should rotate/reorder those patterns;
3. across wind×edge units, higher T should be associated with lower fresh pair confusion;
4. the sign of x-vs-y hard/easy orientation should match the local-wind descriptor;
5. speed alone should not explain the orientation flip.

Primary descriptive endpoint:
- Spearman(T, A/B-averaged fresh pair error) across the 30 wind×edge units.

Secondary:
- Spearman(T, A/B-averaged energy distance);
- wind-wise x/y means;
- W0-W1 and W0/W2 transversality-order correlation.

## Interpretation

PASS_DIAGNOSTIC:
the local wind descriptor predicts the observed hard/easy orientation and materially explains the W2 rotation.

HOLD_DIAGNOSTIC:
sign is consistent but small panel prevents a stable conclusion.

FAIL_DIAGNOSTIC:
local wind-relative orientation does not explain the cross-wind reorder.

No result changes the frozen LSC FAIL.

## Mainline consequence if diagnostic passes

The next scientific object is not an invariant LSC graph.

It is an environment-conditioned inverse geometry:

  d_E(s_i,s_j) = D(P(Y|s_i,E,M), P(Y|s_j,E,M)),

or a local metric/contrast operator that must be predicted from E.

Any future mainline must include operator variation at its first discovery gate.