# CODEX — PF-SNRE ONE-SHOT FINAL QUALIFICATION → CLOSED LOOP → ABLATION

Date: 2026-08-29
Branch: `research/pf-sbi-final-one-shot-20260829`
Execution class: ONE INTEGRATED PIPELINE WITH INTERNAL HARD STOP GATES

Read first: `docs/PF_SNRE_FINAL_RECONSTRUCTION_AFTER_V2_20260829.md`.

The purpose of this contract is to end the iterative experiment loop. Do not return after each internal stage asking what to run next. Execute the stages below in order. If a hard gate fails, terminate the PF-SNRE line and package all evidence. If a gate passes, continue automatically to the next authorized stage without changing formulas, architecture, thresholds or hyperparameters.

## 0. Frozen scientific identity

V2 branch/commit is frozen historical development evidence:

- branch: `research/pf-dei-direct-set-nre-v2-20260829`;
- commit: `14642cf18f7a20b8267daef612f61e3c5f2be163`;
- result remains `PF_DEI_DIRECT_SET_NRE_V2_NO_GO` under its old preregistered gate.

Do not rewrite or relabel it.

Final method candidate:

**PF-SNRE — Physics-Factorized Set Neural Ratio Estimation**.

Network architecture/training semantics are frozen from Direct Set-NRE V2. H01 is development data. No further H01-driven architecture/hyperparameter tuning is permitted.

No TCN, Transformer, recurrence, TrajCast, temporal-coherence identity, adjacent-difference module, A0 rank-Gaussian mapping, temperature, PMFS blend coefficient, active probe or outcome-selected threshold is authorized.

## 1. Preflight provenance and compute budget

Record before work:

- git HEAD and clean status;
- Python/PyTorch/NumPy versions;
- ROS2/GADEN/build hashes;
- bank manifest and shard hashes;
- H01/H02/H03 carrier manifests and q0 hashes;
- train/reserved nuisance member identities;
- all available historical OFF archives and source-update manifests.

Do not rerun GADEN to create offline training data in Stages 2–5. Reuse the existing `PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1` / field assets.

Timing targets based on frozen H01 V2 evidence:

- one 12k-step model was ~134 s CPU;
- historical 50-case inference was ~3.6 s.

Therefore data materialization + 3 LOHO trainings + source-sweep qualification should be minute-scale to tens-of-minutes, not hours. If offline qualification exceeds 45 min, inspect I/O/vectorization before proceeding; do not reduce sources/members/cases to hide a slow implementation.

## 2. Materialize H02/H03 measured-domain datasets from existing physics only

Construct H02 and H03 equivalents of the frozen H01 training representation using the existing train8 physical streams and the exact persistent sensor forward model.

Required per House:

- candidate sources = all legal region carriers;
- 8 frozen predictive training nuisance members;
- 30 existing train trajectory schedules;
- measured-domain samples from the exact sensor forward operator;
- authoritative observed-block/source-update manifests for historical OFF trajectories when available;
- carrier q0 and free-area/free-count metadata;
- stable source/member/trajectory hashes.

No source outcomes are used to choose preprocessing.

Run exact sensor forward parity and block-boundary parity. Any unexplained mismatch => `PF_SNRE_DATA_CONTRACT_FAIL` and STOP.

## 3. Freeze shared, House-agnostic V2 architecture

Use exactly the V2 structural design:

- candidate-conditioned member set;
- member encoder on observation / prediction / residual / absolute residual;
- permutation-invariant member moments;
- block encoder with normalized local geometry/context;
- permutation-invariant visible-block aggregation;
- ratio head outputs one scalar log likelihood-ratio factor;
- no House ID;
- no PMFS posterior input;
- final posterior `q(s|D) proportional to q0(s) exp(f_theta(s,D))`.

House-specific coordinate normalization may use only map/carrier extents available before source outcomes. It is preprocessing, not training.

Training semantics per example:

- choose training House according to a fixed uniform House sampler among the Houses allowed in that fold;
- source proposal uniform over that House's legal carriers;
- generating nuisance member uniformly selected and strictly excluded from all candidate predictive sets (8 -> 7 LOMO);
- negative candidate is an independent uniform carrier draw from the same House;
- trajectory sampled only from allowed training trajectories;
- visible update/prefix sampled without localization outcomes.

Frozen optimizer/budget from V2:

- AdamW, lr `3e-4`, weight decay `1e-4`;
- hidden width 32 and unchanged layer sizes;
- 12,000 maximum steps;
- batch semantics equivalent to V2;
- checkpoint selected only by simulated validation BCE;
- no early decision from held-out-House metrics.

Use deterministic model seed `3301` for every LOHO fold so the only changed factor is the held-out House.

## 4. Three leave-one-House-out (LOHO) models — no test-House training

Train exactly three primary models:

- test H01: train H02+H03;
- test H02: train H01+H03;
- test H03: train H01+H02.

Within each training House:

- trajectories 10..24 = train;
- trajectories 25..29 = validation;
- trajectories 0..9 are not used for neural optimization.

The held-out House is absent from training and checkpoint selection entirely.

Report per fold:

- initial/best validation BCE and best step;
- source exposure min/median/max per training House;
- training wall time;
- checkpoint SHA;
- strict LOMO proof;
- member/block permutation parity.

No model selection across folds. Each fold's seed3301 minimum-validation-BCE checkpoint is fixed.

## 5. One comprehensive offline qualification

This stage has two complementary evaluation panels. It is the only offline gate before runtime integration.

### 5A. Multi-source held-out-House source sweep

Purpose: eliminate the single-H01-source / lucky-map-centroid artifact.

For each held-out House:

1. Select 32 source carriers using deterministic geometry-only spatial coverage before any inference result. Use a stable k-center/farthest-point procedure seeded only by carrier IDs/centroids and include all free-count strata where possible. Save the selected IDs before scoring.
2. Use reserved nuisance realizations as pseudo-observations. Generating reserved member must never be in the train8 predictive ensemble.
3. Use two deterministic reserved trajectory schedules chosen by lexicographic schedule SHA (first and last after sorting), not by performance.
4. Evaluate all five source-update prefixes.

Thus each House has at least `32 sources x reserved observations x 2 trajectories x 5 updates`; use all 4 frozen reserved nuisance members if available under the current bank contract.

For every case score all candidate carriers with:

- PF-SNRE LOHO model;
- geometry-only q0;
- frozen nonlearned physics comparator (use one already frozen method, not a newly designed score);
- source-label permutation/null control.

Primary spatial estimator: the same posterior point-estimator contract intended for closed-loop evaluation. If the paper evaluator uses posterior mean, use the posterior mean of carrier/free-cell coordinates here and freeze that exact rule.

Report:

- point-location error;
- posterior spatial energy score / equivalent predeclared spatial proper score;
- posterior mass within 1 m and 2 m where map resolution supports it;
- likelihood/density true-source rank using `f_theta` or `q(s)/A_s`;
- posterior-mass rank as secondary only;
- entropy/max mass;
- credible-set inclusion and false-confidence events.

### 5B. Actual historical held-out-House source-update panel

Use H01/H02/H03 historical OFF seeds0..9 x their five authoritative source-update prefixes, with the corresponding LOHO model that never trained on that House.

Compare:

- Classic PMFS;
- q0-only;
- PF-SNRE LOHO posterior.

Do not tune from these results.

### 5C. Simulation-based calibration panel

Create a calibration-only pseudo-observation panel from the held-out House reserved bank using sources sampled according to q0 and held-out nuisance members. Do not use historical localization outcomes.

Report at minimum:

- empirical coverage of 50% and 90% highest-posterior-mass credible sets;
- SBC/rank histogram or discrete equivalent;
- max-posterior-mass vs spatial-error relation;
- count of false-confident cases.

A false-confident case for this contract is: the true carrier is outside the 90% credible set while maximum posterior carrier mass >=0.5. This definition is frozen before evaluation.

