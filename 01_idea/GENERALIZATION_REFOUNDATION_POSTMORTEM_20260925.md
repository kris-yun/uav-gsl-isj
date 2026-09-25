# Generalization Refoundation v0 — Why Repeated Mainline Candidates Fail

Date: 2026-09-25

Status: **POSTMORTEM / PROCESS RESET — NO NEW PLUME SIMULATION AUTHORIZED**

Frozen upstream decision remains:
`LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`.

## 1. The failure is scientific, not an execution artifact

The pre-data infrastructure patch only repaired the W0 16->8 replicate selection, SciPy return-value compatibility, and missing execution/package scripts. It did not change the scientific statistic, thresholds, source panel, winds, or outcome-dependent logic.

Therefore the cross-wind FAIL must be interpreted scientifically.

## 2. What actually failed

LSC was discovered as a strong relation inside one fixed environment/operator:

  D(s_i,s_j | House02, W0, fixed observation operator)

was treated too readily as if there were a portable source-pair property

  D(s_i,s_j).

The cross-wind data show that this reduction is wrong.

The correct object is environment-conditioned:

  D_E(s_i,s_j) = distinguishability of source hypotheses under environment/operator E and observation protocol M.

## 3. Direct evidence for wind × source-edge interaction

Using the same ten frozen source-pair edges:

Split-averaged energy-distance edge rankings:
- W0 (`3,5-1_slow`) vs W1 (`3,5-1_fast`): Spearman ~ +0.61;
- W0 vs W2 (`4,5-3_slow`): ~ -0.43;
- W1 vs W2: ~ -0.54.

W0 and W1 belong to the same canonical wind family and have very similar mean weighted directions (~-121 deg and ~-118 deg), differing mainly in speed.
W2 belongs to the other canonical wind family and has mean weighted direction ~160 deg.

Thus changing speed within one wind family largely preserves source-edge distinguishability ordering, while changing the wind family/direction reorganizes it.

Two-way descriptive variance decomposition of energy distance:
- additive split + edge + wind effects explain only about 20-37% of variation within the two split views;
- the wind×edge interaction leaves about 63-79% of total variation beyond that additive structure.

The interaction is not merely split noise:
- A/B interaction-residual Spearman ~0.67;
- Pearson ~0.73.

Therefore the dominant structure is a reproducible environment-by-source-pair interaction.

## 4. Directional anisotropy clue

On the frozen rectangular panel:

W0/W1:
- y-oriented neighbor edges have substantially larger mean distinguishability than x-oriented edges;
- their fresh pairwise error is also lower.

W2:
- x-oriented edges become more distinguishable than y-oriented edges on average.

The canonical global wind-direction projection shows the same qualitative rotation:
- W0/W1 wind has larger |y| than |x| component;
- W2 has much larger |x| than |y| component.

Across the six wind×edge-orientation aggregate cells, absolute wind/edge alignment has exploratory Pearson correlation ~0.80 with mean energy distance.

This is **not confirmation**; it is a post-failure clue that source-space identifiability is anisotropic and wind-conditioned.

## 5. Why the project has repeatedly produced 'signal, then failure'

### 5.1 Hierarchical sample-size mismatch

Thousands of plume realizations in one House/wind increase knowledge of

  P(Y | S, E_fixed),

but do not estimate variability across E.

For cross-environment claims, the experimental unit is the wind/House/operator, not the plume seed.

D1R has 2,688 realization-level samples but only one environment/operator.

### 5.2 Scientific hypothesis overfitting to one environment

Even when every individual experiment is frozen correctly, repeatedly generating new mechanisms from the same W0/D1R environment creates researcher-level selection on that environment.

A mechanism can become exquisitely adapted to House02/W0 while every within-route split remains honest.

### 5.3 Source-only invariants were repeatedly assumed rather than demonstrated

Several routes searched for stable properties of source candidates while transport and observation geometry are strongly environment-conditioned.

Cross-wind failure is therefore not surprising once E is exposed.

### 5.4 Dense labeled reference banks are not a deployment solution

A mechanism that requires repeated known-source plume distributions in every new wind/site is unsuitable as the final real-flight main innovation.

Reference banks may be used for discovery and evaluation, but not as an implicit runtime requirement.

### 5.5 Forward accuracy and inverse identifiability are different objectives

M4 already showed that field-prediction improvements need not improve source ranking.
LSC now shows that inverse distinguishability itself changes with the transport operator.

## 6. New research-governance rules

Effective immediately:

1. **Environment-conditioned by default.**
   Any candidate source mechanism is written as f(S,E,M), not f(S), unless invariance to E is itself confirmed.

2. **Environment count is reported separately.**
   `N_realization`, `N_source`, and `N_environment/operator` must never be conflated.

3. **No mainline discovery from a single E.**
   A new main mechanism must see at least two environment/operators during discovery and face at least one untouched operator before promotion.

4. **No target-environment dense source bank as a runtime dependency.**
   Deployment variables must be available from geometry, wind sensing/estimation, UAV observations, or sparse realistic calibration.

5. **Mechanism before architecture.**
   No new far-domain model is authorized until a deployable environmental variable explains the observed cross-environment interaction.

6. **Strong ordinary baseline first.**
   Any learned representation/inference rule must beat ordinary discriminant/calibration/interpolation baselines on proper source score.

7. **Fresh environment before dense expansion.**
   Spend budget on new independent E before adding more seeds within the same E, once within-E estimator stability is adequate.

## 7. Immediate zero-plume-simulation next step

Candidate diagnostic name: **Wind-Conditioned Identifiability Geometry (WCIG) audit**.

This is not a new main innovation.

Use only existing canonical 3D wind files plus already generated W0/W1/W2 plume results.

For each frozen source-pair edge and wind:
- extract local wind vector statistics from the existing 11 wind iterations at source endpoints/midpoint and a preregistered small neighborhood;
- compute edge displacement vector;
- derive physically available covariates: along-edge wind projection, cross-edge projection, local speed, directional variability/shear;
- test whether these variables explain the reproducible wind×edge distinguishability interaction.

No target plume outcome may be used to choose covariates after the audit is frozen.

## 8. Fresh falsification opportunity

`4,5-3_fast` is the remaining canonical House02 wind family member.

If the zero-plume WCIG audit yields a sharp prediction, freeze the prediction for `4,5-3_fast` **before generating any plume outcomes**.

A particularly falsifiable family-level prediction is:
- `4,5-3_fast` should resemble `4,5-3_slow` in the orientation/order of local source distinguishability more than it resembles the `3,5-1_*` family.

Only after a power analysis should any W3 plume runs be authorized.

## 9. STOP rule

If existing physical wind/geometry variables cannot explain or predict the W0/W1/W2 wind×edge interaction without using target-environment labeled source distributions, stop LSC/WCIG as a mainline mechanism.

Do not rescue it with a larger neural network or another source-bank statistic.