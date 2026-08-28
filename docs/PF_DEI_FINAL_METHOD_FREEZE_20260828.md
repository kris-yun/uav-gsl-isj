# PF-DEI FINAL METHOD FREEZE — 2026-08-28

Status: **FINAL DEVELOPMENT METHOD / NO RESULT-DEPENDENT REDESIGN AFTER THIS FILE**

This file supersedes the earlier exploratory PF-DEI variants (occupancy likelihood, Markov/semi-Markov, Active Probe, component Gate, and post-result transport expansion).

## 1. What has already been established

Preserve without reinterpretation:

- V5 passive cumulative evidence: 0/30 ACCEPT.
- V6-A continuous source diagnostic after removing hard components: 0/30 predictive pass; H01/H02/H03 transfer-only 1/10, 0/10, 2/10; absolute adequacy 0/30.
- CTT occupancy is not physical ppm and cannot be converted empirically to ppm.
- Native physical observation chain is closed and parity-tested:
  `source -> GADEN transport -> physical concentration -> run-persistent dynamic sensor -> measured ppm -> exact PMFS block decision`.
- Exact historical sensor inversion is valid only for the frozen zero-noise symmetric historical configuration; 30/30 runs and 4049/4049 blocks reconstructed, with 159/4049 native-vs-ideal block-decision flips.
- Sensor memory is a real trajectory-dependent observation-aliasing mechanism but does not alone explain the global source-evidence failure.
- The historical single-source native physical forward operator is closed. The remaining engineering object is the candidate-source physical simulation bank.

## 2. Final scientific hypothesis

The failed models assigned source evidence using an incorrect local/static observation representation. The final method tests one paper-level hypothesis:

> Source location is a global latent cause, while plume transport realization, emission-strength nuisance (if not source-proven fixed), and persistent sensor dynamics are nuisance mechanisms that must be marginalized through the native forward simulator using the complete chronological observation prefix.

The method is named:

**PF-DEI-SR — Physics-Factorized Dynamic Event Inference with Sequential Ratio posterior**

Chinese: **物理因子化动态事件推断—序贯比率后验**.

This is physics/causal factorization, not Pearl/Rubin causal-effect estimation.

## 3. Final generative graph

Target:

- `S`: source position, global for the run.

Nuisance:

- `Q`: source emission strength, global for the run **only if it is not source-proven fixed and known**;
- `Z`: a complete run-level native GADEN transport stochastic realization. Do not reset or independently resample `Z` at PMFS context boundaries unless native simulator provenance proves such a reset;
- `R_t`: run-persistent native sensor internal state.

Generated variables:

`(S,Q,Z) -> C_t -> R_t -> M_t -> PMFS block events`.

Runtime inference uses `M_t` (measured ppm), not historical `true_gas_ppm` and not occupancy.

Exact historical deconvolution remains a mechanism/parity diagnostic only; it is **not** required by the final runtime algorithm.

## 4. Source-strength rule — resolve before any historical source score

The earlier RMFE work exposed an amplitude-scale mismatch, so source amplitude may not be silently fixed by convenience.

Before generating the final simulation family, audit authoritative simulator/run configuration without reading source location or localization outcome:

1. If emission strength is proven to be one fixed known value across the preserved historical experiment and the candidate forward generator uses that exact value, freeze `Q` to that value.
2. Otherwise `Q` becomes a global source-independent nuisance. Its support must be frozen solely from documented simulator/source configuration provenance before historical source-evidence evaluation.
3. If native concentration is source-proven linear in `Q`, generate one unit/reference field and scale analytically; prove parity on synthetic fields.
4. If linearity is not source-proven, simulate every frozen `Q` member explicitly.
5. Never fit `Q` from H01/H02/H03 true source, localization error, or historical source-ranking outcomes.

If neither a known `Q` nor a defensible provenance-based nuisance support can be established, stop `PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`.

## 5. One final nuisance family, frozen before historical scoring

There is no base-family-then-expanded-family loop in the final method.

Freeze one source-independent GADEN nuisance design before any new historical source-ranking result is computed.

