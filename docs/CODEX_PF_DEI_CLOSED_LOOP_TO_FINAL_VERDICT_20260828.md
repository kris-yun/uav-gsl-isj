# CODEX MASTER TASK — PF-DEI closed loop to final scientific verdict

Date: 2026-08-28
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

## Purpose

This is the single authorized execution plan from the present state to a final GO/NO-GO scientific verdict. Do not stop after intermediate diagnostics merely to ask for another design review. Continue automatically through the pre-frozen branches below unless a hard scientific/engineering STOP condition is reached.

This task supersedes all earlier PF-DEI execution pointers and stage-specific task files as the current execution authority. Earlier reports remain preserved evidence.

## Preserved evidence — do not overwrite

Keep intact:

- `a504e0e` — native physical forward/operator closure;
- `6fbf08c` — sensor-memory mechanism audit;
- `33f9a80` — exact sensor deconvolution/counterfactual;
- `55dd893` — run-level source-evidence blocker record;
- GitHub scientific history through the current branch.

Frozen scientific facts:

1. V5 passive cumulative evidence: 0/30 ACCEPT.
2. V6-A continuous source diagnostic: 0/30 predictive pass; H01/H02/H03 transfer-only = 1/10, 0/10, 2/10; absolute adequacy = 0/30.
3. Occupancy is not physical concentration and may never be mapped empirically to ppm.
4. Native observation chain is closed: `source -> transport -> physical concentration -> persistent sensor state -> measured ppm -> exact 10-sample PMFS block decision`.
5. Historical deconvolution is valid for the frozen zero-noise symmetric sensor: 30/30 runs, 4049/4049 blocks; native-vs-ideal decision flips = 159/4049.
6. Sensor memory is a real deterministic observation-aliasing mechanism but is not by itself proven to explain source-ranking failure.
7. A1/A2 exact canonicalization parity is already demonstrated on synthetic data.
8. The current missing object is a complete physical candidate-source forward ensemble, not the single-source physical forward operator.

## Global prohibitions

Until explicitly opened by the later stages below, do not use:

- H01/H02/H03 true source;
- localization error;
- ON/OFF improvement;
- any result-dependent House/seed threshold;
- occupancy-to-ppm conversion;
- Active Probe;
- manual posterior temperature/blend/reset;
- ad hoc features chosen after seeing outcomes.

Never retune an earlier frozen stage from a later-stage result.

---

# PHASE I — Materialize the native physical candidate forward bank

Follow the contracts in:

- `docs/PF_DEI_PHYSICAL_BANK_MATERIALIZATION_CONTRACT_20260828.md`
- `experiments/cg_pc_ctt/pf_dei_physical_bank_contract.py`
- `experiments/cg_pc_ctt/pf_dei_runlevel_energy_reference.py`

### I.1 Prove source-support identity

Before expensive simulation, build a stable source-support manifest for every run. Prove:

`source_index <-> stable physical source coordinate <-> geometry_prior mass`

for every chronological prefix.

Do not union the 1,229 adaptive IDs blindly. If source supports differ legitimately by run, preserve run-specific supports; deduplicate expensive fields only by exact `(House,x,y,z)`.

Hard stop:

`STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`

### I.2 Freeze transport members

Use a source-independent native GADEN transport/RNG ensemble with reproducible source/config/RNG provenance.

If a previously frozen native member mapping exists and is explicit, reuse it. Occupancy-member labels alone are not sufficient provenance.

If no explicit native mapping exists, define one fixed native ensemble before any source-evidence result is computed. No outcome-driven ranges or member count changes.

### I.3 Determine field reuse scope

Prove the narrowest valid reuse scope from source/config hashes.

Preferred when valid:

`FIELD_REUSE_SCOPE = HOUSE_SOURCE_MEMBER`

meaning one GADEN field per `(House, source, member)` can be queried along all 10 trajectories in that House.

### I.4 Smoke then full materialization

Smoke: one House, one trajectory, two distinct sources, >=2 members. Require:

- valid `[S,M,T]` physical ppm payload;
- 50 deterministic stored-vs-fresh native query parity checks;
- clean-process repeat/reproducibility check;
- no occupancy-derived values;
- source/prior ordering parity.

If smoke passes, immediately generate the complete valid bank for all 30 runs. Hash every source/config/field/bank artifact.

Status naming:

- preserved single-source operator: `PF_DEI_FORWARD_OPERATOR_CLOSED = YES`;
- bank: `PF_DEI_PHYSICAL_BANK_MATERIALIZED = YES/NO`.

