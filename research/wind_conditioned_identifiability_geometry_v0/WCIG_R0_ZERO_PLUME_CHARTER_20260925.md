# WCIG R0 — Wind-Conditioned Identifiability Geometry Audit

Date: 2026-09-25

Status: **ZERO-PLUME-SIMULATION PHYSICS AUDIT ONLY**

No GADEN plume generation is authorized.
No PMFS closed loop is authorized.

## 1. Question

Can physical wind variables available in a new environment predict how local source-pair distinguishability is reorganized across wind operators?

The target object is not a source-only invariant.

  D_E(s_i,s_j)

is explicitly conditioned on environment/operator E and the frozen observation protocol.

## 2. Existing discovery data

Use only already generated LSC cross-wind results:
- W0 = `3,5-1_slow`;
- W1 = `3,5-1_fast`;
- W2 = `4,5-3_slow`;
- the frozen 8-source / 10-edge panel;
- A/B split energy-distance values already committed.

W0/W1/W2 plume outcomes are discovery/postmortem data only.

## 3. Physical wind inputs

Read only existing canonical 3D wind files and occupancy metadata.

For each of the 10 frozen source edges and each wind iteration:
- use source z = 0.20 m;
- obtain the local 3D wind vector at both source endpoints and the edge midpoint using the repository's existing wind-grid coordinate mapping/interpolator;
- do not create a new interpolator if an existing validated reader is available;
- average endpoint/midpoint vectors only by the fixed rule below.

Primary local vector for an edge/iteration:

  u_e,k = (u(endpoint1)+2*u(midpoint)+u(endpoint2))/4.

Then average across the 11 canonical wind iterations:

  ubar_e = mean_k u_e,k.

## 4. Frozen primary physical features

Let d_hat be the unit 2D source-edge displacement.

Primary features:

1. along-edge mean wind magnitude:
   A_parallel = |d_hat dot ubar_xy|;

2. cross-edge mean wind magnitude:
   A_perp = |d_hat_x*ubar_y - d_hat_y*ubar_x|;

3. local mean horizontal speed:
   U = ||ubar_xy||.

Secondary diagnostics, not allowed to rescue the primary screen:
- across-iteration SD of A_parallel;
- across-iteration circular direction spread;
- local endpoint asymmetry in mean wind;
- vertical component magnitude.

No plume-derived feature may enter the physics predictor.

## 5. Existing-data diagnostic

Fit only simple preregistered models across the 30 edge×wind discovery cells.

Primary model:

  log(energy_distance) = b0 + b1 log(A_parallel + eps) + b2 log(A_perp + eps) + b3 log(U + eps).

eps is fixed to 1e-6 m/s.

Evaluation:
- leave-one-wind-out prediction for each of W0,W1,W2;
- Spearman between predicted and observed split-averaged edge energy within held-out wind;
- pooled Spearman over all 30 leave-one-wind-out predictions.

Also report a rank-only two-feature model using A_parallel/A_perp to ensure the conclusion is not a log-linear scaling artifact.

## 6. Physics-audit advance criterion

This is a discovery mechanistic audit, not confirmation.

Advance to a future fresh-wind prediction contract only if:
- pooled leave-one-wind-out Spearman >= 0.50;
- all three held-out-wind Spearman values are positive;
- the fitted model predicts the observed wind-family orientation reversal qualitatively;
- A/B split versions of the target energy geometry lead to the same qualitative conclusion.

Otherwise:

`WCIG_R0_FAIL_STOP_WIND_GEOMETRY_MAINLINE`.

No neural model may rescue a failure.

## 7. Untouched physical prediction wind

The remaining canonical House02 wind

`W3 = 4,5-3_fast`

is reserved as the next potential plume confirmation environment.

Its **wind field may be read now** because wind is a deployment-available covariate.

Its plume/source outcomes must not be generated or scored during WCIG R0.

After fitting only on W0/W1/W2, record before any W3 plume generation:
- predicted energy ranking for all 10 frozen edges;
- predicted three HARD edges;
- predicted three EASY edges;
- predicted x-edge versus y-edge mean ordering;
- predicted similarity of W3 geometry to W2 versus W0/W1.

## 8. Strong qualitative prediction already motivated by the postmortem

Because W3 and W2 are the same canonical `4,5-3` wind family at different speeds, WCIG should predict W3 source-identifiability geometry to resemble W2 more than the `3,5-1_*` family if wind-conditioned anisotropy is real.

This statement must be frozen before any W3 plume outcome exists.

## 9. Runtime/deployment requirement

A successful WCIG mechanism is only useful if all required covariates are obtainable from:
- occupancy/geometry;
- existing or measured/estimated local wind;
- UAV observation protocol.

No repeated known-source plume bank in the target environment is allowed as a runtime requirement.

## 10. After R0

PASS does not create a main innovation.

It only authorizes:
1. a power analysis for one untouched W3 plume confirmation;
2. later theory search for an environment-conditioned information-geometry formulation;
3. comparison to ordinary physics-based observability/identifiability baselines.

FAIL retires LSC/WCIG from the mainline.