### 5.1 Transport stochastic members

Preferred rule:

- if an explicit native GADEN RNG/substream manifest from preserved work exists, reuse it only when source/config mapping is auditable;
- otherwise use the following fixed native RNG seeds for the simulation/training family:
  `101, 211, 307, 401, 503, 601, 701, 809, 907, 1009, 1103, 1201`;
- reserve disjoint synthetic-qualification transport seeds:
  `1301, 1409, 1511, 1601`.

All other physical transport parameters remain at the exact source-proven House configuration unless they are explicitly documented as uncertain/stochastic in the preserved experiment. Do not create uncertainty ranges merely because the historical fit is poor.

Wind/environment/map are known House covariates, not tunable performance parameters.

### 5.2 Sensor

Use the exact native dynamic sensor configuration and run-persistent state. Do not reset at stop/context boundaries. Do not randomize historical sensor parameters unless the experiment provenance states they were uncertain/random.

## 6. Source support

Use the exact stable source carriers that back each run's `geometry_prior`/native source support. The mandatory identity is:

`source_id <-> physical GADEN coordinate <-> geometry_prior mass`.

Candidate-conditioned inference permits run-specific support, so cross-run integer source indices need not match. Physical coordinates/stable IDs must match their own prior exactly.

Do not union the 1,229 adaptive IDs blindly. If adaptive candidate manifests are only proposal subsets, recover the persistent source-carrier support from the context payload/provenance.

