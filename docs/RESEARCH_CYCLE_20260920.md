# Research-cycle checkpoint — 2026-09-20

## Constraint carried forward

Goal: find a paper-level **main scientific idea** for UAV gas-source localization, not an engineering patch. The main idea must come from a recent (2025/2026) remote-domain top-tier scientific/ML line, have a clear theoretical theme, survive physics scrutiny, and show source-discrimination value on available data. SBI is excluded. Pure neural operator / generic foundation model / Mamba / energy-landscape / causal relabeling without a stronger mechanism are not sufficient.

## Already rejected / demoted

- SINN / structural-information neural inverse operator: failed frozen H03 two-source discrimination (3/4 vs Euclidean 4/4; full source-map mean error 6.29 m vs 4.19 m), so no closed-loop continuation.
- Compound-channel / AVC / symmetrizability: useful diagnostic language but too low-level to carry the paper.
- Generic inverse generative modeling / physical world model / physics-informed SSL: retained only as background inspiration, not yet accepted as the paper's organizing principle.

## Current high-value branch

### A. Multiscale non-stationarity / TimeBridge transfer

Source: Liu et al., **TimeBridge: Non-Stationarity Matters for Long-term Time Series Forecasting**, ICML 2025.

Transfer hypothesis:
- short windows should suppress nuisance non-stationarity to expose local plume-response dependencies;
- long windows should preserve non-stationarity when it carries source-specific cross-variable structure;
- for GSL, the key question is not forecasting accuracy but whether the resulting multiscale representation preserves **source identity** across windows, trajectories, and wind regimes.

Required falsification gates:
1. source classification must remain above control after removing absolute wind-speed cues;
2. performance must be stable across multiple window lengths rather than driven by one convenient timescale;
3. source identity must persist across disjoint temporal blocks;
4. representation must improve source discrimination beyond simple concentration/wind summary statistics.

Status: ACTIVE TEST, not yet accepted as main idea.

### B. Physics-guided operator invariance

Hypothesis:
a source is identifiable by a transport-response operator whose invariant structure persists across nuisance changes (wind realization, sampling window, route segment), rather than by raw concentration magnitude.

Candidate observables:
- local ARX / impulse-response coefficients between wind-aligned transport inputs and gas response;
- pole/zero or decay-time summaries;
- normalized gain and phase-lag quantities designed to remove release-rate scale;
- cross-window subspace / coefficient consistency;
- Fisher information or sensitivity of those operator descriptors to candidate source location.

Required falsification gates:
1. same-source operator descriptors must be more stable across disjoint windows than different-source descriptors;
2. invariance must survive wind-speed normalization / residualization;
3. descriptors must discriminate source better than raw feature controls;
4. the effect must hold across multiple public / historical datasets, not only House01/02/03.

Status: ACTIVE CANDIDATE. This is currently more promising as a paper-level physical theme than a direct architecture transfer if the invariance tests pass.

### C. ARX + Fisher as a control and possible mechanism

ARX itself is not accepted as the main innovation. It is used as a low-capacity system-identification probe to test whether a reproducible source-specific transport operator exists.

Fisher information is used as a diagnostic:
- if the source-specific operator is real, candidate-source perturbations should induce structured, repeatable sensitivity in the identified dynamics;
- if Fisher structure collapses after wind-speed controls or across time blocks, reject the operator-invariance hypothesis.

Status: NEXT EXECUTION STEP.

## Immediate continuation point after interrupted session

1. Obtain measured / public multivariate control data suitable for source-ID tests.
2. Fit low-order ARX probes over multiple window sizes.
3. Evaluate same-source vs different-source coefficient/subspace distances.
4. Repeat after explicit wind-speed leakage controls.
5. Compute Fisher/sensitivity representation and cross-window identity consistency.
6. Compare against TimeBridge-inspired multiscale features and simple raw-statistic baselines.
7. If both TimeBridge and ARX/Fisher fail the frozen discrimination gates, reject this branch and resume 2025/2026 remote-domain search rather than forcing a method.


---

## Cycle update — public-data falsification and symmetry pivot

### Measured-data testbed

Public Orebro3DSEN measurements were used as an external falsification set. The repository provides a 3x3x3 array of 27 calibrated MOX sensors sampled at 2 Hz together with wind speed/direction. Following the dataset's own analysis convention, source-discrimination probes use the 40–90 min interval; the first 15 min is available as an early baseline.

The experiment table contains repeated measurements at the same physical source location under different release/airflow conditions. In table row order, Exp01/Exp02/Exp06/Exp08/Exp09 share source coordinate (2.70, 0.50, 0.90) while varying beaker size and airflow (off / DC fan / tower fan). Exp03/04/05/07/10 provide alternative source locations. This makes the dataset useful for a same-source/different-nuisance test.

### Frozen low-capacity probe results

Windows: 2, 5, and 10 min within 40–90 min.

Representations:
- raw: 27 sensor means;
- spatial shape: per-window affine canonicalization across sensors, `z=(c-mean(c))/std(c)`;
- dynamics: autocorrelation / block-variance descriptors;
- ARX: low-order gas response coefficients using current/lagged wind terms;
- operator proxy: multiscale lagged cross-correlation operators inspired by Koopman/KoopSTD, with temporal-shuffle control.