If bank cannot be built for a source-proven engineering reason, stop only with a precise bank-materialization reason. Do not mislabel the already-closed native operator as unresolved.

---

# PHASE II — Physical run-level source adequacy, no neural model yet

As soon as the bank validates, run the existing chronological full-sequence energy-score diagnostic on the 30 deconvolved physical observations.

Use the same source support, transport members, trajectory and timestamps. Treat the complete time sequence as a correlated object; do not multiply per-sample likelihoods or independent contexts.

Also verify historical A1/A2 canonical score/ranking parity with the exact native sensor/inverse.

Frozen adequacy rule:

`PHYSICAL_RUNLEVEL_SOURCE_FORWARD_ACTIONABLE`

only if:

- total predictive pass >=20/30;
- H01 >=5/10;
- H02 >=5/10;
- H03 >=5/10;
- A1/A2 canonical parity passes.

If this passes -> go directly to PHASE IV.

If it fails -> do not return for design review; go directly to PHASE III.

---

# PHASE III — One automatic physics-randomized transport expansion, then stop or continue

This is the only authorized transport-family expansion. It is not an iterative tuning loop.

### III.1 Freeze broader nuisance before outcome

Construct a broader source-independent GADEN nuisance/transport design from authoritative simulator/config provenance only. Vary only physically meaningful transport variables whose admissible ranges can be justified from source/config/environment provenance. Examples may include wind realization/substream, plume stochastic RNG/substream, release/dispersion parameters already supported by GADEN, or other source-independent native transport parameters whose ranges are physically documented.

Do not choose ranges from localization outcomes, House-specific source truth, or energy-score results. Record the complete design before running historical adequacy.

Use a deterministic space-filling/factorial sampling rule and freeze its member IDs/hashes. Do not perform Bayesian optimization or adaptive member selection from H01/H02/H03 outcomes.

### III.2 Materialize expanded physical ensemble

Reuse the same stable source supports and exact historical trajectories. Generate physical ppm through the native concentration path, then validate hashes/parity exactly as in PHASE I.

### III.3 Re-run the same frozen run-level adequacy test

No score/threshold/transform changes.

If the same >=20/30 total and >=5/10 each House rule now passes:

`PHYSICS_RANDOMIZED_SOURCE_FORWARD_ACTIONABLE`

and continue to PHASE IV.

If it still fails:

`PF_DEI_GENERATIVE_FAMILY_NO_GO`

Stop the method-development loop. Do not add more hand features, Gate changes, transport rounds, Active Probe, or House-specific fixes. Produce the final failure report explaining that the current physics-factorized source/transport family remains insufficient after the one pre-frozen broader nuisance expansion.

---

# PHASE IV — Build the actual PF-DEI inference engine only after physical adequacy

The inference target is run-prefix source inference with global source and source-independent nuisance marginalized by the simulator.

Preferred implementation: candidate-conditioned neural ratio estimation (NRE), because the full sequence is correlated and the simulator is available.

Target ratio:

`r(D,S,kappa) = p(D | S,kappa) / p(D | kappa)`

where `D` is the chronological measured-ppm/run-prefix sequence with timestamps, poses, wind/context markers and PMFS block markers; `kappa` contains observable context only.

Training positives: simulator-generated `(D,S)`.
Training negatives: same-context candidate mismatch `(D,S_minus)` with source sampled independently from the same source prior/support. Never make House identity or trajectory identity a shortcut.

The native persistent sensor state must be propagated across the complete synthetic run; no stop/context reset.

A1/A2 sensor canonicalization remains a required implementation check, not a tunable feature.

### IV.1 Synthetic qualification

Use only experimenter-chosen synthetic sources and held-out simulator nuisance/source draws. Freeze architecture and training protocol before historical evaluation.

Minimum qualification requirements:

- held-out synthetic source ranking materially better than the source-prior/null baseline;
- posterior/ranking invariance to source-index permutation;
- no House/seed-specific threshold;
- native measured-sequence and canonicalized physical-sequence source rankings consistent within the already-established sensor/inverse tolerance where the inverse assumptions hold;
- repeated training seeds do not reverse the qualitative qualification verdict.

If the simulator is identifiable but the inference engine cannot pass these checks, stop:

`PF_DEI_INFERENCE_ENGINE_NO_GO`

Do not blame the sensor/transport family and do not open localization performance.

### IV.2 Truth-blind historical qualification

Run the trained/frozen inference on the 30 historical OFF trajectories without reading true source/error.

