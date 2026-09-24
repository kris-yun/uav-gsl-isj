# STDB-v1 Scientific Charter — Stochastic Transition-Density Belief for UAV Gas Source Localization

Date: 2026-09-24
Branch: `research/stochastic-transition-density-belief-v1`
Status: **SCREENING ADVANCE — NOT YET MAIN-INNOVATION CONFIRMED; NO CLOSED LOOP**

## 1. Failure-derived scientific problem

The accumulated House02 evidence rejects deterministic plume-surrogate escalation.

Frozen source-lineage L1 showed:
- moving from matched 2-D transport to deterministic 3-D physics improves held-out next-centroid error by about 74–75%;
- learned deterministic lineage residual improves over 3-D physics by only about 0–2%;
- destroyed-lineage controls are essentially unchanged.

Independent review explains why:
GADEN injects about 0.01 m/axis of stochastic displacement per 0.1-s step.
Across the 5–6 steps separating saved snapshots this gives an irreducible random-walk scale of about 0.022–0.024 m/axis, essentially equal to the deterministic 3-D residual.

The normalized 3-D residual kernel is approximately:
- zero mean in X/Y;
- standard deviation about 0.009–0.0102 m / sqrt(step);
- weak X/Y cross-correlation;
- nearly source- and wind-invariant.

Therefore the unresolved state is not another deterministic field correction.

> The inverse problem should propagate a conditional transport **distribution**, not predict one realization and score its field error.

## 2. Main scientific object

For each source candidate s, define a causal stochastic transport semigroup / transition density

[
p_s(x,t) = p(x_t=x\mid X_0\sim B_s,\,W_{0:t},O).
]

The source candidate is an initial/injection condition. It does not parameterize a candidate-specific network.

The observation likelihood is marginalized over transport uncertainty:

[
L_t(s)
=
\int p(y_t\mid x_t,x_t^{UAV})\,
p_s(x_t,t)\,dx_t.
]

PMFS keeps its source probability-map output:

[
P_t(s)
\propto
P_{t-1}(s)\,L_t(s).
]

This is the main scientific claim to test.

## 3. 2026 distant-field mother theory

### Top-conference anchor

Dai Shi et al.,
**Expanding the Chaos: Neural Operator for Stochastic (Partial) Differential Equations**,
ICML 2026, arXiv:2601.01021.

Relevant idea:
learn the stochastic solution operator itself, explicitly separating stochastic forcing from deterministic dynamics rather than predicting only a mean trajectory/field.

### Mathematical bridge

Li Zeng, Xiaoliang Wan, Yaobin Wang, Fabio Nobile, Tao Zhou,
**A transition-density-based operator learning method for Fokker-Planck equations with various initial conditions**,
arXiv:2606.09434 (2026).

Relevant idea:
learn the transition PDF p(x|x0,t); solutions for new initial conditions follow from the transition density / Chapman-Kolmogorov relation.
This maps naturally to GSL because each candidate source is a different injection / initial condition.

These papers are theoretical parents, not the claimed novelty.

## 4. Prior-art boundary

Occupied and forbidden novelty claim:

Maurizio Carbone & Lorenzo Piro,
**Learning Backward Transport for Source Localization**,
arXiv:2607.26892 (2026).

That work uses chemical-source detections as source-to-sensor paths and formulates localization through a Schrödinger bridge / learned backward propagator / Langevin source sampling.

Therefore STDB-v1 must NOT claim:
- first stochastic transport method for chemical-source localization;
- Schrödinger-bridge source localization;
- learned backward transport;
- Langevin source backtracking.

Target boundary, if later confirmed:

> **forward candidate-conditioned stochastic transition-density marginalization inside a PMFS-style source posterior, where source candidates are injection conditions of one shared stochastic transport law.**

A targeted 2026 literature screen has not found this exact forward transition-density + PMFS construction. This is provisional, not exhaustive novelty clearance.

## 5. Development evidence already obtained

### 5.1 Universal stochastic-kernel necessary condition — PASS

From 8 × 20,000 compact raw-filament transitions:
- XY normalized residual std ≈ 0.009–0.0102 m/sqrt(step);
- residual means ≈ 0;
- 8-cell classification accuracy from XY residual ≈ 13.6%, near 12.5% chance;
- source/wind AUC from XY residual ≈ 0.525.

Interpretation:
the unresolved XY transport noise is approximately shared rather than source-specific.

### 5.2 Reactive-current control — NO-GO

A cheap Transition-Path / reactive-flux proxy was compared against probability occupancy:
- probability occupancy / transfer density source identity: 8/8;
- directional reactive crossing flux proxy: 2/8.

Do not promote Reactive Flux Matching / committor/current as the main mechanism.

### 5.3 Hard 20-candidate stress set — PASS as mechanism screen