### 5D. Offline qualification gate

Call `PF_SNRE_LOHO_OFFLINE_QUALIFIED` only if ALL hold:

1. **Multi-source spatial value:** pooled source-sweep mean point-location error improves >=20% versus q0-only and >=10% versus the frozen nonlearned physics comparator.
2. **No House collapse in source sweep:** every held-out House improves >=10% versus q0-only on mean point-location error.
3. **Historical cross-House value:** across the three held-out-House historical panels, pooled PF-SNRE mean point-location error improves >=10% versus Classic PMFS and no House mean degrades >5%.
4. **Evidence identifiability:** pooled median normalized density/evidence rank <=0.25, every House <=0.35, and source-label permutation is significantly worse (`p < 0.01`, predeclared paired/permutation test).
5. **Calibration safety:** empirical 90% credible-set coverage >=80%; false-confident count <=1% of calibration cases and not greater than the corresponding PMFS count when PMFS credible sets are defined.
6. **Physics dependence:** a no-physics diagnostic (candidate predictive ppm replaced by a deterministic member/source permutation independent of truth, with all other inputs unchanged) loses at least half of PF-SNRE's source-sweep improvement over q0. This is a leakage check, not a tunable ablation.

If any condition fails: return `PF_SNRE_FINAL_OFFLINE_NO_GO`, package evidence, STOP THE ENTIRE PF-SNRE LINE. Do not create V3, change the loss, enlarge the network or retrain on the failed House.

If all pass: freeze all three LOHO checkpoints, preprocessing, q0 adapter, estimator rule and runtime tensors; continue automatically.

## 6. Runtime implementation — only after offline qualification

### 6.1 Predictive provider

The runtime provider must answer candidate/member physical concentration at arbitrary causally visited `(x,y,z,t)`. Historical trajectory tensors are not sufficient for ON closed loop.

Prefer existing trajectory-independent GADEN field assets/cache. If only historical trajectory samples exist, build one reusable field/query asset per House **once**; do not regenerate per run.

Record field/provider hashes.

### 6.2 Sensor space

PF-SNRE consumes measured-domain observation blocks. Candidate physical predictions are passed through the exact frozen persistent sensor forward operator before entering the network. Do not use `true_gas_ppm`.

### 6.3 Inference runtime

Do not introduce a large new runtime dependency if avoidable. The network is only small affine/SiLU/pooling layers. Preferred implementation order:

1. existing in-process supported TorchScript/libtorch/ONNX runtime if already installed and reproducible;
2. otherwise implement the frozen small forward pass in C++ from exported weights.

No subprocess-per-update workaround.

Require Python vs runtime logit maximum absolute error <=1e-5 on deterministic fixtures and posterior mass error <=1e-6.

### 6.4 Online adapter

At each native PMFS source-update event:

1. Classic PMFS may still compute its native posterior for baseline logging;
2. PF-SNRE scores all carriers from only observations available up to that event;
3. compute `q(s|D) proportional to q0(s) exp(f_theta)`;
4. map region mass to free cells exactly and replace only the `sourceProbability` channel for ON;
5. keep native hit probability, sensor, planner, movement, update cadence and stopping rules unchanged.

No blending with PMFS.

## 7. Shadow gate

Run OFF vs PF-SNRE SHADOW for one timing/provenance seed per House. SHADOW computes full PF-SNRE but must not write `sourceProbability`.

Require exact equality of native behavior:

- trajectory / motion commands;
- PMFS native sourceProbability seen by planner;
- HIT/NOTHING sequence;
- stop/update timing;
- simulator RNG identity where applicable.

Measure PF-SNRE source-update latency. Require worst-case inference + provider materialization comfortably below the PMFS source-update interval; target <1 s and report actual p50/p95/max.

Any side effect or runtime parity failure => `PF_SNRE_SHADOW_FAIL` and STOP.

## 8. Final paired closed-loop confirmation — unseen seeds10..19 only

Do not run a result-driven development matrix first. The architecture and LOHO models are already frozen.

