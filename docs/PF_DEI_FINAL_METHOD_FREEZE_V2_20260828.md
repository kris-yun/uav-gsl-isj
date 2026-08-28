# PF-DEI FINAL METHOD FREEZE V2 — 2026-08-28

Status: **FINAL DEVELOPMENT METHOD V2 / NO RESULT-DEPENDENT REDESIGN AFTER THIS FILE**

This V2 freeze supersedes `PF_DEI_FINAL_METHOD_FREEZE_20260828.md`.

## 1. Why V2 is necessary

The previous autonomous run stopped at `STOP_PF_DEI_SOURCE_SUPPORT_IDENTITY_UNRESOLVED` because the persistent carrier manifests preserve only `carrier_id,x,y,free_cells`, not an authoritative GADEN `z` coordinate. The stop was correct under the previous 3-D identity contract, but the 3-D identity contract was too strong for the native PMFS problem.

Repository source proves that the native PMFS source hypothesis is planar: `SimulationSource` stores a `Vector2` point or a 2-D quadtree node; filaments are represented by `Vector2`; persistent carriers likewise preserve planar source coordinates. Therefore the scientific target must remain the native planar source location, not an invented 3-D source state.

Final target:

`S_xy = (x_source, y_source)` — global planar source location.

The missing vertical coordinate is not assigned from historical truth. It is represented as a nuisance latent:

`H = source height / vertical placement`.

The final generative graph is therefore:

`(S_xy, H, Q, Z) -> C_t -> R_t -> M_t -> PMFS block events`.

where:

- `S_xy` is the only localization target;
- `H` is a source-independent vertical-placement nuisance conditional on environment geometry;
- `Q` is global source strength if not source-proven fixed/known;
- `Z` is native GADEN transport stochasticity;
- `R_t` is the run-persistent native sensor state;
- `M_t` is measured ppm available to the algorithm.

This is a 2.5-D physics-factorized model: planar source localization with 3-D source-height uncertainty marginalized by the native simulator.

## 2. Revised source-support identity contract

The authoritative identity required for every run is now exactly:

`stable carrier id <-> native planar (x,y) <-> geometry_prior mass`.

No unique `z` is required or permitted to be copied from historical source truth.

Run-specific supports are allowed. Cross-run integer source indices need not match. Stable IDs and coordinates must align exactly to the prior used for that run.

Do not union the 1,229 adaptive IDs blindly. Recover the persistent support that actually backs `geometry_prior`.

Hard stop only if the planar identity itself cannot be proven:

`STOP_PF_DEI_PLANAR_SOURCE_SUPPORT_IDENTITY_UNRESOLVED`.

## 3. Source-height nuisance contract

The source-height distribution must be frozen before any historical source-ranking or localization result is opened.

### 3.1 Preferred authoritative route

Search only source-independent scenario/generator metadata for a benchmark/source-placement rule or admissible source catalogue that defines vertical placement for the class of possible sources. Such metadata is allowed only if it describes the candidate/source class independently of which historical source was selected.

If such a rule exists, freeze it as `p(H | S_xy, environment)`.

Forbidden: reading the particular historical source `z` and assigning that value to all candidates.

### 3.2 Geometry-only fallback

If no source-independent catalogue/rule survives, derive the vertical nuisance support from the native 3-D occupancy/source-placement geometry only.

For each planar carrier `(x,y)`:

1. transform `(x,y)` into the exact native GADEN 3-D grid frame using source-independent map metadata;
2. enumerate vertical source coordinates accepted by the native source-placement/query code and lying in free space;
3. apply only source-proven source-radius/clearance constraints if such constraints exist;
4. never consult historical source location, true gas, localization error, or observed gas to define the set.

Let the resulting ordered legal vertical set be `H_s = {h_1,...,h_K}`.

If a nonzero-prior planar carrier has no legal vertical placement, stop:

`PF_DEI_2D3D_GEOMETRY_SUPPORT_NO_GO`.

If the legal set is non-empty and no more specific source-independent placement measure exists, use the discrete uniform measure over the legal vertical source points. This is intentionally conservative: height is marginalized rather than guessed.

## 4. Source strength Q

Retain the V1 rule:

- if `Q` is source-proven fixed and known for the experiment, freeze it;
- otherwise treat `Q` as a global nuisance and freeze its support from authoritative simulator/source configuration only;
- analytical scaling is allowed only after source-level parity proves linearity in `Q`;
- never fit `Q` from H01/H02/H03 source truth, source ranking or localization performance.

Hard stop if neither fixed-known `Q` nor a defensible source-independent support exists:

`PF_DEI_SOURCE_STRENGTH_CONTRACT_NO_GO`.

## 5. One final joint nuisance ensemble

There is no post-result transport/height/source-strength expansion.

For training use eight frozen joint nuisance members. Native transport RNG seeds:

`101, 211, 307, 401, 503, 601, 701, 809`.

For source height, use the eight fixed stratified quantiles of each carrier's legal vertical distribution:

`u_H = (1,3,5,7,9,11,13,15) / 16`.

Map each `u_H` deterministically to the discrete legal vertical distribution by inverse CDF. If several quantiles map to the same legal height because the set is small, preserve the duplicate probability mass; do not invent new heights.

If `Q` is a nuisance, use the same eight strata with a fixed non-monotone permutation:

`Q-stratum permutation (0-based) = [4,0,6,2,5,1,7,3]`.

The resulting member is one joint draw `(H_j,Q_j,Z_j)` and is source-independent except that `H_j` is mapped through the carrier-specific legal geometry distribution.

Reserved qualification/predictive nuisance members use transport seeds:

`907, 1009, 1103, 1201`

