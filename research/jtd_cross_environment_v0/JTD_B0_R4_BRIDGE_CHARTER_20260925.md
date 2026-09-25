# JTD-B0 — R=4 Low-Sample Bridge Gate

Date: 2026-09-25

Status: **ZERO-PLUME / ZERO-HOLDOUT / ESTIMATOR-FEASIBILITY GATE**

Upstream:
- JTD-G0 discovery decision: `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`;
- G0 final commit: `170d0ccddc559c97744af5409ec1e3642bcfa743`;
- R0 benchmark commit: `e527beea07c33cdbc362d156545409245f029968`.

## 1. Purpose

Before testing JTD across E2 environments, verify that an R=4 estimator can recover the already-established G0 temporal-dependence signal on the original 18-source R0 bank.

This gate does NOT test generalization and does NOT create a main-innovation PASS.

## 2. Data

Use only the original R0/JTD-G0 18 sources ×16 independent realizations/source.

No E2 DEV/HOUSE03 data.
No new plume.

Partition the 16 realizations into four deterministic quartets:
- Q1 = reps 1-4;
- Q2 = reps 5-8;
- Q3 = reps 9-12;
- Q4 = reps 13-16.

Within each quartet perform four leave-one-realization-out folds:
- 3 train realizations/source;
- 1 fresh target realization/source.

Across the four quartets every original realization becomes a target exactly once.

## 3. Frozen temporal feature contract

Reuse JTD-G0 exactly:
- 10×30 observation;
- same five temporal blocks;
- two PCA components/block;
- 10-D concatenated feature;
- same concentration transform/scaling conventions.

Fit scaler/PCA using training data only in each fold.
No feature search or block change.

## 4. R=4 Gaussian working likelihood

Source-specific means are estimated from the three training realizations/source.

Because R=3 training realizations/source cannot support stable source-specific 10×10 covariance, use one pooled within-source covariance per fold:

1. compute each source mean mu_s from its three training feature vectors;
2. stack residuals z_sr - mu_s across all 18 sources;
3. estimate one 10×10 OAS covariance `Sigma_FULL` from the pooled residuals.

All 18 source likelihoods share Sigma_FULL but retain distinct mu_s.

Posterior over the 18 candidate sources is normalized exactly as in G0.

## 5. Marginal-preserving SHUFFLED null

Within each source and training fold:
- keep block 1 realization order fixed;
- independently derange blocks 2-5 across the three training realizations;
- only the two non-identity 3-cycles are allowed;
- choose cycles deterministically from a SHA-256 key containing quartet/fold/null_id/source/block.

Block-wise sample sets, source labels, block means, and block marginal covariance are therefore preserved; cross-block realization identity is destroyed.

Recompute the pooled OAS covariance from the shuffled training features.

Use 199 deterministic null realizations/fold unless the exact G0 null count is larger, in which case inherit the G0 count.

For each held-out target, define SHUFFLED NLL as the median truth-source NLL across null realizations.

## 6. Primary paired effect

For every held-out target:

  delta = NLL_SHUFFLED - NLL_FULL.

Positive delta favors preserved temporal dependence.

Report:
- mean delta;
- median delta;
- 10% and 20% trimmed mean delta;
- relative mean NLL improvement;
- per-source mean delta;
- per-quartet mean delta;
- fraction target delta>0;
- truth rank/top-3 as diagnostics only.

## 7. Frozen B0 PASS gate

PASS only if all hold:

### B0-G1
Pooled mean delta > 0 and a source-stratified paired bootstrap 95% CI lower bound > 0.

### B0-G2
All four quartet-level mean deltas > 0.

### B0-G3
At least 14/18 sources have positive mean delta.

### B0-G4
20% trimmed mean delta > 0.

### B0-G5
After removing the largest positive 5% of target-level deltas, the remaining mean delta > 0.

### B0-G6
Relative mean truth-source NLL improvement >= 10%.

## 8. Decision

PASS:
`JTD_B0_PASS_R4_ESTIMATOR_BRIDGE`.

FAIL:
`JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE`.

If FAIL, do NOT interpret this as JTD mechanism failure; it means E2 R=4 is not an adequate direct estimator for the G0 mechanism.

## 9. Consequence

Only B0 PASS authorizes JTD-E1 cross-environment existence testing on the three E2 OPEN environments.

No dense-source expansion and no closed loop at B0.