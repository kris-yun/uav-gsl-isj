# PF-DEI FINAL METHOD FREEZE V3 — REGION-LATENT SOURCE

Date: 2026-08-28
Status: FINAL SCIENTIFIC METHOD / NO RESULT-DEPENDENT REDESIGN AFTER THIS FILE

This V3 contract supersedes V1/V2 source-support contracts while preserving their terminal reports as valid historical evidence under those contracts. V3 is not justified by localization outcomes; it corrects the source-state semantics from repository source code.

## 1. Frozen evidence

Preserve without reinterpretation:

- V5 passive cumulative evidence: 0/30 ACCEPT.
- V6-A continuous source diagnostic: 0/30 predictive pass; H01/H02/H03 transfer-only = 1/10, 0/10, 2/10; absolute adequacy = 0/30.
- Occupancy is not physical ppm.
- Native observation operator is closed: source/transport -> physical concentration -> run-persistent native sensor -> measured ppm -> PMFS block decision.
- Exact historical inverse-sensor replay: 30/30 runs, 4049/4049 blocks; 159/4049 ideal/native block decisions differ.
- Sensor memory is a real deterministic observation-aliasing mechanism but is not sufficient by itself to explain source-evidence failure.
- V1 source-support terminal `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED` remains valid under the V1 requirement for a unique xyz per carrier.
- V2 terminal `PF_DEI_2D3D_GEOMETRY_SUPPORT_NO_GO` remains valid under the V2 requirement that the stored carrier representative `(x,y)` itself be a legal 3-D source column.

## 2. Source-code correction that defines V3

Repository source establishes that the persistent source carrier is a geometry region, not a point:

- persistent carriers are fixed rectangles of up to 2x2 PMFS cells;
- only 2-D free cells inside the rectangle contribute to the carrier;
- the stored `candidate.point` / manifest `(x,y)` is the arithmetic mean of those free-cell centers;
- carrier prior mass is proportional to the number of 2-D free cells in the carrier;
- the stable ID encodes the rectangle, `quadtree_originX_originY_sizeX_sizeY`.

Therefore the representative `(x,y)` is a label/descriptor and may be physically invalid as a 3-D point without invalidating the carrier.

The final localization target is the discrete planar carrier region `S`, not the representative point and not a unique `(x,y,z)` point.

## 3. Final generative graph

Target:

- `S`: persistent planar carrier region, global for the run.

Nuisance:

- `U`: unresolved physical source placement inside the carrier, including horizontal free-cell choice and source height;
- `Z`: run-level GADEN transport stochastic realization;
- `R_t`: run-persistent native sensor state.

Source strength is frozen at `Q = 10.0 ppm` because the V2 source-independent configuration audit established that value. Do not reopen Q.

Generative chain:

`(S,U,Z,Q=10) -> C_t -> R_t -> M_t -> PMFS block events`.

Runtime inference observes causally available measured ppm `M_t`, pose, time, wind and stop/block markers. Historical `true_gas_ppm` is never an inference input.

## 4. Exact carrier-region support

For each carrier `s`, recover its native rectangle from the stable ID / frozen manifest.

Let `F_s` be the exact set of PMFS 2-D cells inside that rectangle whose frozen PMFS occupancy is `Free`.

Mandatory identity:

`carrier_id <-> rectangle <-> F_s <-> geometry_prior mass`.

The prior is frozen exactly as the original geometry-only carrier construction:

`q0(s) = |F_s| / sum_r |F_r|`.

Do not use the representative carrier `(x,y)` to define physical source placement.

## 5. 2-D to 3-D physical placement nuisance U

For each 2-D free cell `f in F_s`:

1. use the exact native cell center `(x_f,y_f)`;
2. map that horizontal coordinate into the authoritative GADEN 3-D occupancy geometry using source-proven coordinate transforms;
3. obtain `V_f`, the set of source-admissible free 3-D voxel-center heights at that horizontal cell according to native geometry/source-placement semantics.

Define `F_s+ = {f in F_s : |V_f| > 0}`.

Hard geometry condition:

`|F_s+| > 0` for every carrier with nonzero q0 mass.

If any carrier has no legal placement anywhere in its own rectangle, terminate `PF_DEI_REGION_3D_SUPPORT_NO_GO`.

Do not expand outside the carrier rectangle. Do not copy historical source z. Do not force the representative mean point to be legal.

### 5.1 Conditional placement distribution

Preserve the planar carrier prior q0. Conditional on carrier s:

- horizontal source cell is uniform over `F_s+`;
- conditional on horizontal cell f, source height is uniform over `V_f`.

Thus each valid horizontal free cell has equal conditional mass regardless of how many vertical free voxels it contains.

This distribution is source-truth independent and uses geometry only.

For deterministic finite simulation, flatten the hierarchical distribution into a stable CDF ordered by native 2-D cell index then z. Use eight training nuisance quantiles:

`u_train = [1,3,5,7,9,11,13,15] / 16`

and four reserved qualification/predictive quantiles:

`u_reserved = [2,6,10,14] / 16`.

The placement selected by a quantile is a latent physical simulation member, not a redefinition of the carrier target.

## 6. GADEN stochastic transport — deterministic seed hook

The preserved VM GADEN source uses default-constructed static `std::mt19937` engines and does not expose a transport seed. V3 therefore authorizes exactly one simulator engineering change: an isolated deterministic RNG initialization hook.

Allowed modification:

- expose explicit seeds/substreams for every random engine that participates in native filament/transport generation;
- change RNG initialization only;
- do not change any probability distribution, transport equation, concentration equation, timestep, wind, source physics or sensor physics.

Mandatory parity before use:

1. build an unmodified reference and an isolated seeded build;
2. with the seed hook disabled/default-compatible, reproduce the unmodified native output on controlled fields/query points within the established numerical tolerance (bitwise if achievable);
3. prove source/config/library hashes;
4. prove changing the seed changes stochastic realization while preserving all non-RNG configuration.

If the seed hook cannot be isolated and parity-proven, terminate `PF_DEI_GADEN_RNG_CONTROL_NO_GO`.

Freeze joint training transport seeds:

`101, 211, 307, 401, 503, 601, 701, 809`.

Freeze reserved transport seeds:

`907, 1009, 1103, 1201`.

Member j pairs transport seed j with placement quantile j. There is no Cartesian nuisance expansion and no result-driven member increase.

## 7. Native physical trace generation

For each `(House, carrier s, joint nuisance member j)` generate a coherent physical source realization using the exact latent placement selected from the carrier and the frozen transport seed.

Use native GADEN physical concentration and the already parity-proven native persistent sensor.

Engineering representation may be either:

- a materialized native field queried along many trajectory schedules; or
- a streaming native trace generator that produces exactly the same physical concentration at requested pose/time points.

The choice is engineering only. It must pass stored-vs-direct native query parity and clean-process reproducibility.

Never derive ppm from PMFS/CTT occupancy.

## 8. Source-independent trajectory library

For each House use:

- the 10 historical OFF pose/time skeletons with all gas/source labels stripped;
- 20 additional source/gas-independent feasible native-navigation skeletons, deterministic seeds `3001..3020`, for training;
- 5 reserved source/gas-independent feasible skeletons, deterministic seeds `4001..4005`, for qualification.

Trajectory skeleton is sampled independently of source carrier.

## 9. Final candidate-conditioned sequential ratio estimator

Train per-House weights with one common architecture/training recipe.

Target:

`f_psi(D_1:t, s, kappa) ~= log p(D_1:t | S=s,kappa) - log p(D_1:t | kappa)`

where simulator generation marginalizes the frozen joint nuisance `(U,Z,R)`.

Posterior:

`q_t(s) proportional q0(s) * exp(mean_j f_psi_j(D_1:t,s,kappa))`.

Do not multiply independent context likelihoods. Do not multiply q_t by the native gas posterior from the same observations.

### 9.1 Candidate descriptor

The candidate is a region. Candidate-conditioned inputs may use only geometry descriptors that are fixed before gas observation:

- robot position relative to carrier free-cell centroid;
- carrier rectangle physical width/height;
- four-bit 2x2 free-cell mask (zero padded on map edges);
- normalized free-cell count;
- current measured ppm transformed as `log1p(measured_ppm / thresholdGas)`;
- causally available measured wind;
- delta time;
- stop-start and block-boundary markers.

Do not provide a latent placement U to the classifier at inference; U is marginalized nuisance.

### 9.2 Frozen network

Use the same causal TCN as V2, with candidate-geometry features appended to the sample embedding:

- sample encoder -> width 64 -> GELU;
- 9 residual causal Conv1D blocks;
- width 64, kernel 5;
- dilations `1,2,4,8,16,32,64,128,256`;
- LayerNorm + GELU;
- masked global mean pooling concatenated with final valid hidden state;
- MLP `128 -> 64 -> 1` logit (increase only the first input projection dimension as required by the fixed region features; hidden widths remain frozen).