Truth S2 plus 19 nearby PMFS confounders was used only as a stress test.
With a physical, time-varying GADEN filament observation width and converged stochastic ensembles, both independent S2-W2 plume realizations put truth at rank 1.

This set is truth-centered and therefore not an authoritative inference gate.

### 5.4 Full native PMFS candidate bank — PASS for relative source-identifiability signal

The authoritative source-blind bank contains 180 native PMFS candidates.
Exact truth is NOT inserted.
Nearest native candidate to S2:
- `quadtree_4_35_5_4`
- distance to truth: 0.5653287467 m.

Using the frozen physical observation kernel and 200 random source-blind spatial probe sets:

At 50 spatial probes × 10 target times:
- plume A deterministic median rank: 35.5; stochastic: 3
- plume B deterministic median rank: 34.5; stochastic: 2

At 100 spatial probes × 10 target times:
- A deterministic median rank: 44; stochastic: 1
- B deterministic median rank: 42; stochastic: 1

This establishes a full-bank distributional source-identifiability signal, but these counts are NOT UAV measurement counts because each spatial probe is repeated at all ten target times.

### 5.5 Corrected total-observation audit — PASS for relative benefit, NOT final source localization

The evaluation was corrected to sample N TOTAL spatiotemporal measurements.

Density→hit calibration was frozen using S1-W2 A/B only; S2-W2 never tunes calibration.

For 30 total observations:
- A: deterministic median rank 26.5 -> stochastic 4; median MAP error 6.395 -> 1.747 m
- B: deterministic median rank 12 -> stochastic 2; median MAP error 1.972 -> 0.747 m

For 50 total observations:
- A: rank 16 -> 4; MAP error 3.221 -> 1.747 m
- B: rank 5.5 -> 1; MAP error 1.972 -> 0.565 m

For 100 total observations:
- A: rank 11.5 -> 3; MAP error 1.972 -> 1.747 m
- B: rank 4 -> 1; MAP error 1.747 -> 0.565 m

Thus stochastic marginalization remains load-bearing after correcting the earlier probe-count interpretation.

However plume A still has negative median nearest-candidate margin. STDB-v1 is not yet confirmed.

### 5.6 Calibration-free point-process control — NO-GO

A scale-marginalized conditional-count Poisson point-process likelihood was tested.
It was substantially worse than the frozen S1-only calibrated hit likelihood.

Do not use it as an auxiliary innovation to rescue STDB.

### 5.7 Historical single-UAV route 10-observation proxy — FAIL / INFORMATION-LIMITED

Two source-blind historical House02 x/y paths were aligned exactly to the 10 opened C0.5 target snapshots.

Observed S2-W2:
- plume A: only 3/10 hits on each route;
- plume B: 0/10 hits on both routes.

Nearest-truth candidate remains poorly ranked.

This blocks any deployment/closed-loop claim from the current offline data.

Important limitation:
the historical path is at z=0.3 m while the C0.5 development field is the z=0.2 m sensor slice.
This is a conservative geometry proxy, not formal flight validation.

## 6. What is frozen and what is not

Frozen scientific mechanism:
- deterministic 3-D physical drift;
- stochastic transport distribution rather than deterministic realization;
- candidate source as injection/initial condition;
- marginal observation likelihood;
- PMFS probability-map output.

NOT frozen:
- real-time density solver/operator architecture;
- estimated-wind implementation;
- exact online sensor observation model;
- closed-loop planning behavior.

Do NOT train a neural operator merely to improve House02 accuracy.
A learned stochastic operator is permitted later only as an amortized real-time approximation to a mechanism that has already passed causal/source-rank gates.

## 7. Next decisive gate

Before any ROS/PMFS closed loop:

1. extract a full 566-snapshot route-aligned S2-W2 A/B gas trace from the already-existing raw House02 GADEN bank;
2. use source-blind historical navigation paths, not truth-selected probe locations;
3. use only current/past observations in sequential posterior updates;
4. compare:
   - Native-style/deterministic transport likelihood;
   - STDB stochastic-marginalized likelihood;
5. report nearest-truth native candidate rank and MAP source error versus observation count.

Required development signal:
- both independent plume realizations must show lower median/final rank or source error than deterministic transport;
- improvement cannot depend on oracle future observations;
- all-miss trajectories must remain mathematically defined;
- if route-aligned sequential evidence does not improve in BOTH A/B, **STOP STDB AS MAIN INNOVATION**.

Only a pass authorizes estimated-wind/W0 and then closed-loop integration.

## 8. Real-world rule

No future GADEN wind, source truth, true concentration field, or simulator filament state may appear in deployment inference.

The production state must use current/past estimated wind and UAV gas observations only.

House02 remains development-only.
Fresh House01/03 and real-flight confirmation stay unopened until STDB-v1 passes the route-aligned causal gate.