and height quantiles:

`0.125, 0.375, 0.625, 0.875`.

If `Q` is a nuisance, qualification `Q` quantiles are the reverse order:

`0.875, 0.625, 0.375, 0.125`.

No nuisance member/range/count may change after historical outcomes are seen.

## 6. Native physical field bank

Materialize native GADEN physical fields for the planar source support and the frozen joint nuisance members.

Training bank key:

`(House, source_id, nuisance_train_id)`.

Reserved qualification/predictive bank key:

`(House, source_id, nuisance_eval_id)`.

Each key resolves internally to a concrete GADEN source `(x,y,h_j)`, source strength `Q_j`, transport seed/config, and exact House environment.

A field may be reused across trajectories only if House environment/time-origin/config provenance proves reuse.

Never use occupancy-derived ppm or historical `true_gas_ppm`.

Before scaling, require a smoke bank containing at least two planar source carriers with distinct x/y and at least two nuisance members, including distinct legal heights when the geometry allows. Require stored-vs-fresh native query parity and clean-process reproducibility.

## 7. Final inference target

Keep the V1 candidate-conditioned sequential ratio estimator, but the simulator now marginalizes `(H,Q,Z,R)` while the candidate supplied to the network is only planar `(x_s,y_s)`.

For measured causal prefix `D_1:t`, House/environment `kappa`, and planar candidate `s`:

`f_psi(D_1:t, s, kappa) ~= log p(D_1:t | S_xy=s, kappa) - log p(D_1:t | kappa)`.

Final posterior:

`q_t(s) proportional q0(s) * exp(mean_j f_psi_j(D_1:t,s,kappa))`.

Do not multiply by the native PMFS gas posterior; both consume the same observations.

Runtime PF-DEI replaces only the source posterior/evidence channel. Native PMFS navigation-cost-aware planning, feasible-target logic, motion controller, sensing cadence and stopping semantics remain unchanged.

## 8. Network and optimization

Retain the exact V1 frozen causal-TCN architecture and optimization recipe from `PF_DEI_FINAL_METHOD_FREEZE_20260828.md` Section 8. No architecture sweep, temperature fitting, House-specific threshold or historical-performance tuning.

Input candidate-relative position is planar x/y plus robot z as an observed trajectory covariate; no candidate source z is supplied to the inference network because height is marginalized by simulation.

## 9. Source-independent trajectory simulation

Retain the V1 trajectory rule:

- 10 historical OFF geometry/time skeletons per House with all gas/truth fields removed;
- 20 source/gas-independent feasible training skeletons, seeds `3001..3020`;
- 5 reserved source/gas-independent qualification skeletons, seeds `4001..4005`.

Training source identity is sampled independently of the trajectory skeleton.

The native persistent sensor state runs coherently from the beginning of each simulated sequence.

## 10. Synthetic qualification

Use only held-out planar source carriers selected deterministically by stable-ID hash, the reserved nuisance members, and reserved trajectory skeletons.

Minimum 128 synthetic cases per House.

Require all:

- true synthetic planar source top-5 recall >= 0.75;
- median normalized true-source rank <= 0.10;
- mean log posterior/prior gain at the true planar source > 0;
- source-index permutation invariance;
- zero forbidden-field leakage;
- all three training-seed models individually beat the geometry-prior baseline on mean true-source rank.

If any House fails:

`PF_DEI_INFERENCE_ENGINE_NO_GO`.

No redesign is allowed.

## 11. Historical truth-blind predictive qualification

Freeze weights before historical measured ppm is loaded for qualification.

For four chronological prefix/future splits per run:

1. compute planar posterior `q_t(s)` from the complete measured prefix;
2. form a posterior-weighted reserved native-simulator predictive mixture for the disjoint future segment, marginalizing the four reserved `(H,Q,Z,R)` nuisance members;
3. compare its multivariate energy score with the geometry-prior predictive mixture using the identical reserved nuisance family.

Run PASS:

- mean future predictive gain > 0;
- posterior predictive beats prior predictive in >=3/4 future segments.

Global PASS:

- >=20/30 runs;
- each House >=5/10.

Otherwise terminal:

`PF_DEI_HISTORICAL_PREDICTIVE_NO_GO`.

No transport/height/Q expansion or score retuning is permitted.

## 12. Truth opening, runtime and closed-loop evaluation

If truth-blind qualification passes, continue automatically with the already frozen sequence:

1. open development truth once for offline safety only;
2. stop if pooled offline expected-location error is >5% worse than native PMFS or any new false-confident collapse appears;
3. implement isolated `pfdei_sr` runtime source-posterior replacement only;
4. require fixed-prefix Python/runtime parity;
5. run six engineering smoke runs on seeds 314159 and 271828 for H01/H02/H03;
6. run H01/H02/H03 x seeds0..9 x OFF/ON = 60 development arms, 300 s;
7. GO only if pooled expected-location error reduction >=10%, >=20/30 pairs improve, no House degrades >5%, zero new false-confident collapses, and all parity/runtime contracts pass;
8. if development GO, freeze everything and run seeds10..19 confirmatory OFF/ON without any changes.

No Active Probe, posterior blend, minimum-KL mixing with native gas posterior, temperature, House threshold or post-result model revision.

## 13. Scientific interpretation

A successful result supports the paper-level mechanism:

> planar source location is recoverable only after marginalizing 3-D vertical placement, emission scale, turbulent transport realization and persistent sensor dynamics through the native physical simulator over the complete chronological observation history.

A failure after this V2 freeze is a genuine PF-DEI-SR NO-GO for the present simulator/data regime. Do not create V3 by adding hand features or result-driven nuisance ranges.