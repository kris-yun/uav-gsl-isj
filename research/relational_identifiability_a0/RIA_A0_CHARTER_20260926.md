# RIA-A0 — Relational Identifiability Audit

Date: 2026-09-26

Status: **ZERO-PLUME PRE-ADMISSION AUDIT — NOT A MAIN-INNOVATION TEST**

Frozen upstream facts:
- JTD mainline STOP.
- NPG mapping STOP.
- SPX diagnosis retained as `SPX_G0_SOURCE_PROBE_INTERACTION` with the strict interpretation that neither frozen single-factor dominance rule was supported.
- Previous RSC-G0 cancelled before execution because its NLL-utility target mixed physical identifiability with estimator risk.

## 1. Scientific purpose

Separate two questions that SPX currently confounds:

### Q1 — Observation-level source identifiability
Does switching the probe layout change how distinguishable the two source-conditioned observation distributions are, independent of FULL/BP/MBD?

### Q2 — Estimator risk
Does switching the probe layout instead mainly change how badly a finite-sample Gaussian working model can become overconfident?

RIA-A0 does not propose a new mother theory.
It decides whether a future physical/biological mother theory is even justified.

## 2. Data scope

Use only House02 `3,5-1_slow` W0.

Primary panel:
- 84 frozen CENTRAL 0.3 m source pairs;
- both frozen probe protocols P_G1A and P_E2;
- the already-cross-extracted 10x30 tensors from SPX;
- all 16 realizations/source.

OFFSTRIP 3 pairs:
- descriptive stress test only;
- never used to choose formulas or thresholds.

0 new plume.
No H01 DEV.
No House03.
No H02 W2.

## 3. Four-fold reference budget

Retain SPX's four deterministic folds.

For each pair/protocol/fold:
- 12 realizations/source = REFERENCE;
- 4 realizations/source = HELDOUT.

All observation-identifiability quantities are computed from REFERENCE only.
All operational bounded metrics are computed on HELDOUT only.

Folds share references and are NOT treated as independent experimental units.
Pair is the bootstrap unit.

## 4. Primary model-independent-ish identifiability quantities

Use the raw flattened 10x30 ppm observation vector `x in R^300`.
No PCA.
No OAS.
No learned decoder.
No target-driven feature transform.

### 4.1 Normalized contrast-to-within ratio

For sources a and b:

`S = ||mu_a - mu_b||_2^2`

`W = 0.5 * [ mean_i ||x_ai-mu_a||_2^2 + mean_j ||x_bj-mu_b||_2^2 ]`

`D_CNR = S / (W + eps)`

with `eps = 1e-12 * max(1, W)`.

### 4.2 Normalized energy distance

Let:

`ED = 2 mean_{i,j} ||x_ai-x_bj|| - mean_{i!=i'} ||x_ai-x_ai'|| - mean_{j!=j'} ||x_bj-x_bj'||`

using the unbiased within-source off-diagonal means.

Normalize by:

`W_E = 0.5 * [ mean_{i!=i'} ||x_ai-x_ai'|| + mean_{j!=j'} ||x_bj-x_bj'|| ]`

`D_ED = ED / (W_E + eps)`.

Energy distance is used as a distribution-separation diagnostic, not claimed to equal mutual information or Bayes error.

## 5. Pair/protocol aggregation

For each pair/protocol:
- average D_CNR across the four 12-reference folds;
- average D_ED across the four folds;
- report fold range and standard deviation.

Define probe-switch changes:

`Delta_CNR = D_CNR(P_E2) - D_CNR(P_G1A)`

`Delta_ED = D_ED(P_E2) - D_ED(P_G1A)`.

These are the primary observation-identifiability changes.

## 6. Bounded operational relevance

From the frozen SPX heldout scores, for every pair/protocol compute:

`A(P) = median over {FULL,BP,MBD} of heldout accuracy`

`B(P) = - median over {FULL,BP,MBD} of heldout Brier`

where higher is better for both A and B.

Define:
- `Delta_A = A(P_E2)-A(P_G1A)`;
- `Delta_B = B(P_E2)-B(P_G1A)`.

These are not treated as intrinsic information measures.
They are bounded operational checks that the reference-only distribution-separation metric is behaviorally relevant across multiple existing readers.

## 7. Estimator-risk quantities

For FULL, BP and MBD separately, pair/protocol:

- mean two-class NLL;
- 20% trimmed mean NLL;
- `tail_excess = mean_NLL - trimmed20_NLL`;
- misclassification rate;
- mean NLL conditional on misclassification;
- 95th percentile target NLL;
- maximum target NLL.

For FULL-vs-BP and FULL-vs-MBD also retain the frozen SPX pair utility.

Probe-switch estimator-risk changes are differences P_E2-P_G1A.

## 8. Frozen A0 questions

### A0-Q1 — Does reference-only identifiability track bounded heldout discriminability?

For both D_CNR and D_ED require:
- Spearman with Delta_A > 0;
- Spearman with Delta_B > 0.

Use 10,000 pair bootstrap resamples of the 84 CENTRAL pairs for 95% intervals.

### A0-Q2 — Are NLL utility flips separable from identifiability change?

Compute for FULL-vs-BP and FULL-vs-MBD:
- Spearman of SPX probe-switch NLL utility with Delta_CNR and Delta_ED;
- Spearman with FULL tail_excess change;
- proportion of pair utility sign flips for which Delta_A and Delta_B agree with the NLL-utility sign;
- proportion for which bounded metrics disagree while tail_excess moves in the NLL-utility direction.

No threshold is optimized post hoc.

### A0-Q3 — Is there a physical-target candidate worth predicting?

A future physical-context mother-theory search is authorized only if BOTH D_CNR and D_ED:
- have positive bootstrap-lower-bound association with at least one of Delta_A or Delta_B;
- have the same sign of association with both bounded metrics;
- are not dominated by a single source pair: leave-one-pair-out sign of the association remains positive for >=95% of removals.

## 9. Diagnostic labels

Return exactly one:

`RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED`
if A0-Q3 passes.

`RIA_A0_MODEL_RISK_DOMINANT_NO_PHYSICAL_TARGET_YET`
if A0-Q3 fails while SPX NLL utility is materially associated with tail_excess changes.

`RIA_A0_MIXED_OR_UNRESOLVED`
for all other outcomes.

These are diagnostic labels, not GO/HOLD/STOP for a method.

## 10. Consequence

If `PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED`:
- only then revive a far-domain relational sensing / sensory-contingency search;
- the future theory must predict Delta_CNR / Delta_ED prospectively from source–probe–flow context;
- it may not use FULL-vs-BP/MBD NLL utility as the physical target.

If `MODEL_RISK_DOMINANT_NO_PHYSICAL_TARGET_YET`:
- do not build a context-gating model;
- treat the current problem as estimator robustness/calibration unless new physical evidence appears.

If `MIXED_OR_UNRESOLVED`:
- no new mother-theory candidate is authorized;
- record the ambiguity and stop rather than add another model.

## 11. OFFSTRIP stress test

After the CENTRAL diagnosis is frozen, compute D_CNR/D_ED and bounded/risk summaries for the three OFFSTRIP pairs.

Descriptive only.
No threshold or label may be changed from OFFSTRIP results.