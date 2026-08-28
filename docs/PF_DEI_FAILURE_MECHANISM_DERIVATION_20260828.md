# PF-DEI failure-mechanism derivation

Date: 2026-08-28

Status: **DERIVATION / NOT A PERFORMANCE CLAIM / NOT A FROZEN INFERENCE ARCHITECTURE**

This note converts the accumulated negative evidence into falsifiable mechanism hypotheses before the forward-operator closure result is known.

## 1. Established facts

The following are already established and must not be softened later:

- V5 passive cumulative evidence remains inactive across all 30 development OFF runs.
- V6-A removes hard source components and still gives 0/30 continuous predictive pass.
- Source-transfer-only pass is H01 1/10, H02 0/10, H03 2/10.
- Absolute adequacy is 0/30.
- Existing CTT occupancy is an any-filament cell-occupancy event, not concentration in ppm.
- Native PMFS uses measured concentration samples, averages the consumed measurement block, and thresholds the mean.

Therefore component fragmentation and gate strictness are not sufficient explanations.

## 2. Current strongest mechanism hypothesis

### Trajectory-dependent observation aliasing

The old models effectively assume a local observation relation

`Y_b ~ p(Y | S, Z_c, x_b)`.

The native simulator instead has a history-dependent chain

`S -> Z_c -> C_t -> R_t -> M_t -> Y_b`,

with sensor state `R_t` potentially carrying information from earlier poses and contexts.

Thus the correct conditional object is closer to

`p(Y_b | S, Z_{1:c}, x_{0:t_b}, C_{0:t_b}, R_{t_b^-})`,

not a function of the current stop cell alone.

If two seeds reach the same cell with different exposure histories, they can legitimately produce different measured sequences under the same source. A local occupancy/frequency likelihood then attributes sensor carry-over to the current candidate source and can reverse source ranking across seeds or contexts.

This mechanism directly predicts the historical pattern: some trajectories accidentally make the proxy locally valid, while others produce systematic ranking errors that Bayesian accumulation amplifies.

## 3. Misspecification decomposition

Write the true run likelihood schematically as

`L_true(S) = log ∫ p(M_{1:T},R_{1:T},Z_{1:C} | S, design) dR dZ`.

The historical proxy is closer to

`L_proxy(S) = Σ_j log Bernoulli(r_j ; p_occ(S,j))`.

The gap is decomposed into four scientifically distinct terms:

1. **Observation-operator error**: filament occupancy is substituted for physical/measured concentration.
2. **Sensor-state omission**: run-persistent response/recovery memory is ignored or reset.
3. **Temporal aggregation error**: correlated measured samples and nonlinear block averaging/thresholding are replaced by one hit frequency.
4. **Transport-family error**: even with the correct observation operator and sensor model, the simulated concentration family may still fail to cover obstacle turning, recirculation or other real transport modes.

Only item 4 should be called a transport-family insufficiency. The current evidence does not yet identify its magnitude because items 1--3 are already known to be wrong or unresolved.

## 4. Fast falsification ladder after forward closure

All tests below are simulation-only or truth-blind until a method is frozen.

### F1 — sensor-history counterfactual

Construct two synthetic trajectories with the same source, same transport realization and identical concentration sequence during an evaluation stop, but different pre-stop exposure histories:

- history A: clean-air prehistory;
- history B: high-exposure prehistory.

Then feed both through the native persistent sensor.

If measured ppm or the final block decision differs during the identical evaluation exposure, the local-stop conditional-independence assumption is formally falsified.

This test isolates sensor memory without requiring H01/H02/H03 source truth.

### F2 — ideal-sensor versus native-sensor transfer

Using exactly the same physical concentration forward traces, compare truth-blind cross-context source transfer under:

- ideal observation: direct concentration / exact block averaging without sensor memory;
- native observation: persistent dynamic sensor and the real measured sequence.

Interpretation:

- ideal succeeds, native fails -> sensor dynamics are a dominant blocker;
- both fail -> transport/source forward family remains inadequate;
- native succeeds but occupancy proxy fails -> observation operator is the dominant blocker.

