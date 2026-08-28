# CODEX FINAL TASK V3 — PF-DEI region-latent autonomous closure

Date: 2026-08-28
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative method:

`docs/PF_DEI_FINAL_METHOD_FREEZE_V3_REGION_LATENT_20260828.md`

This is the only execution authority after V2. V1/V2 terminal reports are preserved evidence, not current stopping conditions. Do not stop after an intermediate successful stage to ask for another method design. Continue automatically until one terminal state below is reached. Engineering retries are allowed only when scientific inputs remain byte-for-byte frozen.

## 0. Preserve and merge history

Preserve all reachable evidence including:

- `a504e0e` forward operator closure;
- `6fbf08c` sensor-memory audit;
- `33f9a80` exact deconvolution;
- `55dd893` run-level bank blocker;
- `2fc133f` V1 source-support terminal evidence;
- `a2b8040` V2 geometry-support terminal evidence, if present on the local evidence branch;
- all GitHub V1/V2 method commits.

Do not reset/overwrite historical evidence.

Run current PF-DEI selftests first. A regression may be fixed only as an engineering defect without changing frozen science.

## 1. Reconstruct the exact region-valued carrier state

From repository source and frozen manifests, reconstruct every persistent carrier as:

- stable carrier ID;
- rectangle `(origin_i,origin_j,size_i,size_j)`;
- exact list of original PMFS 2-D free cells `F_s` inside that rectangle;
- representative centroid retained only as metadata;
- geometry-prior mass `|F_s| / total_free_cells`.

Audit all 150 context priors against this region mapping.

Do not require the representative centroid to be a legal 3-D source point.

Hard stop only if the source-code region identity or geometry-prior alignment cannot be reproduced:

`PF_DEI_REGION_SUPPORT_IDENTITY_NO_GO`.

## 2. Build the region-to-3D latent placement support

For every original free 2-D cell in every carrier:

1. map the exact native PMFS cell center to GADEN 3-D coordinates using source-proven transforms;
2. enumerate source-admissible free voxel-center heights from authoritative 3-D occupancy/source-placement semantics;
3. create `F_s+` and the hierarchical conditional distribution from the V3 freeze.

Required artifact:

`artifacts/pf_dei_v3/source_region_3d_support_manifest.csv`

with carrier ID, 2-D cell index/xy, legal-z count, legal z values or immutable external reference/hash, and conditional weights. No truth/performance fields.

Every nonzero-prior carrier must have at least one legal placement somewhere inside its own rectangle.

If any does not:

`PF_DEI_REGION_3D_SUPPORT_NO_GO`.

Do not expand outside the carrier rectangle and do not use historical source z.

Verify that the V2 49/41/51 representative-centroid failures are explainable as centroid-label failures rather than empty carrier-region support; report exact counts but do not use outcomes to modify support.

## 3. Freeze source strength and final nuisance members

Keep `Q=10.0 ppm` exactly as established by the source-independent V2 configuration audit.

Create eight training joint nuisance members by pairing, in order:

- placement CDF quantiles `[1,3,5,7,9,11,13,15]/16`;
- GADEN transport seeds `101,211,307,401,503,601,701,809`.

Create four reserved members by pairing:

- placement CDF quantiles `[2,6,10,14]/16`;
- GADEN transport seeds `907,1009,1103,1201`.

No Cartesian expansion and no result-driven member changes.

## 4. Implement isolated deterministic GADEN RNG control

Audit every random engine used in the native filament/transport generation path.

Create an isolated patched GADEN build that exposes deterministic RNG initialization only. Do not alter distributions, equations, timesteps, wind, Q, concentration computation or sensor model.

### 4.1 Compatibility parity

Before generating any new dataset:

- run unmodified native GADEN and patched GADEN in compatibility/default mode on controlled sources/fields;
- compare at least 100 pre-frozen concentration query points across all three Houses where supported;
- require bitwise equality if the build/runtime permits, otherwise the already established numerical query tolerance;
- hash source, compiler/build flags, libraries and binaries.