At 5 min, using experiment centroids and repeated source-location identity:
- raw concentration: same-vs-different AUC 0.489, leave-condition-out accuracy 0.20;
- affine spatial shape: AUC 0.880, accuracy 0.82;
- dynamics: AUC about 0.486, accuracy 0.36;
- ARX: AUC about 0.549, accuracy 0.54;
- multiscale operator proxy: AUC 0.403, accuracy 0.14;
- shuffled-time operator control: AUC 0.406, accuracy 0.26.

The affine spatial result is stable across scales:
- 2 min: AUC 0.891, leave-condition-out accuracy 0.808;
- 5 min: AUC 0.880, accuracy 0.820;
- 10 min: AUC 0.880, accuracy 0.800.

A baseline-subtracted affine shape is similar (5 min AUC 0.883, accuracy 0.86); rank-only and centered-log-ratio alternatives also retain useful identity but do not clearly dominate the simple affine quotient.

### Critical rejection

**Physics-guided transport-operator invariance is demoted/rejected as the main idea.**

Reason: on measured data, ARX/dynamical/operator descriptors do not outperform the much simpler affine spatial canonical form. More importantly, temporal shuffling is as good as or better than the operator proxy, so the observed discrimination cannot be defended as evidence for a source-specific dynamical transport operator.

TimeBridge-style multiscale temporal modeling is therefore also demoted from main-theme status. Its high-level non-stationarity lesson may remain useful for auxiliary window design, but the data do not justify making temporal dynamics the paper's organizing principle.

### Strong surviving phenomenon: nuisance quotient / canonicalization

The robust empirical phenomenon is spatial source identity after removing a shared offset and positive scale.

For concentration vector `c in R^n`, define

`
P = I - (1/n) 11^T,
kappa(c) = P c / ||P c||.
`

For nuisance action

`
c' = a c + b 1,   a > 0,
`

we have exactly

`
kappa(c') = kappa(c).
`

Thus unknown common background offset and positive concentration/release/sensor gain are quotiented out analytically, while the spatial plume shape remains. This is not a learned black-box invariance.

The measured-data result is consistent with this mechanism: raw amplitude does not preserve repeated-source identity, whereas the quotient representation does.

### Recent remote-domain scientific lineage

This branch now has a stronger 2025/2026 theoretical lineage than the operator branch:

1. Tahmasebi & Jegelka, **Generalization Bounds for Canonicalization: A Comparative Study with Group Averaging**, ICLR 2025. Canonicalization projects data onto a reduced input space representing invariance classes and gives explicit generalization/sample-complexity regimes.
2. Shumaylov et al., **Lie Algebra Canonicalization: Equivariant Neural Operators under Arbitrary Lie Groups**, ICLR 2025. Canonicalization aligns inputs under continuous/non-compact symmetries before ordinary model inference.
3. Urbano et al., **RECON: Robust Symmetry Discovery via Explicit Canonical Orientation Normalization**, ICLR 2026. Data-aligned canonicalization addresses unknown, instance-specific symmetries and test-time distribution shift.
4. Lin & Levie, **Adaptive Canonicalization with Application to Invariant Anisotropic Geometric Networks**, ICLR 2026. Canonicalization is allowed to depend on the input/model; continuity and universal-approximation results are established.
5. **Quotient-Space Diffusion Models**, ICLR 2026. The general principle is that when group-related observations are equivalent, learning can be performed on the quotient rather than wasting capacity on movement inside equivalence classes.

### New main candidate

**Working theme: Transport-Nuisance Quotient Canonicalization (TNQC).**

Paper-level statement:
> Gas-source inference should be performed on equivalence classes of observations under physically non-identifying nuisance transformations, rather than on raw concentration fields.

The first exact quotient is affine concentration nuisance. The unresolved hard nuisance is airflow.

A fixed global linear wind residualizer looked very strong when fit transductively, but failed a stricter leave-one-condition-out test. With the canonical affine shape and cross-fitted wind regression, repeated-source accuracy was only about 0.60 at 2/5/10 min: Exp01/02/06 generalized, but the held-out tower-fan Exp08/09 conditions failed. Therefore **wind cannot be declared a simple global linear nuisance**.

This failure is useful: it points directly to the second-innovation requirement. We need a physics-conditioned/adaptive canonicalizer, not another generic residualization layer.

### Revised architecture hypothesis

Main innovation:
- **Nuisance quotient inference**: exact analytic quotient for release/background amplitude nuisance, with posterior inference performed in the canonical space.

Auxiliary innovation candidate 1:
- **Context-conditioned transport canonicalizer**: use observed wind/transport context to map airflow-dependent plume realizations to a common source representation. This should be adaptive/contextual, inspired by 2026 adaptive canonicalization, but physically constrained rather than a free network.

Auxiliary innovation candidate 2:
- **Orbit-consistency identifiability gate**: release posterior evidence only when disjoint windows agree after canonicalization. This converts cross-window canonical consistency into an identifiability condition and may connect naturally to the already successful ME-ACI sequential-replication gate.

### Next hard gate

Do not promote TNQC yet. The branch advances only if a source-blind context-conditioned canonicalizer:
1. improves held-out DC/tower airflow conditions without seeing their source truth;
2. preserves the exact affine nuisance invariance;
3. beats raw concentration, affine-only canonicalization, and shuffled/temporal controls;
4. transfers to House/VGR data or a second measured dataset;
5. yields an online statistic compatible with the PMFS/ME-ACI posterior rather than only an offline classifier.

Status: **TNQC promoted to primary candidate; operator-invariance and TimeBridge demoted. Airflow canonicalization is now the decisive falsification test.**