No House-specific threshold may be introduced.

### F3 — occupancy proxy versus physical-concentration forward

Matched ablation, same source candidates, nuisance draws, poses and timestamps:

A0. historical occupancy/frequency proxy;
A1. physical concentration with ideal sensor;
A2. physical concentration with native persistent sensor.

The difference A1-A0 estimates the cost of the old observation proxy; A2-A1 estimates the incremental effect of native sensor dynamics on source evidence.

These are mechanism diagnostics, not localization-performance claims.

### F4 — finite transport family versus physics-randomized transport

Only if A2 is still inadequate, expand nuisance randomization in the authoritative GADEN forward model while keeping the observation chain fixed.

If adequacy improves only after broader nuisance randomization, then the finite CTT transport family is genuinely under-dispersed / structurally incomplete.

## 5. Why raw measured samples are one trajectory, not 80 independent replicates

Let the measured sequence be `M_1,...,M_T`. The correct evidence is sequential/history-dependent:

`p(M_{1:T}|S) = ∫ p(M_{1:T},R_{1:T},Z_{1:C}|S) dR dZ`.

It is invalid to replace this by `∏_t p(M_t|S)` unless conditional independence is proven after conditioning on the state. With dead time, response/recovery dynamics, plume persistence and shared transport, that independence generally does not hold.

This is why a simulation-based or state-space inference engine is preferred after forward closure.

## 6. Candidate PF-DEI-SBI derivation after forward closure

This section is a pre-derivation only. Architecture is deliberately not frozen.

Let `D` denote the complete causally available prefix: measured ppm, timestamps, poses, available wind and block boundaries. Let `kappa` denote fixed design/context information. The forward simulator samples nuisance variables `Z` and runs the persistent sensor internally.

A candidate-conditioned neural ratio estimator can be trained by contrastive simulation:

Positive pairs:
`S ~ q0(S|kappa), D ~ p(D|S,kappa)`.

Negative pairs:
keep the same `D,kappa` but pair with `S^- ~ q0(S|kappa)` independently.

With balanced positive/negative classes, the optimal classifier logit satisfies

`f*(D,S,kappa) = log p(D|S,kappa) - log p(D|kappa)`.

Therefore the source posterior is

`q(S|D,kappa) ∝ q0(S|kappa) exp(f(D,S,kappa))`.

Key properties:

- context-specific transport and run-persistent sensor state are marginalized by simulator randomization;
- no independence assumption over raw samples is needed;
- candidate sources can be scored on a common geometry prior;
- negative sources must be sampled within the same design/context to prevent House identity or trajectory metadata from becoming a shortcut;
- training on random valid prefixes yields an online/sequential estimator without retraining at every source update.

Whether NRE, NLE or another SBI engine is finally used must wait for forward-operator closure and synthetic calibration.

## 7. Calibration and falsification requirements for any later SBI

Before touching development localization error:

- simulation-based calibration on held-out synthetic sources;
- candidate/source permutation invariance;
- nuisance-seed holdout;
- sensor-state initialization/persistence stress tests;
- random-prefix calibration for online use;
- same-context negative sampling to prevent House leakage;
- at least one leave-one-transport-family-out misspecification test;
- an absolute posterior-predictive adequacy check, because relative source ranking alone can be confidently wrong.

The old minimum-KL/I-projection assimilation remains a possible safety layer, but no assimilation rule is frozen until the new source evidence is calibrated.

## 8. Mechanism verdicts to return once the forward-operator data arrive

Return one of the following mechanism labels, not an ambiguous narrative:

- `OBSERVATION_PROXY_DOMINANT`
- `SENSOR_MEMORY_DOMINANT`
- `TRANSPORT_FAMILY_DOMINANT`
- `MIXED_OBSERVATION_SENSOR_TRANSPORT`
- `FORWARD_OPERATOR_STILL_UNRESOLVED`

The label must be justified by F1--F4, not by localization performance.