### 4.2 Seed effectiveness

For at least one controlled source per House, show that two nondefault frozen seeds produce different stochastic plume realizations while all non-RNG configuration remains identical.

If the RNG hook cannot be isolated, complete and parity-proven:

`PF_DEI_GADEN_RNG_CONTROL_NO_GO`.

Do not fake multiple members by process timing or uncontrolled randomness.

## 5. Implement one reusable native trace generator

Build one audited CLI/library/orchestration path:

`House + carrier_id + joint_member_id + trajectory_schedule -> physical_ppm[T], measured_ppm[T]`.

It must:

1. select the latent placement deterministically from the carrier-region conditional CDF and the member quantile;
2. generate native GADEN transport with the frozen member seed;
3. query exact physical concentration at requested pose/time samples;
4. propagate the exact run-persistent native sensor from run start;
5. return measured ppm and exact metadata/hashes.

It may internally materialize a field or stream the simulator, whichever is simpler, but outputs must be parity-equivalent to the native concentration query.

### 5.1 Smoke

Use one carrier with >=2 legal horizontal cells if available, one carrier with a V2-invalid representative centroid but V3-valid region support, two nuisance members, one historical geometry-only trajectory and one random source-independent trajectory.

Require:

- direct native physical-query parity on >=50 pre-frozen points;
- clean-process reproducibility;
- exact sensor-forward parity;
- no occupancy-derived ppm;
- no historical true source/z/gas.

Engineering failures may be repaired without changing source/nuisance definitions. If arbitrary legal placements cannot be simulated through native GADEN:

`PF_DEI_NATIVE_TRACE_GENERATOR_NO_GO`.

## 6. Generate the final simulation dataset

For each House:

Trajectory library:

- 10 historical OFF geometry-only pose/time skeletons; strip all gas/source labels;
- 20 random feasible source-independent training skeletons using deterministic seeds `3001..3020`;
- 5 reserved source-independent qualification skeletons using seeds `4001..4005`.

Training generation must sample carrier independently of trajectory.

Generate enough traces to cover every carrier with every one of the eight training joint nuisance members and all 30 training skeletons, reusing a physical field across trajectories only when provenance proves reuse is exact. Query-on-demand/streaming is allowed to reduce storage.

Reserved traces use only the four reserved nuisance members and the five reserved trajectories.

No historical measured ppm is used to train the model.

Hash all manifests and simulator artifacts.

## 7. Train the frozen PF-DEI-SR V3 ratio estimator

Implement exactly Section 9 of the V3 freeze.

Candidate descriptor must represent the carrier region, not a hidden source placement:

- free-cell centroid;
- rectangle extent;
- 2x2 free-cell mask;
- free-cell count;
- sample-wise robot-relative-to-centroid geometry;
- measured ppm transform;
- measured wind;
- delta time and stop/block markers.

Do not expose latent placement U to the classifier.

Use exactly the frozen causal TCN, optimizer, training seeds and early-stop rule. No architecture/hyperparameter search.

Positive `(D,s)` and negative `(D,s_minus)` pairs reuse the identical D/trajectory/environment; only carrier candidate changes.

Save weights/hashes for all three training-seed models.

## 8. Reserved synthetic qualification

Choose 32 carriers per House by deterministic stable-ID hash/coverage independent of historical truth. For each carrier use all four reserved joint nuisance members on reserved trajectories to obtain at least 128 cases per House.

Apply exactly the frozen criteria:

- top-5 recall >=0.75;
- median normalized true-carrier rank <=0.10;
- positive mean log posterior/prior gain;
- permutation invariance;
- zero forbidden-field leakage;
- each individual training-seed model beats q0 rank baseline.

If any House fails:

`PF_DEI_INFERENCE_ENGINE_NO_GO`.

No redesign/rerun with altered science.

If PASS, continue automatically.

## 9. Historical truth-blind future-predictive qualification

Freeze weights before loading historical measured ppm.

For each of 30 OFF runs and each of four chronological prefix/future splits:

