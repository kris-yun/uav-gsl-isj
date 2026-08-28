# CODEX FINAL TASK — PF-DEI-SR autonomous experiment closure

Date: 2026-08-28
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative method:

`docs/PF_DEI_FINAL_METHOD_FREEZE_20260828.md`

This file is the only current execution authority. Do not stop after an intermediate successful stage to request another method design. Continue automatically until one of the terminal verdicts defined below is reached. Engineering retries that preserve the frozen scientific inputs are allowed and must be logged.

## 0. Preserve all prior evidence

Do not reset/overwrite:

- `a504e0e` native forward closure;
- `6fbf08c` sensor-memory audit;
- `33f9a80` exact deconvolution replay;
- `55dd893` run-level bank blocker evidence;
- all GitHub PF-DEI derivation/history.

The historical `/dev/shm` overlay loss remains a reproducibility limitation for old runs. Every new simulation/runtime launched now must freeze deployed source/config/library/overlay hashes.

Run all current PF-DEI reference selftests first. Fix only engineering defects if a frozen selftest regressed; do not alter scientific formulas.

## 1. Resolve the final source/nuisance contracts before any new historical source ranking

### 1.1 Source-support identity

Recover the exact source carriers underlying `geometry_prior` for every run/prefix and prove:

`stable source id <-> native GADEN xyz <-> geometry_prior mass`.

Run-specific support is allowed. Cross-run integer source indices need not match.

Do not union the 1,229 adaptive IDs blindly.

Hard stop if unresolved:

`STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

### 1.2 Source-strength contract

Audit the authoritative preserved simulator/run source configuration while programmatically discarding source-location fields and all performance/truth labels.

Follow exactly Section 4 of `PF_DEI_FINAL_METHOD_FREEZE_20260828.md`:

- if source emission strength is known/fixed, freeze it;
- otherwise create the provenance-defined global nuisance `Q`;
- prove linear scaling before using analytical scaling;
- otherwise explicitly simulate Q levels.

Hard stop if neither fixed-known nor defensible nuisance support exists:

`PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`.

### 1.3 Final transport family

There is only one final family; no post-result expansion.

Use explicit auditable preserved native member seeds if available. Otherwise use training seeds:

`101,211,307,401,503,601,701,809,907,1009,1103,1201`

and reserved synthetic qualification seeds:

`1301,1409,1511,1601`.

All non-stochastic physical House parameters remain exactly source-proven. Do not widen parameter ranges after seeing historical source evidence.

Write and hash:

- `source_support_manifest.csv`;
- `source_strength_manifest.csv`;
- `transport_manifest.csv`;
- environment/config/library/overlay manifest.

## 2. Build the reusable native physical field bank

The required expensive object is not merely a historical trace bank. Materialize reusable native GADEN fields or an equivalent immutable queryable representation for every required unique:

`(House, source physical coordinate, Q member if explicit, transport member)`.

A field may be reused across trajectories only when House environment/time-origin/config provenance proves reuse is valid.

Use the already parity-audited native physical concentration query. Never use occupancy-derived ppm or historical `true_gas_ppm`.

### 2.1 Smoke

Before scaling, use:

- 1 House;
- 2 distinct source coordinates;
- >=2 training transport members;
- 1 historical trajectory skeleton;
- 1 source-independent random feasible trajectory skeleton.

Require:

- physical ppm finite/non-negative within source-proven serialization tolerance;
- 50 pre-frozen stored-vs-fresh native query parity points;
- clean-process reproducibility;
- exact source/support ordering;
- exact time/pose query semantics;
- native sensor forward parity on a deterministic subset.

If smoke fails, repair only engineering/provenance defects with frozen scientific inputs. If the native field cannot be generated reproducibly for arbitrary candidate coordinates, stop:

`PF_DEI_PHYSICAL_BANK_ENGINEERING_NO_GO`.

### 2.2 Full field bank

After smoke PASS, automatically generate all required training and reserved-qualification fields. Parallel job key:

`(House, source_id, Q_id, transport_id)`.

Deduplicate only by exact physical/config identity.

Hash every output. Do not silently omit failed jobs; engineering retries must reuse identical frozen inputs.

## 3. Create the source-independent trajectory library and simulation dataset

For each House:

- historical geometry-only OFF trajectory skeletons: 10;
- source-independent random feasible training skeletons: seeds `3001..3020`;
- reserved source-independent qualification skeletons: seeds `4001..4005`.

Random feasible skeleton generation must use native map/navigation constraints but no gas/source information.

For every training example:

1. choose trajectory skeleton independently of source;
2. choose source from the support prior;
3. choose Q nuisance/member according to the frozen contract;
4. choose one of the 12 training transport members;
5. query native physical concentration along the complete trajectory;
6. propagate one coherent run-persistent native sensor state from run start;
7. emit measured ppm at exact cadence plus stop/block markers;
8. sample one or more causal prefix endpoints.

No historical measured ppm is used for training.

Negative source examples must reuse the same exact generated observation and trajectory and replace only candidate source by an independent source draw from the same support prior.

## 4. Train exactly the frozen PF-DEI-SR NRE

Implement the architecture/training protocol exactly from `PF_DEI_FINAL_METHOD_FREEZE_20260828.md`:

- causal TCN;
- fixed 9-layer dilation schedule;
- fixed input features;
- balanced BCE;
- fixed optimizer/hyperparameters;
- model seeds `1701,1702,1703`;
- identical architecture/recipe for H01/H02/H03;
- environment-specific weights are allowed;
- no architecture search, no temperature fitting, no historical-performance tuning.

Save exact training/validation split manifests, weights and hashes.

## 5. Synthetic qualification — first hard scientific gate

Use only reserved transport seeds `1301,1409,1511,1601`, reserved trajectory skeletons `4001..4005`, and deterministic experimenter-selected synthetic source candidates independent of historical true source.

Minimum 128 cases per House.

Require every criterion from Section 11 of the final method freeze:

- top-5 source recall >=0.75;
- median normalized true-source rank <=0.10;
- positive mean log posterior/prior gain at the true source;
- source-index permutation invariance;
- zero forbidden-field leakage;
- each of the three training-seed models individually beats prior baseline on mean source rank.

If any House fails, terminal verdict:

`PF_DEI_INFERENCE_ENGINE_NO_GO`.

Do not alter nuisance family/model and rerun.

If PASS, automatically continue.

## 6. Historical truth-blind predictive qualification — second hard scientific gate

Freeze model weights before reading historical measured ppm for qualification.

Apply the frozen models to the 30 historical OFF measured sequences. Never read true source, localization error, ON/OFF improvement or `true_gas_ppm` in this stage.

At each of four chronological prefix/future splits:

1. compute current PF-DEI posterior `q_t(s)` from the full measured prefix;
2. use the frozen native simulation bank on that exact historical trajectory to build the `q_t`-weighted predictive mixture for the disjoint future segment;
3. compare its multivariate energy score to the source-independent geometry-prior predictive mixture.

Run PASS:

- mean future predictive gain >0;
- posterior predictive beats prior predictive in >=3/4 future segments.

Global PASS:

- >=20/30 runs;
- H01 >=5/10;
- H02 >=5/10;
- H03 >=5/10.

If not, terminal verdict:

`PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`.

Do not expand transport or retune.

If PASS, automatically freeze all scientific artifacts and continue.

## 7. Open development truth once; no science changes thereafter

Only now may the 30 development-run source truth/localization metrics be loaded.

Compare frozen PF-DEI-SR source posterior and native PMFS source estimate on exactly the same historical OFF observations. This is an offline sanity check, not the final performance claim.

Hard safety stop only if either occurs:

- pooled expected-location error is >5% worse than native PMFS on the same historical observations; or
- the already-defined project false-confident-collapse metric shows any new collapse.

If either occurs:

`PF_DEI_OFFLINE_SAFETY_NO_GO`.

Otherwise do not tune anything; continue directly to runtime integration.

## 8. Runtime integration — source posterior replacement only

Create a new isolated mode, e.g. `pfdei_sr`, without modifying Classic OFF or frozen historical modes.

At every native PMFS source-update point:

1. collect the complete causal measured-ppm prefix with pose/time/wind/markers;
2. evaluate the frozen House model for every candidate in the current stable source support;
3. compute `q_pfdei(s) = normalize(q0(s) * exp(mean_3_models(logit_s)))` using stable log-sum-exp;
4. inject `q_pfdei` only into the native source-evidence/posterior channel used for destination evaluation;
5. keep native PMFS navigation-cost-aware planner, feasible-target logic, motion controller, sensing schedule and stopping semantics unchanged.

Forbidden:

- multiplying PF-DEI posterior by native observation posterior;
- minimum-KL blend with native posterior;
- temperature/blend/reset;
- Active Probe;
- House/seed threshold;
- using future samples.

Fallback to native is permitted only for a logged engineering contract violation (model/input/support unavailable), never because localization looks bad.

Require Python/C++ or Python/runtime numerical parity for fixed synthetic prefixes and source permutations before real smoke.

## 9. Six closed-loop infrastructure smoke runs

Run H01/H02/H03 with seeds `314159` and `271828`.

Smoke is for infrastructure/parity, not scientific retuning. Check:

- no crash/deadlock;
- model hash/support identity;
- strict run-prefix causality;
- native sensor acquisition unchanged;
- native planner cost/navigation semantics unchanged;
- posterior normalization/permutation parity;
- no fallback except documented engineering fault;
- no false-confident collapse.

Engineering defects may be fixed without changing model/science, then smoke repeated.

If the frozen method cannot be executed causally/stably even after engineering repair:

`PF_DEI_RUNTIME_NO_GO`.

Otherwise continue automatically.

## 10. Final 60-arm development closed loop

Run exactly:

`H01,H02,H03 x seeds0..9 x OFF/ON = 60 arms`

Contract:

- OFF = unmodified Classic PMFS;
- ON = frozen `pfdei_sr`;
- paired deterministic setup;
- 300 s;
- no scientific/model changes during matrix.

Development GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all runtime/parity contracts pass.

If any fail:

`PF_DEI_MAIN_INNOVATION_NO_GO`.

No seed0..9 retuning.

If all pass:

`PF_DEI_MAIN_INNOVATION_DEVELOPMENT_GO`

and continue automatically.

## 11. Confirmatory closed loop

Freeze absolutely everything and run fresh seeds10..19 with the same H01/H02/H03 OFF/ON 300-s contract.

Apply the same scientific effect criteria as the development matrix. No retuning.

Final success:

`PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.

Otherwise:

`PF_DEI_CONFIRMATORY_NO_GO`.

## 12. Terminal behavior

Do not return intermediate 'should I continue?' messages. Continue until exactly one terminal state:

- `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`
- `PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`
- `PF_DEI_PHYSICAL_BANK_ENGINEERING_NO_GO`
- `PF_DEI_INFERENCE_ENGINE_NO_GO`
- `PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`
- `PF_DEI_OFFLINE_SAFETY_NO_GO`
- `PF_DEI_RUNTIME_NO_GO`
- `PF_DEI_MAIN_INNOVATION_NO_GO`
- `PF_DEI_CONFIRMATORY_NO_GO`
- `PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`

At the terminal state write one consolidated report with exact hashes, frozen manifests, bank counts, training/qualification results, truth-blind historical predictive results, runtime parity, development/confirmatory performance if reached, and one mechanistic conclusion.

The scientific method must not change after this task begins. Only engineering fixes that preserve the frozen contracts are permitted.