# Partial-Identification GSL V1

Date: 2026-09-22
Branch: `research/partial-identification-gsl-v1`
Status: **MAIN-INNOVATION CANDIDATE / R2 FALSIFICATION REQUIRED**

## 1. Mother idea

Gas-source localization under turbulent transport should not assume that a misspecified forward model point-identifies one source.

Instead, define the **identified source set**

[
mathcal I_epsilon(y)={s: exists, Tinmathcal T_epsilon 	ext{such that} D(y,F(s,T))le epsilon},
]

where:
- (s) is source location;
- (T) is a plausible transport law / nuisance realization;
- (mathcal T_epsilon) is a misspecification neighbourhood;
- (D) is a predeclared observation discrepancy.

The estimator's first job is to determine what the data actually identify.
Only when (mathcal I_epsilon) contracts sufficiently should the algorithm release a point source estimate.

The planner should therefore seek actions that reduce the worst-case spatial diameter / ambiguity of (mathcal I_epsilon), rather than maximize entropy reduction of one potentially wrong posterior.

## 2. Modern remote-field roots

Recent anchors:
- NeurIPS 2025 — Lanners et al., *Data Fusion for Partial Identification of Causal Effects*.
- ICML 2025 — Schweisthal et al., *Learning Representations of Instruments for Partial Identification of Treatment Effects*.
- Artificial Intelligence 2026 — Skalse & Abate, *Partial identifiability and misspecification in inverse reinforcement learning*.

Transferred principle:

> under structural ambiguity and model misspecification, valid inference is an identified set / bound before it is a point estimate.

This is materially different from:
- conformal prediction sets;
- credal posterior sets;
- generalized-Bayes tempering;
- ordinary robust Bayes;
- entropy thresholding.

## 3. Why it directly matches the project failure

Frozen project evidence already shows:
- strong source-discriminative spatial signal exists in the controlled asset;
- TNQC V5 nevertheless gives essentially no 300-s endpoint gain;
- all six authoritative R2 cases exhibit false-confident collapse.

This is exactly the regime where a point posterior can be scientifically stronger than the available identification information.

The working hypothesis is not "uncertainty should be larger".
It is:

**the forward model may not uniquely identify source location at the current trajectory, and PMFS currently converts non-identifiability into false posterior certainty.**

## 4. Hard novelty boundary

Not new:
- inverse source problems;
- robust optimization;
- confidence / credible regions;
- conformal source sets;
- generalized Bayes;
- finite transport-model ensembles.

Targeted contribution:

**transport-misspecification-aware partial identification of gas-source location, with active motion chosen to contract the identified source region.**

Targeted searches found no direct GSL/OSL implementation of partial-identification / identified-set inference under transport misspecification.

## 5. Authoritative R2 falsification object

Use the exact GitHub Release:
`tnqc-v5-r2-execution-20260921`

Archive:
`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

SHA256:
`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Six cases:
House01/02/03 × seed0/1.

Native endpoint remains:
`ExpectedValue(sourceProbability,0.05)` at 300 s.

No 2/5/10-min substitute metric.

## 6. First R2 screen: source robustness radius

For each source-update candidate (s), use only exported support alignment:
- measured_probability;
- measured_confidence;
- simulated_hit_probability;
- geometry / candidate support.

Define a predeclared discrepancy functional (D_s) and then compute the **minimal misspecification radius**

[
ho^*(s)=inf{ho: s 	ext{cannot be rejected under the allowed discrepancy set of radius }ho}.
]

Do not choose one truth-tuned radius.

Evaluate the full source-blind **breakdown curve**:
- identified-set mass / area vs radius;
- spatial diameter vs radius;
- native-MAP robustness radius;
- true-source-neighbourhood inclusion vs radius (truth used only by evaluator);
- false confident posterior vs small robustness radius.

The first scientific question is:

> Does the native sharp posterior correspond to a genuinely robustly identified source, or to a source whose dominance disappears under a very small admissible model discrepancy?

## 7. Required controls

- identical calculation on native and TNQC posteriors;
- source-blind radius grid fixed before truth inspection;
- duplicated support rows may not increase identification strength;
- support erasure must widen, never sharpen, the identified set;
- affine nuisance transforms already handled by the frozen quotient may not be re-counted as new robustness;
- candidate count / quadtree leaf area must not be treated as iid replication;
- no radius or threshold chosen per House or seed.

## 8. Promotion gate

Do not promote from "honest uncertainty" alone.

A main-innovation GO requires both:

1. **diagnostic necessity**:
   the six false-confident R2 cases must show systematically small robustness/breakdown radii despite sharp native posterior;

2. **localization utility**:
   an identified-set-derived source estimator or fixed-trajectory decision rule must improve the native 300-s endpoint by >=2% pooled, with >=4/6 non-worse, before any closed-loop run.

If only criterion 1 passes, partial identification is an auxiliary reliability contribution, not the main localization innovation.

## 9. Current verdict

**GO FOR R2 OFFLINE FALSIFICATION ONLY.**

No closed-loop authorization yet.