- infer carrier posterior q_t from measured prefix only;
- construct the future predictive mixture over carriers and the four reserved joint nuisance traces on that exact historical trajectory;
- compare multivariate energy score against q0 prior-predictive mixture.

Run PASS iff mean gain >0 and posterior predictive beats prior on >=3/4 future segments.

Global PASS iff >=20/30 and each House >=5/10.

Failure:

`PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`.

No transport/member/network expansion follows.

If PASS, continue automatically.

## 10. Open development truth once — offline safety only

Project carrier posterior to original PMFS 2-D free cells exactly:

`q_cell(f) = q_carrier(s) / |F_s|` for every original free cell f in carrier s.

This projection deliberately does not use which subcell/z placements were physically valid in the nuisance simulator; 3-D nuisance affects carrier evidence only.

Compare against native PMFS on the same 30 historical observations.

Hard stop only if pooled expected-location error is >5% worse or any new frozen false-confident-collapse event appears:

`PF_DEI_OFFLINE_SAFETY_NO_GO`.

Do not tune from error values.

Otherwise continue.

## 11. Runtime `pfdei_sr_v3`

Integrate an isolated runtime mode without modifying Classic OFF.

At each source update:

- use the complete causal measured prefix;
- score every current persistent carrier with the frozen three-model ensemble;
- form `q_carrier(s) proportional q0(s)*exp(mean logits)`;
- uniformly project carrier mass to original 2-D free cells;
- replace only the PMFS source-evidence/posterior grid used by destination evaluation;
- leave native navigation-cost planner, feasible targets, motion controller, sensing cadence and stopping semantics unchanged.

Forbidden: posterior multiplication with native gas evidence, blend/KL/temperature/reset, Active Probe, future samples, House/seed performance thresholds.

Require Python/runtime fixed-prefix and permutation parity before closed loop.

## 12. Six infrastructure smoke runs

Run H01/H02/H03 with seeds 314159 and 271828.

Use localization output only for crash/collapse safety; do not change science. Fix only engineering defects preserving hashes/model/nuisance definitions.

If the frozen method cannot be executed causally/reliably despite engineering repair:

`PF_DEI_RUNTIME_ENGINEERING_NO_GO`.

Otherwise continue automatically.

## 13. 60-arm development matrix

Run exactly:

`H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms`, 300 s.

OFF = Classic PMFS.
ON = frozen `pfdei_sr_v3`.

No scientific edits during the matrix.

GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all parity/runtime contracts pass.

If any fail:

`PF_DEI_MAIN_INNOVATION_NO_GO`.

Terminal. No retuning on seeds 0..9.

If all pass:

`PF_DEI_MAIN_INNOVATION_DEVELOPMENT_GO`

and continue automatically.

## 14. Confirmatory matrix

Freeze every artifact from development GO.

Run H01/H02/H03 seeds 10..19 with identical paired OFF/ON 300 s contract.

No retuning.

Final success:

`PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.

Otherwise:

`PF_DEI_CONFIRMATORY_NO_GO`.

## 15. Final response only

Do not return intermediate `should I continue?` messages. Continue until one terminal state:

- `PF_DEI_REGION_SUPPORT_IDENTITY_NO_GO`
- `PF_DEI_REGION_3D_SUPPORT_NO_GO`
- `PF_DEI_GADEN_RNG_CONTROL_NO_GO`
- `PF_DEI_NATIVE_TRACE_GENERATOR_NO_GO`
- `PF_DEI_INFERENCE_ENGINE_NO_GO`
- `PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`
- `PF_DEI_OFFLINE_SAFETY_NO_GO`
- `PF_DEI_RUNTIME_ENGINEERING_NO_GO`
- `PF_DEI_MAIN_INNOVATION_NO_GO`
- `PF_DEI_CONFIRMATORY_NO_GO`
- `PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.

Return one consolidated terminal report with exact hashes, preserved V1/V2 evidence, region support statistics, RNG parity, simulator/training qualification, historical predictive result if reached, offline/runtime result if reached, 60-arm/confirmation result if reached, and one final scientific interpretation.
