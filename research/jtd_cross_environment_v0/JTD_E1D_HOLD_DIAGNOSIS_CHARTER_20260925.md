# JTD-E1D — HOLD Diagnosis: Nearest-Neighbor Temporal-Dependence Failure

Date: 2026-09-25

Status: **ZERO-PLUME / ZERO-UNSEAL / POST-HOLD MECHANISM DIAGNOSIS ONLY**

Upstream frozen decision:
`JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL`.

Important: E1D cannot convert E1 HOLD into GO and cannot change any E1 threshold.

## 1. Why E1D

E1 passed G1, G2, G4, G5, G6 and G7, but failed breadth G3:
- 12/18 positive environment×source units;
- per-environment positive-source counts 5/6, 3/6, 4/6.

Post-hoc inspection shows most non-positive units are numerical-floor ties, while the two materially negative source-level effects are concentrated in adjacent-source confusions.

E1D asks:

> Does preserved temporal dependence fail because the K=4 source-specific Gaussian covariance is unstable/overconfident for certain adjacent pairs, or because the temporal dependence itself is genuinely anti-discriminative for those pairs?

## 2. Data scope

Use only:
- the frozen E1 four-reference/source arrays;
- the 36 already-generated E1 fresh targets;
- the frozen E1 FULL/null derangements and raw scores.

0 new plume.
Do not read H01 DEV.
Do not read House03.
Do not run dense G1A.

## 3. Frozen adjacent pairs

Use the E1 six-source panel ordering:
- pair P0: source indices 0↔1;
- pair P1: source indices 2↔3;
- pair P2: source indices 4↔5.

No pair selection from outcomes.

## 4. Pairwise evidence audit

For every fresh target y from true source s with frozen partner n:

FULL pair margin:
`m_full = log p_FULL(y|s) - log p_FULL(y|n)`.

SHUFFLED pair margin:
`m_null = median_j [log p_NULL_j(y|s) - log p_NULL_j(y|n)]`.

Temporal pair contribution:
`delta_pair = m_full - m_null`.

Report target/source/pair/environment summaries and pair-restricted classification accuracy.

This is diagnostic only; no new GO threshold is introduced.

## 5. Gaussian score decomposition

For true and partner source under FULL, export separately:
- Mahalanobis quadratic term;
- log-determinant term;
- total Gaussian log likelihood.

Report which term drives the wrong-partner preference in every materially negative target.

Do not change covariance or means for this decomposition.

## 6. K=4 covariance stability audit

Using the same four frozen references/source, perform four leave-one-reference-out K=3 refits of the original source-specific OAS model.

For every E1 fresh target report:
- true-vs-partner margin sign across the four K=3 refits;
- truth rank across refits;
- true-source NLL dispersion;
- OAS shrinkage coefficient, covariance trace/logdet and condition number by source/refit.

Purpose: determine whether the materially negative pair failures are stable or sensitive to one reference realization.

This does NOT override B1, which already showed K=3 is not globally reliable.

## 7. Block-product diagnostic control

Recompute the existing JTD-G0 BLOCK-PRODUCT working likelihood on E1 reference/target data:
- preserve each temporal block's source-specific mean/covariance;
- remove cross-block covariance/dependence;
- no feature or PCA change.

For each fresh target compare:
- FULL;
- BLOCK-PRODUCT;
- SHUFFLED.

This is a mechanistic diagnostic control only and may not be used to retune E1.

## 8. Required factual outputs

Explicitly identify:

A. numerical-floor/tie source units;
B. materially negative source units;
C. whether each materially negative case is an adjacent-partner error;
D. whether FULL is more overconfident than BLOCK-PRODUCT/SHUFFLED in those cases;
E. whether the error is stable under all K=3 jackknife refits or reference-sensitive;
F. whether pairwise temporal dependence improves or worsens each of the nine frozen environment×pair units.

## 9. Diagnostic conclusion labels

Return exactly one descriptive diagnosis:

`JTD_E1D_COVARIANCE_ESTIMATION_FAILURE_LOCALIZED`
if materially negative cases are strongly reference-sensitive and/or disappear under the block-product control;

`JTD_E1D_PAIRWISE_TEMPORAL_SIGNAL_HETEROGENEOUS`
if materially negative nearest-neighbor effects remain stable across refits and are specifically caused by preserved cross-block dependence;

`JTD_E1D_MIXED_ESTIMATION_AND_PAIR_HETEROGENEITY`
if both mechanisms are present.

These are diagnosis labels, not GO/HOLD/STOP decisions.

## 10. Consequence

After E1D, the primary thread decides whether the next experiment is the already-existing dense-bank JTD-G1A (0 new plume) or whether JTD requires representation/theory work before consuming further validation budget.

No closed loop.