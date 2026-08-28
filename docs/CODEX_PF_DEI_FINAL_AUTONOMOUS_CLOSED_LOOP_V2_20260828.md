# CODEX FINAL TASK V2 — PF-DEI-SR 2.5-D autonomous experiment closure

Date: 2026-08-28
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative science contract:

`docs/PF_DEI_FINAL_METHOD_FREEZE_V2_20260828.md`

This V2 task supersedes all earlier PF-DEI execution documents, including `CODEX_PF_DEI_FINAL_AUTONOMOUS_CLOSED_LOOP_20260828.md` and the earlier broad master task.

Do not stop after an intermediate successful stage to request another method design. Continue automatically until one terminal verdict below is reached. Engineering retries are allowed only when they preserve every frozen scientific input and must be logged.

## 0. Preserve prior evidence and merge history

Preserve/reach without reset or overwrite:

- `a504e0e` — native physical forward/operator closure;
- `6fbf08c` — sensor-memory audit;
- `33f9a80` — exact deconvolution/counterfactual;
- `55dd893` — missing physical-bank blocker;
- `2fc133f` — V1 terminal source-support report;
- current GitHub V2 method history.

Record deployed GADEN/ROS source, config, library and overlay SHA-256 for every new simulation/runtime. Historical `/dev/shm` overlay loss remains an archival limitation only.

Run all current PF-DEI reference selftests. Fix only engineering regressions; do not alter frozen scientific formulas.

## 1. Close the revised planar source-support contract

The target is planar `S_xy`, not 3-D xyz.

### 1.1 Recover planar support

For every historical run/prefix prove:

`stable carrier id <-> native planar x,y <-> geometry_prior mass`.

Use the persistent carrier manifests and the exact geometry-prior provenance. Run-specific supports are allowed. Do not union the 1,229 adaptive proposal IDs blindly.

Write/hash:

`artifacts/pf_dei_v2/source_support_xy_manifest.csv`.

Hard stop only if this planar identity fails:

`STOP_PF_DEI_PLANAR_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

### 1.2 Build source-independent legal height support

Never read/copy historical source z.

First search source-independent scenario/generator metadata for a benchmark-wide or House-level source-placement rule/catalogue that describes all admissible source heights independently of which historical source was selected.

If found, freeze that rule.

Otherwise use the geometry-only fallback from the V2 method freeze:

- parse the authoritative native 3-D occupancy/source-placement geometry;
- map each carrier x,y into the exact GADEN frame;
- enumerate all native-legal free vertical source coordinates at that x,y;
- apply only source-proven source-radius/clearance constraints;
- derive no height from gas observations, historical source fields or localization results.

Write/hash:

`artifacts/pf_dei_v2/source_height_support_manifest.csv`.

For each nonzero-prior carrier require at least one legal height. If any fail:

`PF_DEI_2D3D_GEOMETRY_SUPPORT_NO_GO`.

If no authoritative placement measure exists, use the discrete uniform distribution over the legal heights exactly as frozen in V2.

### 1.3 Resolve source strength Q

Audit source-independent native configuration only.

- if Q is fixed-known, freeze it;
- otherwise freeze a provenance-defined global Q support;
- prove analytical scaling before using it; otherwise simulate Q explicitly.

If neither route is valid:

`PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`.

## 2. Freeze the one final joint nuisance family

Do this before any new historical source-ranking result.

Training transport seeds:

`101,211,307,401,503,601,701,809`.

For each carrier map height strata:

`u_H=(1,3,5,7,9,11,13,15)/16`

through the carrier's legal height inverse CDF.

If Q is uncertain, map Q strata by the fixed permutation:

`[4,0,6,2,5,1,7,3]`.

Reserved qualification/predictive transport seeds:

`907,1009,1103,1201`

with height quantiles:

`0.125,0.375,0.625,0.875`

and reversed Q quantiles when Q is uncertain.

Write/hash one immutable nuisance manifest. No member/range/count may be changed from later outcomes.

## 3. Materialize native physical training and reserved banks

For every required `(House, source_id, nuisance_member)` generate the actual native GADEN field using concrete source xyz `(x_s,y_s,h_member)`, Q and transport member.

Use the already parity-audited native physical concentration path. Never use occupancy-derived ppm or historical `true_gas_ppm`.

Field reuse across trajectories is allowed only with proven House environment/time-origin/config identity.

### 3.1 Smoke

Before full scaling use:

- one House;
- two distinct planar carriers;
- at least two nuisance members;
- one historical geometry/time skeleton;
- one source-independent random feasible skeleton.

Require:

- native legal source placement;
- finite non-negative physical ppm;
- >=50 deterministic stored-vs-fresh native concentration parity queries;
- clean-process reproducibility;
- exact pose/time semantics;
- native persistent-sensor forward parity on a deterministic subset.

Engineering repairs may fix paths/config plumbing only. If arbitrary legal planar+height source fields cannot be generated reproducibly:

`PF_DEI_PHYSICAL_BANK_ENGINEERING_NO_GO`.

### 3.2 Full banks

Generate and hash:

- training physical fields for all planar carriers x 8 training nuisance members;
- reserved physical fields for all planar carriers x 4 reserved nuisance members.

Deduplicate only by exact physical/config identity. No missing source-member cells are allowed.

Query each reusable field along every compatible training/qualification/historical trajectory skeleton before discarding it.

## 4. Build the source-independent simulation dataset

For each House use:

- 10 historical OFF pose/time skeletons with all gas/truth/outcome fields removed;
- 20 source/gas-independent feasible training skeletons, seeds `3001..3020`;
- 5 source/gas-independent reserved qualification skeletons, seeds `4001..4005`.

For every simulated training sequence:

1. choose trajectory skeleton independently of source;
2. choose planar source from the geometry prior/support independently of trajectory;
3. choose one frozen joint nuisance member `(H,Q,Z)`;
4. query native physical concentration along the entire trajectory;
5. propagate one coherent native sensor state from run start;
6. output measured ppm/time/pose/wind/stop/block markers;
7. create causal prefixes only.

No historical measured ppm is training data.

Negative ratio examples reuse the exact same D and trajectory but replace only the candidate planar source with an independent draw from the same planar support prior.

## 5. Train exactly the frozen PF-DEI-SR causal TCN

Use the architecture and optimization recipe from V2/V1 freeze exactly:

- per-sample input: log1p measured ppm/threshold, candidate-relative planar dx/dy, robot z as observed covariate, observed wind, dt, stop/block markers;
- linear ->64 ->GELU sample encoder;
- 9 causal residual Conv1D blocks, width64, kernel5, dilations 1,2,4,8,16,32,64,128,256;
- LayerNorm+GELU;
- masked global mean + final hidden state;
- MLP 128->64->1;
- balanced BCE;
- AdamW lr 3e-4, weight decay 1e-4;
- batch64, max100 epochs, patience10, gradient clip1.0;
- model seeds 1701,1702,1703;
- final ratio logit = arithmetic mean of the three model logits.

Identical architecture/hyperparameters/qualification thresholds across H01/H02/H03. Environment-specific weights are allowed. No architecture search or temperature calibration.

## 6. Reserved synthetic qualification — hard gate 1

Use only held-out planar carriers selected by deterministic stable-ID hashing, reserved nuisance members and reserved trajectory skeletons. Historical true source is forbidden.

Minimum 128 synthetic cases per House.

Require every House:

- true synthetic planar source top-5 recall >=0.75;
- median normalized true-source rank <=0.10;
- mean log posterior/prior gain at true source >0;
- source-index permutation invariance within numerical tolerance;
- zero forbidden-field leakage;
- each of the three model seeds independently beats the geometry-prior baseline on mean true-source rank.

If any House fails:

`PF_DEI_INFERENCE_ENGINE_NO_GO`.

Do not redesign or retrain with changed science.

If PASS, automatically continue.

## 7. Historical truth-blind future-predictive qualification — hard gate 2

Freeze all weights/hashes before loading historical measured ppm for this stage.

For each of the 30 OFF runs and four chronological prefix/future splits:

1. compute planar posterior q_t(s) from the complete measured prefix;
2. use the reserved 4-member physical/sensor bank on the exact historical trajectory to form the q_t-weighted future predictive mixture, marginalizing H,Q,Z,R;
3. form the source-independent geometry-prior predictive mixture using the exact same reserved nuisance family;
4. compare multivariate energy scores on the disjoint future segment.

A run passes iff:

- mean future predictive gain >0;
- posterior predictive beats prior predictive on >=3/4 segments.

Global PASS iff:

- total >=20/30;
- H01>=5/10;
- H02>=5/10;
- H03>=5/10.

If FAIL:

`PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`.

No nuisance expansion, score change, network change, Gate or threshold tuning.

If PASS, automatically freeze science and continue.

## 8. Open development truth once — offline safety only

Now, and only now, load the already-preserved 30-run source truth/localization metrics.

Compare the frozen PF-DEI planar posterior/expected source location with native PMFS on exactly the same historical OFF observations.

Hard safety stop if:

- pooled expected-location error is >5% worse than native; or
- any new already-defined false-confident collapse occurs.

Then terminal:

`PF_DEI_OFFLINE_SAFETY_NO_GO`.

Otherwise do not tune anything; continue.

## 9. Runtime integration

Implement isolated mode `pfdei_sr_v2` without changing Classic OFF or frozen historical modes.

At each native PMFS source-update point:

1. collect the complete causal measured prefix;
2. evaluate the frozen House model for each current stable planar carrier;
3. compute `q_pfdei(s)=normalize(q0(s)*exp(mean_3_model_logits))` using stable log-sum-exp;
4. replace only the native source-evidence/posterior channel with q_pfdei;
5. keep native navigation-cost planner, feasible-target logic, motion controller, sensing cadence and stopping semantics unchanged.

Forbidden:

- multiplying PF-DEI by native gas posterior;
- minimum-KL/native blending;
- posterior reset/temperature;
- Active Probe;
- House/seed thresholds;
- future samples.

Require Python/runtime numerical parity on fixed synthetic prefixes and source permutations before smoke.

## 10. Six infrastructure smoke runs

Run H01/H02/H03 with seeds 314159 and 271828.

Smoke is for infrastructure/parity/causality only. Fix engineering defects without changing the scientific method. Do not tune from smoke localization error.

If the frozen method cannot execute causally/reliably despite engineering repair:

`PF_DEI_RUNTIME_ENGINEERING_NO_GO`.

If smoke passes, automatically continue.

## 11. 60-arm development matrix

Run exactly:

`H01,H02,H03 x seeds0..9 x OFF/ON = 60 arms`

- OFF = Classic PMFS;
- ON = frozen `pfdei_sr_v2`;
- 300 s;
- paired deterministic setup;
- no scientific changes during matrix.

Development GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all parity/runtime contracts pass.

If any fail:

`PF_DEI_MAIN_INNOVATION_NO_GO`.

Do not retune seeds0..9.

If all pass:

`PF_DEI_MAIN_INNOVATION_DEVELOPMENT_GO`

and continue automatically.

## 12. Confirmatory seeds

Freeze everything and run H01/H02/H03 x seeds10..19 x OFF/ON with the identical contract.

No retuning.

Final terminal success:

`PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.

Otherwise:

`PF_DEI_CONFIRMATORY_NO_GO`.

## 13. Terminal states and one final report

Do not send intermediate "should I continue" requests. Continue until exactly one terminal state:

- `STOP_PF_DEI_PLANAR_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`
- `PF_DEI_2D3D_GEOMETRY_SUPPORT_NO_GO`
- `PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`
- `PF_DEI_PHYSICAL_BANK_ENGINEERING_NO_GO`
- `PF_DEI_INFERENCE_ENGINE_NO_GO`
- `PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`
- `PF_DEI_OFFLINE_SAFETY_NO_GO`
- `PF_DEI_RUNTIME_ENGINEERING_NO_GO`
- `PF_DEI_MAIN_INNOVATION_NO_GO`
- `PF_DEI_CONFIRMATORY_NO_GO`
- `PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.

At termination produce one consolidated report with exact commits/hashes, support/height/Q/nuisance manifests, simulation-bank completeness, synthetic qualification, historical truth-blind qualification, offline safety, runtime parity, smoke, 60-arm results, confirmatory results if reached, final verdict, and the scientifically supported failure/success mechanism.

This is the final PF-DEI-SR V2 experiment campaign. No V3 hand-feature or result-driven nuisance redesign is authorized.