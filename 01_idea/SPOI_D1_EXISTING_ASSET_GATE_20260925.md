# SPOI D1 Existing-Asset Transport-Context Gate — 2026-09-25

Status: **FROZEN BEFORE W2/occupancy BYTES ARE INSPECTED**

No new GADEN plume simulation is allowed.

## 1. Data

Use only:
- D1R 168 sources x16 realizations x10 times x30 probes;
- frozen D1R 168-source panel;
- Gate1A probe/observation contract;
- existing canonical House02 W2 wind_iteration_0..10;
- existing House02 OccupancyGrid3D.csv.

## 2. Outer generalization contract

Cross two axes:

### Source holdout
Checkerboard split of the dense 24x7 source panel:
- 84 source cells completely excluded from model fitting;
- opposite parity evaluated;
- repeat both parities.

### Realization holdout
- direction A: train references 1..8, evaluate 9..16;
- direction B: train references 9..16, evaluate 1..8.

Total: four outer sourceheldout x realization directions.

All source hypotheses remain in the final 168-cell posterior.

## 3. Physical input field

For every candidate source s construct the same deterministic operator input:

a_s = {
  source-injection indicator at s,
  occupancy/free-space field,
  canonical W2 spatial wind sequence/statistics,
  frozen source/probe coordinate metadata
}.

Wind/geometry may not be reconstructed from target plume realizations.

## 4. Query/output space

The predictive function evaluated at D1 is the frozen 10x30 observation field.

A later full-field test may use 10x83x119 concentration cubes only after D1 ADVANCE.

## 5. Sparse observation operators

Predeclare fixed deterministic query masks using RNG seed 2026092501.

Observation budgets:
- M=20 queries;
- M=100 queries;
- full M=300 diagnostic.

For M=20 and M=100 generate 16 masks each, uniformly without replacement from the 300 registered queries.

All candidate methods see identical masks.

Full-300 is diagnostic because current D0 shows stochastic rank may be most useful under partial observation.

## 6. Common inference output

Every method must return a normalized probability over the same 168 source cells.

Uniform microcell prior unless a separate frozen PMFS prior is explicitly supplied to all arms.

Primary per-target score:

log2 q(true_source | observed_queries, context).

## 7. Model ladder

Use a common deterministic context backbone where applicable.

### A0 deterministic mean / rank-0
Predict only the conditional plume mean from source+wind+geometry context.

### A1 diagonal heteroscedastic
Predict mean plus independent query variances.

### A2 shared low-rank covariance
Predict mean plus one global low-rank stochastic basis/spectrum.

### A3 shared basis + source-conditioned spectrum
Shared basis, input-conditioned latent variances.

### A4 input-dependent-basis DLL-lite
Input-conditioned mean, input-conditioned low-rank basis and input-conditioned coefficient covariance.
No diffusion/flow matching yet.

### A5 full DLL
Not authorized at D1. Only considered after A4 ADVANCE.

## 8. Ordinary inference champion

Include the strongest non-generative reference-only baseline:
- source-context metric/prototype model or equivalent direct discriminative candidate-context method;
- identical train-source and observation budget;
- full 168-cell posterior;
- train-only calibration.

Any stochastic-operator mainline must beat this baseline, not merely rank-0 Gaussian.

## 9. Nested selection

Within each outer training-source set:
- all stochastic rank;
- regularization;
- context-backbone capacity;
- likelihood temperature;
- calibration;
must be selected by source-heldout inner CV only.

No outer heldout source or realization may choose rank/model family.

## 10. Primary D1 endpoints

For M=20 and M=100 separately report:
- mean true-source log2 score;
- multiclass Brier score;
- fractional HPD coverage at 0.5/0.8/0.95;
- top1/top3 and MAP error as diagnostics only.

Aggregate over the 16 frozen masks only after per-mask results are saved.

## 11. D1 ADVANCE

`SPOI_D1_ADVANCE_STOCHASTIC_OPERATOR` requires all:

1. nested CV selects a nonzero stochastic rank in all four outer scenarios for at least one sparse budget M in {20,100};
2. A4 input-dependent-basis model beats A0 rank-0 on mean proper log score in all four outer scenarios at that same M;
3. A4 beats the locked ordinary inference champion in all four outer scenarios at that same M;
4. average gain over the ordinary champion >= 0.20 bit/target;
5. no material calibration degradation;
6. the selected representation uses true wind/geometry context rather than target leakage;
7. prior-art audit preserves the forward-stochastic-operator inversion distinction.

## 12. HOLD

`SPOI_D1_HOLD_STOCHASTIC_SPREAD_AUX_ONLY` if:
- A3 source-conditioned spread improves over A0/A2,
- but A4 does not consistently beat the ordinary champion.

Interpretation: source-dependent uncertainty is an auxiliary likelihood innovation, not the main paper.

## 13. STOP

`SPOI_D1_STOP_NO_OPERATOR_ADVANTAGE` if:
- nested selection returns rank 0 throughout;
- stochastic models improve field likelihood but not source proper score;
- ordinary direct inference matches/beats A4;
- results depend on outer-target-selected rank or temperature.

No rescue with new plume realizations at D1.

## 14. After ADVANCE only

Only then consider:
- packaging D1R full concentration cubes;
- reproducing the official ICML 2026 DLL coefficient diffusion layer;
- cross-wind/cross-House gate;
- PMFS closed-loop integration.
