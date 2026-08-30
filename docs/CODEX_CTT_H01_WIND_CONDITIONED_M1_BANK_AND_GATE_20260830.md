# CODEX EXECUTION CONTRACT — CTT H01 wind-conditioned neural first-passage M1 bank + offline gate

Date: 2026-08-30  
Status: **AUTHORIZED FOR OFFLINE PHYSICAL BANK GENERATION / TRAINING / FALSIFICATION ONLY**  
Closed loop: **NOT AUTHORIZED unless every gate in this document passes.**

## 0. Scientific objective is frozen

Do not invent a new method version. The paper-level method remains **Causal Transport Tomography (CTT)**:

`source S -> transport Z_t -> physical concentration C_t -> persistent sensor state R_t -> measured concentration M_t -> ordered event/first-passage observation Y_t`.

The neural network is **M1, a physical first-passage solver surrogate**. It is not a source classifier, posterior corrector, reliability gate, planner, or end-to-end localization network.

Frozen factorized neural output:

- `p_e(x) = P(F < never | x)`;
- `p_phi(t | event,x), t=0..79`;
- `P(F=t|x)=p_e p_phi(t|event,x)`;
- `P(F=never|x)=1-p_e`.

Frozen training loss:

`L = BCE(ever) + CE(first_passage_bin | ever)`.

No trainable weight between the two terms. No localization/rank/posterior/planner signal may enter training or checkpoint selection.

## 1. Mandatory provenance preflight

Before simulation, write `P0_PROVENANCE_PREFLIGHT.md` and stop if any item fails.

1. Create an isolated worktree/branch from `research/ctt-causal-first-passage-event-inference-20260830`.
2. Record parent SHA, working-tree diff, compiler/tool versions, ROS2/GADEN overlays, `libgaden.so` resolution order, and executable SHA-256.
3. Use authoritative `main_v8` / accepted native physical concentration path only. `dataset_v1` is forbidden.
4. Verify the historical RNG hook remains opt-in and does not change the default simulator when disabled.
5. Verify exact native concentration-query + run-persistent sensor parity on a controlled synthetic case before mass generation.
6. `occupancyWords`, hit-frequency maps, CTT occupancy and any occupancy-to-ppm conversion are forbidden as the physical observation.
7. Do not read H01 true source, localization error, PMFS source rank, planner reward, or closed-loop outcome during bank construction/training/model selection.
8. No new 300-s closed-loop run is permitted in this task.

## 2. Frozen H01 physical design

### 2.1 Source query grid

Use the frozen H01 210 physical source carriers. Carrier IDs/coordinates are query variables, not truth labels.

All 210 carriers remain available in train/validation/test because the deployment map/source query grid is known a priori. Do not create a source-classification holdout requirement.

### 2.2 Wind-context split — inherit CTT-V13 M1 exactly

Use 10 complete generating wind contexts indexed `0..9` with exact wind-file/config hashes.

- TRAIN contexts: `0,3,5,6,8,9`
- VALIDATION contexts: `4,7`
- TEST contexts: `1,2`

A context belongs to exactly one split. Do not split individual cells/samples from one wind context across train/test.

The neural conditional inputs must be computed from the **same wind field that generated the forward simulation**. Trajectory-local estimated wind that was not a parent of the simulator field is forbidden as a substitute.

### 2.3 Transport-key split — inherit CTT-V13 M1

Use 8 keyed stochastic transport realizations per source/context.

- TRAIN keys: `0,1,2,3,4,5`
- HELD-OUT physical keys: `6,7`

Keys 6/7 never enter gradient training.

### 2.4 Query trajectories

Use the existing frozen H01 reserved query schedules:

- train routes: `4001,4002,4003`
- validation route: `4004`
- test route: `4005`

Do **not** re-simulate the plume separately for each route if the native world field is route-independent. Preferred implementation:

1. generate one coherent source × wind-context × transport-key physical plume realization;
2. sample that same realization at each frozen route's actual `(pose,timestamp)` sequence;
3. pass each route's sampled physical concentration through a separate run-persistent native sensor trajectory from its causal start state.

This keeps route sampling separate from physical plume RNG and avoids unnecessary duplicate forward simulations.

## 3. Required bank payload

For every `(wind_context, source_carrier, transport_key, route)` materialize auditable data sufficient to reconstruct the native observation chain.

Minimum payload/manifest fields:

- House and scene/config hash;
- source carrier ID and physical coordinate/support;
- wind context ID + exact generating wind file/config SHA-256;
- transport key and RNG provenance;
- route seed/schedule SHA-256;
- sample timestamps and poses;
- native physical concentration `C_t` in physical units;
- native/run-parity measured concentration `M_t` after persistent sensor dynamics;
- sensor implementation/code hash and parameter/config hash;
- `sensor_state_scope = run_persistent`;
- `context_state_reset = false`;
- per completed physical stop: exactly the first 80 causally consumed native 0.2-s samples corresponding to 8 × 10-sample PMFS blocks;
- first-passage label `F in {0..79, never}` using the native measured threshold;
- binary measured event tape only as an auxiliary derived field, never as replacement for `M_t`.

Incomplete tail samples after the 8 completed blocks must not be treated as a ninth block.

Write a file-level SHA-256 manifest covering every payload and all source/config files.

## 4. Mandatory bank integrity gates

All must PASS before neural training.

### G0-A — source/query coverage

- all 210 carriers present in every required wind context and transport key;
- no duplicate/missing carrier coordinate aliases without explicit quotient mapping.

### G0-B — wind provenance

For every record, prove the conditional wind features supplied to M1 come from the exact wind context used by the forward simulator.

### G0-C — transport independence

- same `(source,wind,key)` rerun is deterministic under frozen seed;
- different held keys produce non-degenerate stochastic variation on supported H01 inputs.

### G0-D — native physical/sensor parity

On a preregistered smoke subset, require native physical query parity and persistent sensor parity to numerical/bitwise tolerance inherited from the accepted PF-DEI parity tests.

### G0-E — PMFS block semantics

For every completed stop:

- exactly 80 retained native samples = 8 × 10 samples;
- samples ordered and not reused;
- no moving samples included;
- recomputed 10-sample block means reproduce native block HIT/NOTHING decisions where archived reference exists.

Any G0 failure => `STOP_CTT_H01_M1_BANK_INVALID`.

## 5. Neural M1 training — frozen architecture role

Implement/refactor a clean bank-driven version of the already frozen factorized model in:

`experiments/cg_pc_ctt/ctt_causal_first_passage_20260830/train_eval_h01_factorized_neural_first_passage.py`

You may change **I/O plumbing and context encoder input dimensions only as required by the new bank**. You may not change the scientific output factorization or training objective.

Required conditional input categories:

- candidate source geometry;
- current query/robot geometry;
- map/obstacle geometry features already available at deployment;
- exact generating wind-context features derived causally from the simulator wind field;
- causal route/time context up to the scored stop.

Forbidden inputs:

- carrier class embedding/one-hot ID as a shortcut;
- true source identity as an input feature;
- PMFS posterior/rank;
- localization error;
- future route/gas/wind;
- route semantic ID;
- wind context semantic ID/name;
- hidden simulator frame/phase ID unavailable at deployment;
- planner action outcome or closed-loop reward.

Checkpoint selection uses validation **proper factorized physical loss only**.

## 6. Capacity-matched physical comparator

Train a capacity-matched `STATIC-WIND` arm using the identical architecture and data except that dynamic generating-wind features are replaced by the TRAIN-context mean. No extra parameters, temperature or calibration are allowed.

This tests whether wind conditioning is physically load-bearing.

## 7. Direct held-out physical M1 gate

Evaluate only after checkpoints are frozen.

Primary TEST set:

- complete TEST wind contexts `1,2`;
- route `4005`;
- held transport keys `6,7`;
- all 210 physical source query carriers.

Report categorical first-passage NLL and integrated arrival-by-time Brier score, clustered by source × wind context.

M1 physical GO requires all:

1. `STATIC-WIND - CONDITIONAL` NLL paired cluster-bootstrap lower 95% CI > 0;
2. `STATIC-WIND - CONDITIONAL` Brier lower 95% CI > 0;
3. CONDITIONAL improves both NLL and Brier separately in TEST context 1 and TEST context 2;
4. shuffling the actual generating-wind context among matched test examples worsens NLL with lower 95% CI > 0;
5. probability normalization max error < `1e-6`;
6. repeated identical inputs/keys give identical output within frozen numerical tolerance;
7. no obstacle/invalid query receives legal physical support if the inherited M1 mask contract forbids it.

Failure => `CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO` and STOP. Do not alter the network/loss/gate after seeing test results.

## 8. Source-evidence mechanism gate

Only if Section 7 PASSES.

Use the frozen neural checkpoint to score synthetic source interventions on the held test data. Source truth here is simulator-selected evaluation truth only and is opened after the model is frozen.