Optimization:

- balanced BCE joint-vs-product;
- AdamW lr `3e-4`, weight decay `1e-4`;
- batch 64;
- max 100 epochs;
- early-stop patience 10 on simulator-only validation BCE;
- gradient clip 1.0;
- training model seeds `1701,1702,1703`;
- final log ratio = arithmetic mean of the three logits.

No architecture sweep, temperature fitting or historical-performance tuning.

Positive pair: simulator-generated `(D,s)`.
Negative pair: same exact D/trajectory/environment with an independent alternative carrier sampled from q0.

## 10. Synthetic qualification

Use only reserved placement quantiles, reserved transport seeds and reserved trajectory skeletons.

Select 32 source carriers per House by deterministic stable-ID hash/coverage independent of historical truth. Use four reserved joint nuisance members -> minimum 128 cases per House.

Require all:

- synthetic true carrier top-5 recall >= 0.75;
- median normalized true-carrier rank <= 0.10;
- mean log posterior/prior gain at true carrier > 0;
- carrier-index permutation invariance;
- zero forbidden-field leakage;
- each of the three training-seed models individually improves mean true-carrier rank over q0 baseline.

Failure is terminal `PF_DEI_INFERENCE_ENGINE_NO_GO`.

## 11. Historical truth-blind future-predictive qualification

Freeze weights before loading historical measured ppm.

For 30 historical OFF runs, use four chronological prefix/future splits. At each split:

1. infer q_t(s) from the complete causal measured prefix;
2. build future predictive mixture using q_t(s) and the four reserved `(U,Z)` joint nuisance traces on that exact trajectory;
3. compare multivariate energy score against the q0 prior-predictive mixture.

Run PASS iff:

- mean future predictive gain > 0;
- q_t predictive beats q0 predictive in >=3/4 future segments.

Global PASS iff:

- >=20/30 runs PASS;
- H01 >=5/10;
- H02 >=5/10;
- H03 >=5/10.

Failure is terminal `PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`. No nuisance/model redesign follows.

## 12. Development truth opening and offline safety

Only after Section 11 passes may development true source/error be read.

Project carrier posterior back to the native PMFS 2-D source grid without injecting subcarrier 3-D information:

for each original free 2-D cell `f in F_s`:

`q_cell(f) = q_carrier(s) / |F_s|`.

This exactly preserves carrier mass and the native geometry-only planar state definition.

Hard offline safety stop if:

- pooled expected-location error is >5% worse than native PMFS on the same historical observations; or
- any new project-defined false-confident collapse appears.

Otherwise freeze all science and continue.

## 13. Runtime semantics

Create isolated mode `pfdei_sr_v3`.

At each native PMFS source update:

1. ingest complete causal measured run prefix;
2. infer carrier posterior q_t(s);
3. project q_t(s) uniformly to original free 2-D cells within each carrier as in Section 12;
4. replace only the source-evidence/source-posterior channel used by native destination evaluation;
5. retain native navigation-cost-aware planner, feasible target logic, sensing schedule, controller and stopping semantics.

Forbidden:

- multiply PF-DEI by native gas posterior from same data;
- minimum-KL/blend/temperature/reset;
- Active Probe;
- House/seed performance thresholds;
- future samples.

Require fixed-prefix Python/runtime parity and carrier/source-index permutation invariance.

## 14. Closed-loop development and confirmation

Infrastructure smoke: H01/H02/H03 with seeds 314159 and 271828. Fix engineering-only defects; no scientific changes.

Development matrix:

`H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms`, 300 s.

OFF = Classic PMFS.
ON = frozen `pfdei_sr_v3`.

Development GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all runtime/parity contracts pass.

Failure: `PF_DEI_MAIN_INNOVATION_NO_GO`, terminal, no retuning.

If GO, freeze everything and run H01/H02/H03 seeds 10..19 with identical OFF/ON contract.

Final success: `PF_DEI_MAIN_INNOVATION_CONFIRMATORY_GO`.
Otherwise: `PF_DEI_CONFIRMATORY_NO_GO`.

## 15. Scientific claim if successful

The supported mechanism is not generic causal-effect identification. The paper-level claim is:

> Robotic gas-source localization becomes more robust when the planar source hypothesis is treated as a persistent geometry region and unresolved 3-D source placement, stochastic transport and persistent sensor dynamics are marginalized by a native physics simulator over the complete chronological observation prefix.

No additional V4 method redesign is authorized from development outcomes.