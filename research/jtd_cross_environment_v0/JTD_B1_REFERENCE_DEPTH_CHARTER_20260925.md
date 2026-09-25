# JTD-B1 — Source-Specific OAS Reference-Depth Audit

Date: 2026-09-25

Status: **ZERO-PLUME / ESTIMATOR-DEPTH AUDIT — NOT A MECHANISM CONFIRMATION**

Upstream:
- JTD-G0: `JTD_G0_GO_TEMPORAL_DEPENDENCE_SIGNAL`;
- JTD-B0: `JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE`.

## 1. Why B1 is needed

B0 changed two things at once:
1. realization depth was reduced;
2. source-specific OAS covariance from G0 was replaced by one pooled covariance shared by all sources.

Because JTD's discriminative temporal dependence may itself be source-specific covariance/dependence, B0 is not a faithful power curve for the G0 model class.

B1 restores the exact G0 source-specific OAS working likelihood and varies only reference depth.

## 2. Data

Use only the audited R0 18 sources x16 realizations.
No E2 data.
No sealed data.
No new plume.

Retain the original G0 four evaluation folds:
- F0 targets reps 1,5,9,13;
- F1 targets reps 2,6,10,14;
- F2 targets reps 3,7,11,15;
- F3 targets reps 4,8,12,16.

Each fold leaves 12 candidate reference realizations/source.

## 3. Reference-depth ladder

Evaluate source-specific OAS at:
`K = {3,4,6,8,10,12}` reference realizations/source.

For every K<12, use three deterministic balanced cyclic reference subpanels from the 12 available references.

Subpanel construction must be frozen before scoring and depend only on replicate indices, never outcomes.

For K=12 use the original G0 reference set.

## 4. Representation and null

Exactly inherit G0:
- raw 10x30 observation;
- five contiguous two-time blocks;
- training-only StandardScaler per block;
- PCA=2/block;
- concatenated 10-D representation;
- source-specific OAS Gaussian working likelihood;
- anchor block 1 fixed;
- blocks 2-5 independently deranged within source;
- marginal-preserving destructive null;
- 200 deterministic nulls per fold/subpanel.

No pooled covariance.
No alternate normalization.
No feature/model search.

## 5. Per-depth metrics

For each K report across all fold/subpanels:
- mean delta NLL;
- source-stratified bootstrap 95% CI;
- median delta;
- 20% trimmed mean delta;
- relative mean NLL improvement;
- positive-source count;
- positive-target fraction;
- minimum fold/subpanel mean delta;
- mean/full truth NLL;
- 95th and 99th percentile FULL truth NLL;
- mean truth rank/top-3 as diagnostics.

Define delta = NLL_SHUFFLED - NLL_FULL.

## 6. Reliability gate for a reference depth K

A depth K is `RELIABLE` only if all hold:

R1. source-stratified bootstrap 95% CI lower bound > 0;
R2. every fold/subpanel mean delta > 0;
R3. at least 14/18 sources have positive mean delta;
R4. 20% trimmed mean delta > 0;
R5. after removing the largest positive 5% target deltas, remaining mean delta > 0;
R6. relative mean NLL improvement >= 10%.

These are the B0 robustness requirements, now applied to the G0-faithful likelihood family.

## 7. Decision

Let K_min be the smallest RELIABLE depth.

If any K<=10 is RELIABLE:
`JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED`
and report K_min.

If only K=12 is RELIABLE:
`JTD_B1_HOLD_REQUIRES_G0_DEPTH`.

If K=12 itself does not reproduce G0:
`JTD_B1_FAIL_IMPLEMENTATION_OR_CONTRACT_DRIFT`.

## 8. Consequence

B1 does not test cross-environment generalization.

If K_min is identified, use it to determine the minimum E2 OPEN deepening budget before JTD-E1.

Target design after B1 should preserve at least two fresh realizations/source in each E2 OPEN environment.

No dense-source expansion or closed loop at B1.