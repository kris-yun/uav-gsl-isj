# NPG-G0 — Task-Relevant Neural Population Geometry Falsification Gate

Date: 2026-09-25

Status: **NEW MAINLINE CANDIDATE / ZERO-PLUME / REFERENCE-ONLY MECHANISM TEST**

Upstream frozen fact:
`JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL` remains final.

This is NOT a JTD rescue.

## 1. Mother-theory anchors

Primary normative anchor:
- Wakhloo, Slatton & Chung, Nature Neuroscience 2026, `Neural population geometry and optimal coding of tasks with shared latent structure`.
- The theory links representation geometry and finite training-sample budget to downstream readout generalization.

Biological/olfactory bridge:
- Hu et al., Nature Neuroscience 2026, `Representational learning by optimization of neural manifolds in an olfactory memory network`.
- In an odor-discrimination task, task-relevant manifold geometry and manifold capacity are linked to discriminability.

Prior-art boundary:
- generic manifold learning/UMAP already appears in 2026 odor-source-localization work; therefore novelty cannot be `use manifold learning`.

## 2. New scientific hypothesis

For a fixed observation context, whether a cross-time interaction code helps source localization is determined by TASK-RELEVANT representation geometry and finite-reference estimation burden, not by total correlation strength alone.

Operationally:

> geometry computed from reference observations only should predict, before seeing held-out realizations, whether adding cross-time interaction features will improve or hurt discrimination of a local source pair.

The prediction must beat ordinary inner cross-validation and simple correlation/variance descriptors.

If it cannot, this mother-theory candidate loses main-innovation eligibility.

## 3. Data scope

Use only the already-open House02 `3,5-1_slow` dense bank:
- 168 sources;
- 16 independent realizations/source;
- frozen 10x30 observation contract.

0 new plume.
Do NOT use E2 fresh-target outcomes as training or gate data.
Do NOT read H01 DEV or House03.

## 4. Frozen source-pair units

The 168 sources form a 24 x 7 grid strip.

Primary units are 84 disjoint 0.3 m horizontal nearest-neighbor pairs:
- within each y row;
- x columns paired as (1,2), (3,4), ..., (23,24);
- every source appears in exactly one primary pair.

Define four contiguous x macro-bands:
- Band0: columns 1-6;
- Band1: columns 7-12;
- Band2: columns 13-18;
- Band3: columns 19-24.

Each band contains 21 disjoint source-pair units.

No outcome-driven pair selection.

## 5. Frozen realization splits

Two complementary directions:
- Split A: even-indexed realizations are DESIGN (8/source), odd-indexed are AUDIT (8/source);
- Split B: odd DESIGN, even AUDIT.

All transforms and predictors for a direction are fitted using DESIGN only.
AUDIT realizations are never used to fit PCA, interaction scaling, geometry, hyperparameters, or source-pair predictors.

## 6. Base representation

Exactly five contiguous two-time blocks.
For each split and held-out source band:
- fit StandardScaler on DESIGN observations only;
- fit PCA=2 per block on DESIGN observations only;
- concatenate to z in R^10.

Then standardize each z coordinate using DESIGN-only global scale.

## 7. Fixed interaction representation

Partition z into five 2-D temporal blocks z_b.

Use parameter-free bounded coordinates:
`u = z / sqrt(1 + z^2)` elementwise.

For every block pair b<c, form the 2x2 outer product `u_b u_c^T`.
Concatenate all ten block-pair outer products to:
`j(z) in R^40`.

Candidate interaction representation:
`r_int = [z ; j(z)] in R^50`.

Base representation:
`r_base = z in R^10`.

No learned interaction subspace U at G0.
No rank tuning.
No Transformer/LSTM.

## 8. Actual held-out utility target

For each source pair, use the same fixed ridge-logistic reader family on DESIGN data for base and interaction representations.

Regularization is selected globally within the three non-held-out macro-bands only and frozen before scoring the held-out band.

Primary held-out utility:
`Delta_log = logloss_base - logloss_interaction` on AUDIT realizations.

Positive means the temporal interaction code helps.

Also report Brier and classification accuracy as diagnostics.

## 9. Reference-only neural-geometry predictor

For each pair and representation, compute from DESIGN only:
- center separation;
- effective within-source radius / total within variation;
- participation-ratio effective dimension;
- task-noise alignment;
- leading-axis alignment between the two source manifolds;
- finite-sample penalty term inspired by the fixed-readout risk decomposition;
- analytic `A - B/(2K)` score as a diagnostic feature.

These features form a low-dimensional GEOMETRY VECTOR.

Across source macro-bands, fit one fixed ridge predictor from the geometry vector to Delta_log using leave-one-band-out training:
- train on 3 bands;
- predict the 21 source-pair utilities in the held-out band;
- repeat for all four held-out bands.

Ridge penalty grid and standardization are selected using only the 3 training bands.

Pair outcomes from the held-out band may not enter selection.

## 10. Strong ordinary predictors

Evaluate with the same held-out bands:

1. `INNER_CV`: within each held-out pair's 8 DESIGN realizations, estimate interaction utility using a deterministic 4/4 swap cross-validation.
2. total cross-block covariance norm;
3. total interaction energy;
4. raw concentration-mass difference;
5. base-only pair separation / SNR.

`INNER_CV` is the primary ordinary competitor.

## 11. Frozen G0 gates

### G0-1 — utility is genuinely heterogeneous
Across the 84 primary pairs after averaging Split A/B:
- at least 10% of pairs have Delta_log > 0;
- at least 10% have Delta_log < 0.

If not, return HOLD because sign prediction is not meaningfully identifiable.

### G0-2 — theory predictor has prospective value
Across held-out macro-bands:
- Spearman correlation between geometry-predicted and AUDIT Delta_log > 0;
- pair-cluster bootstrap 95% CI lower bound > 0;
- correlation must be positive in both Split A and Split B separately.

### G0-3 — theory adds value beyond ordinary CV
Define per-pair squared prediction error for GEOMETRY and INNER_CV.
Require:
`mean(error_INNER_CV - error_GEOMETRY) > 0`
with pair-cluster bootstrap 95% CI lower bound > 0.

### G0-4 — sign prediction is not worse than ordinary CV
On pair benefit sign, GEOMETRY balanced accuracy must be >= INNER_CV balanced accuracy and >= 0.60.

### G0-5 — not explained by one spatial band
GEOMETRY-vs-INNER_CV mean squared-error advantage must be positive in at least 3 of 4 held-out macro-bands.

## 12. Decision

PASS:
`NPG_G0_PASS_TASK_GEOMETRY_PREDICTS_INTERACTION_UTILITY`
only if G0-1..G0-5 all pass.

HOLD:
`NPG_G0_HOLD_INSUFFICIENT_UTILITY_HETEROGENEITY`
only if G0-1 fails while no implementation issue is found.

STOP:
`NPG_G0_STOP_GEOMETRY_NOT_BETTER_THAN_ORDINARY_SELECTION`
for failure of any of G0-2..G0-5.

## 13. Consequence

PASS only authorizes a NEW method-development stage that learns a constrained task/context-conditioned interaction code.

PASS does NOT reinstate JTD, does NOT establish cross-environment generality, and does NOT authorize closed loop.

STOP means the 2026 neural-population-geometry mother theory, in this GSL mapping, has not produced predictive value beyond ordinary data-driven model selection and loses main-innovation priority.

H01 DEV and House03 stay sealed in every branch.