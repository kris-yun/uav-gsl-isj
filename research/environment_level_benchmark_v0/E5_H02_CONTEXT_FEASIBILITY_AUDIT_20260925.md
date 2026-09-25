# E5 — Post-E4B H02 Context-Adaptation Feasibility Audit

Date: 2026-09-25

Status: **POSTMORTEM / ORDINARY-BASELINE FEASIBILITY ONLY — NOT A MAIN-INNOVATION PASS**

Upstream frozen decision:
`E4B_FAIL_STOP_FACTORIZED_DEFORMATION_MAINLINE`.

## 1. What E4B killed

The fixed factorized deformation hypothesis is stopped.

Frozen E4B results:
- speed-mode capture = 0.0074;
- family-mode capture = 0.4864;
- mean capture = 0.2469;
- target top-2 energies = 0.9625 / 0.9088;
- factorial interaction ||Q|| = 13.824 > 2*Nmax = 8.793;
- target effect norms are well above same-wind seed noise.

Therefore:

> low-rank deformation exists within individual environment changes, but neither a reusable single subspace nor additive speed/family factorization transfers to the untouched fourth H02 wind.

Do not revive E4A/E4B with different thresholds.

## 2. Four-wind H02 variance structure

Using all four now-open H02 canonical winds, six frozen sources, four realizations/source, 300-D log(1+ppm):

Balanced variance decomposition:
- source main effect: ~67.8%;
- wind main effect: ~8.7%;
- source x wind interaction: ~20.5%;
- seed residual: ~3.0%.

Thus environment interaction is much larger than seed noise and is a first-class part of the inverse problem.

## 3. Fixed environment-invariant representation is weak

A strong ordinary shrinkage-LDA trained on three winds and evaluated on the fourth, with train-wind-only temperature calibration, gives held-out-wind six-source accuracy roughly:
- W0: 79.2%;
- W1: 54.2%;
- W2: 50.0%;
- W3: 33.3%.

Calibrated true-source NLL is approximately:
- 1.20;
- 1.97;
- 1.91;
- 2.40 bits.

Uniform six-source NLL is log2(6)=2.585 bits.

Therefore a fixed discriminant representation contains some reusable source information but is not reliably environment invariant.

## 4. Ordinary few-context factor adaptation feasibility

Exploratory postmortem only.

For each held-out H02 wind:
- train an ordinary rank-2 environment factor model from the other three winds;
- reveal exactly two target-wind context sources and two realizations/context source;
- infer the target environment factor coefficients;
- predict the other four query-source prototypes;
- evaluate only the opposite two fresh realizations/query source;
- average over all 15 choices of the two context sources and both 2+2 realization directions.

### Query prototype prediction

Mean query-source relative-L2 prediction error:

W0:
- no context ~0.500;
- common shift ~0.572;
- factor context ~0.376.

W1:
- no context ~0.599;
- common shift ~0.697;
- factor ~0.355.

W2:
- no context ~0.613;
- common shift ~0.726;
- factor ~0.432.

W3:
- no context ~0.624;
- common shift ~0.693;
- factor ~0.561.

### Fresh query-source classification

Nearest predicted-prototype accuracy on four completely non-context source locations:

W0:
- no context ~66.7%;
- common shift ~77.5%;
- factor ~100%.

W1:
- no context ~62.5%;
- common shift ~80.8%;
- factor ~100%.

W2:
- no context ~50.0%;
- common shift ~49.6%;
- factor ~69.6%.

W3:
- no context ~66.7%;
- common shift ~62.1%;
- factor ~81.7%.

### Train-environment-only calibrated proper score

Nested train-wind temperature calibration; query true-source NLL in bits:

W0:
- no context 1.462;
- factor 1.334.

W1:
- no context 1.529;
- factor 1.242.

W2:
- no context 1.600;
- factor 1.395.

W3:
- no context 1.443;
- factor 1.384.

The ordinary factor baseline improves proper score in all four postmortem leave-one-wind-out directions.

## 5. Scientific interpretation

Supported only as a feasibility fact:

> within a fixed House/probe geometry, small labeled target-environment context can be useful for source inference even when fixed invariant source representations fail.

This does NOT establish:
- a novel main innovation;
- cross-House transfer;
- a deployable calibration protocol;
- superiority over Neural Processes, GP/Bayesian calibration, ICON/GenICON, meta-learning, or coordinate-aware operators.

Indeed, the success of a very ordinary low-rank factor baseline raises the novelty bar.

## 6. Cross-House obstacle

H01/H02/H03 use different geometry-selected probe coordinates and different source panels.

The fixed 300-D H02 factor basis is therefore not a valid cross-House model.

Do not unseal H01 DEV merely to test this House02-specific basis.

Any cross-House candidate must consume coordinates/geometry/wind/context as structured inputs and be compared against ordinary coordinate-aware NP/GP/operator baselines.

## 7. Mainline decision

Current status:
`CONTEXT_ADAPTATION_FEASIBLE_WITHIN_HOUSE_BUT_MAIN_INNOVATION_NOT_ESTABLISHED`.

H01 DEV remains sealed.
House03 remains sealed.
No new plume is authorized.

Next work is zero-simulation theory/prior-art and baseline design:
1. define the strongest coordinate-aware ordinary context baseline;
2. identify whether any GSL-specific source-information mechanism remains beyond generic context-conditioned function/operator learning;
3. only if a pre-data structural distinction exists, freeze one H01 DEV test.