For each test wind context × held transport key × source intervention, compare:

- `FULL`: factorized neural first-passage likelihood;
- `SURVIVAL_ONLY`: remove conditional phase, retain only ever/never;
- `TIME_PERMUTE`: permute the 80 native samples within each stop before extracting first passage; preserve the same multiset/hit count;
- `PHASE_LABEL_SHUFFLE`: preserve candidate survival probability but permute candidate phase distributions across source coordinates;
- `STATIC_WIND_FULL`: full scorer from the capacity-matched static-wind model.

Required reports: normalized true-source rank, median rank, Top-5, Top-10, paired win/loss/tie counts, exact/sign-test p-values, and results separately for test wind contexts 1 and 2.

Source-evidence GO requires all:

1. FULL mean normalized rank < SURVIVAL_ONLY and one-sided paired sign-test `p <= 0.01`;
2. FULL Top-10 is not lower than SURVIVAL_ONLY;
3. FULL mean normalized rank < TIME_PERMUTE with `p <= 0.01`;
4. FULL mean normalized rank < PHASE_LABEL_SHUFFLE with `p <= 0.01`;
5. FULL mean normalized rank < STATIC_WIND_FULL with `p <= 0.01`;
6. the direction of FULL vs SURVIVAL and FULL vs TIME_PERMUTE is non-negative in each of test wind contexts 1 and 2;
7. no result-dependent threshold, blend, posterior projection, Top-K router or fallback is introduced.

Failure => `CTT_H01_WIND_CONDITIONED_FIRST_PASSAGE_SOURCE_EVIDENCE_NO_GO` and STOP.

## 9. Runtime qualification — only after Sections 7 and 8 PASS

No closed-loop run yet. First implement runtime inference and prove:

1. Python reference ↔ deployment implementation first-passage probability parity;
2. source-likelihood/posterior update parity on frozen offline cases;
3. native block is consumed exactly once: CTT and native PMFS may not both assimilate the same observation;
4. no future data leakage;
5. persistent sensor semantics unchanged;
6. inference latency within the frozen source-update budget;
7. OFF/ABSTAIN path, if an OFF reference path exists, reproduces native PMFS exactly and is not a learned reliability gate.

Only after this section PASS may the terminal report set:

`CTT_H01_CLOSED_LOOP_DEVELOPMENT_AUTHORIZED = YES`.

Otherwise it remains `NO`.

## 10. Explicitly forbidden rescue operations

Do not perform any of the following after seeing a failed gate:

- change loss weights;
- add class weights based on test outcomes;
- add temperature/blend/alpha;
- add learned reliability or acceptance gate;
- add Top-K rescue;
- posterior/rank projection;
- tune first-passage threshold;
- change context split/member split;
- selectively remove hard sources/contexts;
- use localization error for model selection;
- launch a closed loop to see whether a failed offline model "works anyway".

A failed gate requires a scientific terminal NO-GO, not another H01 post-hoc method version.

## 11. Required return package

Create one immutable evidence root containing at minimum:

- `00_EXECUTIVE_VERDICT.md`
- `01_PROVENANCE_AND_INPUT_HASHES.md`
- `02_BANK_CONTRACT.json`
- `02_BANK_FILE_SHA256.tsv`
- `03_BANK_COVERAGE.csv`
- `04_NATIVE_SENSOR_PARITY.csv`
- `05_FIRST_PASSAGE_LABEL_AUDIT.csv`
- `06_TRAINING_CONTRACT.json`
- training histories + frozen checkpoint hashes
- `07_M1_PHYSICAL_GATE.json/md`
- `08_SOURCE_EVIDENCE_CASES.csv`
- `08_SOURCE_EVIDENCE_GATE.json/md`
- destructive-control case files
- `09_RUNTIME_PARITY.md` only if offline gates pass
- `10_CLOSED_LOOP_AUTHORIZATION.md`
- exact source diff/patch
- source SHA-256 manifest
- build commands
- run commands
- wall-time / bank-generation cost report

Unique terminal status must be exactly one of:

- `STOP_CTT_H01_M1_BANK_INVALID`
- `CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO`
- `CTT_H01_WIND_CONDITIONED_FIRST_PASSAGE_SOURCE_EVIDENCE_NO_GO`
- `CTT_H01_RUNTIME_QUALIFICATION_NO_GO`
- `CTT_H01_CLOSED_LOOP_DEVELOPMENT_AUTHORIZED`

Do not start a 300-s closed-loop experiment inside this contract.