Use chronological prefix-to-future predictive adequacy and source-independent model criticism. Keep the same adequacy rule used to authorize the physical family unless the statistic is mathematically incommensurate; in that case freeze an equivalent null-vs-model predictive criterion before reading historical outcomes.

If historical predictive adequacy is not recovered, stop:

`PF_DEI_INFERENCE_HISTORICAL_NO_GO`

No performance opening.

If adequate, freeze the trained model, hashes and all inference parameters, then continue.

---

# PHASE V — Frozen offline performance opening

Only now may source truth/localization error be opened for the already-frozen 30 OFF trajectories.

Compare the frozen PF-DEI posterior/source estimate against the corresponding native PMFS state on exactly the same historical observations. This stage is diagnostic of source inference quality only; no planner interaction yet.

Do not tune the model from these errors.

If the frozen PF-DEI source estimate is grossly worse or creates false-confident collapses, stop:

`PF_DEI_OFFLINE_PERFORMANCE_NO_GO`

Otherwise continue directly to runtime integration.

---

# PHASE VI — Runtime integration, no Active Probe

Implement a new isolated runtime mode. Do not mutate Classic OFF behavior or old frozen modes.

Runtime semantics:

1. ingest the complete causally available run prefix;
2. update PF-DEI source evidence/posterior using the frozen inference engine;
3. assimilate into PMFS only by the already frozen minimum-change rule (minimum-KL / I-projection or exact native return when the source-evidence adequacy guard is not met);
4. no posterior reset, temperature, ad hoc blend, House threshold or Active Probe;
5. planner remains native PMFS, including its navigation-cost trade-off.

Require Python/runtime parity on synthetic fixtures and deterministic replayable prefixes.

---

# PHASE VII — Closed-loop smoke and 60-arm development matrix

### VII.1 Six fixed smoke runs

Use nondevelopment seeds:

- 314159
- 271828

for H01/H02/H03.

Audit:

- process/runtime stability;
- model/source-support identity;
- bank/inference hash identity;
- run-prefix causality (no future samples);
- persistent sensor-state handling;
- posterior assimilation parity;
- no false-confident collapse;
- native planner semantics preserved.

If infrastructure/parity fails, fix only engineering defects without changing frozen science. Repeat smoke.

If the scientifically frozen inference is valid but runtime behavior is intrinsically non-actionable, stop and report precisely; do not retune science from smoke localization error.

### VII.2 60-arm development evaluation

Run exactly:

H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms

- OFF = Classic PMFS;
- ON = frozen PF-DEI runtime;
- paired deterministic setup;
- 300 s;
- no scientific edits during the matrix.

Final development GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all runtime/parity contracts pass.

If any fail:

`PF_DEI_MAIN_INNOVATION_NO_GO`

Stop. Do not retune seeds 0..9.

If all pass:

`PF_DEI_MAIN_INNOVATION_DEVELOPMENT_GO`

continue automatically to confirmatory evaluation.

### VII.3 Confirmatory seeds

Freeze everything from the development GO and run fresh seeds 10..19 for H01/H02/H03 with the same OFF/ON contract.

Report confirmatory pooled/House results and whether the effect replicates. No retuning.

Final successful state:

`PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`

Otherwise:

`PF_DEI_CONFIRMATORY_NO_GO`.

---

# Required final output

Do not send intermediate "should I continue?" messages. Continue automatically until one of the hard terminal states below is reached:

- `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`
- precise physical-bank engineering STOP
- `PF_DEI_GENERATIVE_FAMILY_NO_GO`
- `PF_DEI_INFERENCE_ENGINE_NO_GO`
- `PF_DEI_INFERENCE_HISTORICAL_NO_GO`
- `PF_DEI_OFFLINE_PERFORMANCE_NO_GO`
- `PF_DEI_MAIN_INNOVATION_NO_GO`
- `PF_DEI_CONFIRMATORY_NO_GO`
- `PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`

At the terminal state, return one consolidated report containing:

1. exact commits/hashes and environment provenance;
2. all intermediate frozen verdicts;
3. physical-bank completeness/reuse statistics;
4. base and expanded transport adequacy if applicable;
5. inference qualification if applicable;
6. runtime smoke if applicable;
7. 60-arm and confirmatory results if reached;
8. the single final terminal verdict;
9. a concise statement of the scientifically supported failure mechanism or success mechanism.

The purpose of this document is to finish the PF-DEI decision tree in one execution campaign, not to create another sequence of micro-audits.