If identity cannot be proven, stop `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

## 7. Final inference target

For a House/environment `kappa`, a complete causally available measured sequence/prefix `D_1:t`, and a candidate source `s`, train a balanced joint-vs-product neural ratio estimator:

`f_psi(D_1:t, s, kappa) ~= log p(D_1:t | s, kappa) - log p(D_1:t | kappa)`

where the simulator marginalizes the frozen nuisance family `(Q,Z,R)`.

The final source posterior is recomputed from the complete prefix:

`q_t(s) proportional q0_t(s) * exp(mean_j f_psi_j(D_1:t,s,kappa))`.

`j` indexes the frozen training-seed ensemble defined below.

Do **not** independently multiply context likelihoods. Do **not** multiply this posterior into the native PMFS posterior; both use the same observations and that would double-count evidence.

At runtime PF-DEI replaces only the source-evidence/posterior channel used by the native PMFS planner. Native navigation-cost/planner semantics remain unchanged.

## 8. Final NRE architecture and training protocol

Environment-specific weights are allowed because the native forward physics differs by House, but **architecture, hyperparameters, training recipe, thresholds and validation rules are identical for H01/H02/H03**.

### 8.1 Per-sample candidate-conditioned input

At each sensor sample use only causally available fields:

- `log1p(measured_ppm / thresholdGas)`;
- candidate-relative position `(x_t-x_s, y_t-y_s, z_t-z_s)`, normalized by the House map diagonal;
- observed wind vector at that time, standardized from simulated training data only;
- `delta_t / 0.2s`;
- stop-start and block-boundary binary markers.

No true gas, true source field, localization error, future observation, native final error, or House/seed performance label.

### 8.2 Network

Use a causal TCN, not a model search:

- sample encoder: linear -> 64 -> GELU;
- 9 residual causal Conv1D blocks;
- width 64;
- kernel size 5;
- dilations `1,2,4,8,16,32,64,128,256`;
- LayerNorm and GELU in each residual block;
- masked global mean pooling concatenated with the final valid hidden state;
- MLP `128 -> 64 -> 1` logit.

No Transformer/CNN/RNN architecture sweep.

### 8.3 Optimization

- balanced BCE joint-vs-product objective;
- AdamW, learning rate `3e-4`, weight decay `1e-4`;
- batch size 64;
- maximum 100 epochs;
- early stopping patience 10 on simulator-only validation BCE;
- gradient clip 1.0;
- training model seeds `1701,1702,1703`;
- final ratio logit = arithmetic mean of the three logits.

No temperature calibration from H01/H02/H03 historical outcomes.

### 8.4 Positive/negative construction

Positive: simulator-generated `(D,s)`.

Negative: same exact `D`, same exact trajectory/environment, independent alternative source `s_minus` from the same source-support prior.

Trajectory/source shortcut is prohibited. Training source is sampled independently of the trajectory skeleton.

## 9. Source-independent trajectory library

The NRE must not be trained only on one observed historical source/trajectory pairing.

For each House:

1. Reuse the 10 historical OFF pose/time skeletons **without their gas values or true source**; when generating training simulations, sample synthetic source independently of the skeleton.
2. Add 20 map-only random feasible stop/trajectory skeletons generated with native navigation constraints and deterministic trajectory seeds `3001..3020`; trajectory target selection must be source/gas independent.
3. Reserve 5 additional map-only feasible skeletons with seeds `4001..4005` for synthetic qualification only.

All synthetic sequences use the native sampling cadence, stop/block schedule and run-persistent sensor model.

## 10. Training/qualification separation

Training may use the 12 training transport seeds and the 30 source-independent trajectory skeletons per House.

Synthetic qualification uses only:

- reserved transport seeds `1301,1409,1511,1601`;
- reserved trajectory skeletons `4001..4005`;
- experimenter-selected source candidates by a deterministic stable-ID rule, never historical true source.

No historical measured ppm enters architecture/hyperparameter selection.

## 11. Synthetic qualification rule

For each House choose up to 32 source candidates by deterministic stable-ID hashing/coverage, independent of source truth. Generate all reserved transport/trajectory combinations that are computationally feasible, with a minimum of 128 qualification cases per House.

At the final prefix require all:

- true synthetic source top-5 recall >= 0.75;
- median normalized true-source rank <= 0.10;
- mean log posterior/prior gain at the true synthetic source > 0;
- source-index permutation invariance within numerical tolerance;
- zero forbidden-field leakage;
- all three training-seed models individually beat the source-prior baseline on mean true-source rank.

If not, stop `PF_DEI_INFERENCE_ENGINE_NO_GO`. Do not change the architecture or nuisance family.

## 12. Truth-blind historical predictive qualification

After synthetic qualification, freeze all weights/hashes. Apply PF-DEI to the 30 historical OFF measured sequences without reading true source/error.

For each chronological prefix, use `q_t(s)` to form a posterior-weighted native-simulator predictive mixture for the next disjoint future segment. Compare its multivariate energy score with the source-independent `q0` prior-predictive mixture using the same frozen physical/measured simulation bank.

A run passes if mean future predictive gain is >0 and the posterior predictive mixture beats the prior mixture on at least 3 of 4 non-overlapping forward segments.

Historical qualification passes only if:

- total pass >=20/30;
- H01 >=5/10;
- H02 >=5/10;
- H03 >=5/10.

If not, stop `PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`. Do not expand transport or retune NRE.

## 13. Truth opening and runtime semantics

Only after truth-blind historical predictive qualification may localization truth/error be opened.

No scientific parameter may change after this point.

Runtime mode:

- ingest the complete causally available measured-ppm prefix;
- evaluate the frozen House PF-DEI-SR model on the current stable source support;
- compute `q_t(s) = normalize(q0_t(s) * exp(mean logit))`;
- replace only the native PMFS source-evidence/posterior input used for target selection;
- keep native PMFS navigation-cost-aware planner, motion logic, stopping logic and sensor acquisition unchanged;
- no Active Probe;
- no posterior temperature/blend/reset;
- no minimum-KL combination with the native observation posterior;
- exact native fallback only for an engineering contract violation (missing model/input/support), never based on localization outcome.

## 14. Final experimental criteria

Development matrix remains exactly:

`H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms`, 300 s, paired deterministic setup.

OFF = Classic PMFS.
ON = frozen PF-DEI-SR runtime.

Development GO requires all:

- 30/30 valid pairs;
- pooled expected-location error reduction >=10%;
- >=20/30 paired runs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses under the already-existing project metric;
- all parity/runtime contracts pass.

If GO, run untouched confirmatory seeds 10..19 with the same contract.

No retuning after development or confirmatory outcomes.