For each House H01/H02/H03 and seeds10..19:

- OFF = unmodified Classic PMFS;
- ON = PF-SNRE using the LOHO model trained on the other two Houses;
- exact paired simulator/source/wind contracts;
- 300 s horizon or the frozen benchmark horizon;
- no retraining, tuning or threshold change between runs.

Total: 30 OFF/ON pairs = 60 arms.

Primary closed-loop gate:

- pooled expected/final localization error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero **new** false-confident collapses relative to OFF under the frozen project definition; if the project definition is absent, use the Stage5 calibration definition and report both posterior confidence and final error;
- pair/runtime contracts all PASS.

If this fails: `PF_SNRE_CLOSED_LOOP_NO_GO`, STOP. Do not retrain from seeds10..19.

If this passes: `PF_SNRE_CLOSED_LOOP_GO`; freeze FULL results and continue to ablation only.

## 9. Frozen ablations after FULL GO

Do not alter FULL after seeing ablations.

### 9.1 Offline mechanistic ablation matrix

Run the complete multi-source source-sweep and historical panels for:

- FULL PF-SNRE;
- `ABLATE_NUISANCE_SET` — replace member set with its predictive mean while keeping downstream architecture dimensionally matched via a frozen deterministic adapter;
- `ABLATE_LEARNED_RATIO` — frozen nonlearned comparator instead of neural set-NRE;
- `ABLATE_PHYSICS_INPUT` — candidate predictive physics permuted/removed, leakage control;
- `ABLATE_Q0` — uniform carrier mass, diagnostic only.

### 9.2 Closed-loop ablations

Reuse the already generated OFF and FULL seeds10..19. To control compute, run closed-loop only for the two scientifically central mechanism removals:

- `ABLATE_NUISANCE_SET`;
- `ABLATE_LEARNED_RATIO`.

Use all 30 House/seed conditions if simulator wall time permits within the same execution. Before launching, benchmark one arm and print projected total wall time. If projected ablation wall time exceeds 12 h, run a predeclared stratified subset of 5 seeds per House (`10,12,14,16,18`) for 15 conditions per ablation and document the cost-based reduction before seeing ablation outcomes.

Never select the subset from performance.

## 10. Universal deployment model artifact

Only after LOHO offline qualification and final closed-loop GO, train one **universal deployment model** on all three Houses with the same frozen architecture/training semantics and seed3301:

- train trajectories10..24;
- validation25..29;
- H01/H02/H03 balanced House sampling;
- 12k-step maximum;
- checkpoint by simulated validation BCE only.

This model is NOT used to rewrite paper validation results. It is the artifact intended for a future unseen physical room.

Deployment claim must be phrased accurately:

- no source-label neural retraining in a new room;
- environment setup still requires map/carriers, physics predictive bank or field cache, and source-independent wind/sensor calibration;
- controlled source strength Q is currently part of the benchmark contract. If real Q is unknown, add Q as a simulator nuisance **before** viewing real localization outcomes, otherwise state the controlled-Q limitation.

## 11. Evidence package

At final STOP/GO produce one immutable package containing:

- all git/model/provider hashes;
- data/split manifests;
- LOHO training summaries;
- source-sweep/calibration/historical qualification;
- no-physics leakage diagnostic;
- Python/runtime parity;
- shadow evidence;
- 30-pair closed-loop raw/evaluator outputs;
- ablation outputs if FULL GO;
- timing/RSS/CPU/GPU summaries;
- final decision JSON with every predeclared gate as boolean;
- README distinguishing DEVELOPMENT, OFFLINE-QUALIFICATION, CONFIRMATORY-CLOSED-LOOP, and ABLATION evidence.

Return exactly one final status among:

- `PF_SNRE_FINAL_OFFLINE_NO_GO`;
- `PF_SNRE_SHADOW_FAIL`;
- `PF_SNRE_CLOSED_LOOP_NO_GO`;
- `PF_SNRE_CLOSED_LOOP_GO`.

Do not automatically invent a follow-up method after a NO-GO.