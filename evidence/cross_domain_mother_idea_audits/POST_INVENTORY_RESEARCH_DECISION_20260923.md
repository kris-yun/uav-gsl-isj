# Post-inventory research decision — 2026-09-23

Branch: research/cross-domain-mother-idea-audits-20260923

Status: **NO NEW METHOD PROMOTED**

## 1. What the dynamic-information audit actually established

The accepted PMFS runs used:
- 200 recording steps;
- deltaTime = 0.2 s;
- nominal 40 s candidate-internal model time;
- one fixed PMFS-estimated 2D wind grid per candidate rollout.

The internal candidate simulator therefore computes ordered dynamics and then collapses them into a single static occupancy-frequency map via hitMap[cell] /= timesteps.

The attempted in-loop dynamic export failed Native parity because asynchronous runtime overhead perturbed the closed-loop execution. The prototype was correctly removed.

This parity failure is **not** evidence that the internal dynamics are scientifically unavailable. It is evidence that they must not be observed by adding I/O inside the live asynchronous run.

## 2. New prerequisite: deterministic post-run candidate replay

Before testing any mother theory that needs candidate-internal dynamics, build a standalone, offline replay of the existing PMFS candidate transport kernel.

The replay must consume only artifacts/parameters available at the source-update decision time:
- occupancy/grid metadata;
- final candidate leaf geometry;
- frozen source-update id;
- native random seed / transport substream;
- PMFS estimated_wind.csv at that source update;
- accepted runtime simulation parameters;
- candidate sampled-source contract.

It must NOT consume:
- true source;
- future wind;
- future gas;
- future robot trajectory;
- GADEN full-field oracle data.

### Exact reproduction gate

For each replayed candidate, before any new dynamic diagnostic is trusted:

1. reproduced sampled source point must match the Native candidate contract;
2. reproduced final time-averaged hit probabilities on the observed support must match candidate_support_alignment.csv;
3. reproduced native candidate score must match the accepted Native score;
4. candidate identity and final-leaf mapping must match.

If exact or pre-frozen numerical parity cannot be established, STOP. Do not use replay-generated dynamics as scientific evidence.

Only after this gate may the replay expose:
- per-step occupied cells;
- active filament count;
- filament centroid/covariance;
- transition counts;
- sparse dynamic occupancy.

This avoids any closed-loop observer effect.

## 3. Mother-theory priority after the inventory

### Priority A — transfer operators / Perron–Frobenius

Why now:
- the available internal primitive is literally particle/occupancy transport under a source injection and fixed estimated wind;
- transfer-operator theory acts on the evolution of densities/occupancy, not on static plume appearance;
- no time-varying oracle wind is required for the first necessary-mechanism test.

First kill test:
- using deterministic replay only, estimate a candidate-internal transition operator or coarse Markov transport operator;
- test whether source identity is carried by operator action / occupancy-flow evolution across old and independent plume development cases;
- test source × transport identity before localization.

Do not construct a localization posterior until this mechanism passes.

### Priority B — trajectory ensembles / large deviations

Why:
- the PMFS transport RNG can in principle generate source-blind stochastic replicas;
- this directly addresses stochastic realization mismatch rather than trying to find one invariant static statistic.

But:
- one replay trajectory is insufficient;
- replicas require a separately frozen computation budget / key schedule;
- no truth-based replica selection.

First kill test:
- same-source path/action distributions must be more similar across realizations than wrong-source distributions;
- must survive CStar source/transport intervention.

### Priority C — Mori–Zwanzig, faithful version

The direct proxy already failed.

A faithful model-internal test becomes possible only after deterministic replay parity, because the ordered candidate dynamics then exist.

However this still tests **model-internal unresolved memory**, not the true plume's hidden dynamics. Therefore it is lower priority than transfer-operator and trajectory-ensemble tests.

### Deferred — fluctuation/response theory

Current frozen accepted data are insufficient for an honest online response-law test:
- candidate rollout uses one fixed 2D wind grid;
- historical intermediate PMFS estimated-wind grids were overwritten;
- GADEN time-varying 3D wind is simulator oracle.

A future experiment may log causal estimated-wind history prospectively, but the frozen accepted runs cannot supply it.

### Deferred / oracle-only — LCS / FTLE

Time-resolved full spatial velocity fields exist in GADEN, but they are oracle data. They may be used as an offline explanatory diagnostic, not as evidence for a deployable online method unless an online spatial-wind estimator history is prospectively logged.

### Deferred — intervention equivariance

Needs paired source-fixed transport interventions with source-conditioned forward state, not merely scalar measured histories.

## 4. Immediate order of work

1. Do not touch the live PMFS runtime.
2. Build deterministic offline replay.
3. Prove replay parity against accepted candidate banks.
4. If parity passes, audit transfer-operator necessary mechanism first.
5. If that fails, audit trajectory-ensemble / large-deviation mechanism.
6. Only after a mother theory passes old + independent-plume + source/transport identity gates may a method name or localization construction be created.

## 5. Core lesson

The next main innovation should not be another statistic computed from the already-collapsed hitMap.

The scientifically meaningful opportunity exposed by the audit is to move one level earlier in the information chain:

**source hypothesis -> transport dynamics -> time-averaged hitMap**

and test whether source identity exists in the transport dynamics themselves before temporal aggregation destroys it.
