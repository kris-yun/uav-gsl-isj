# CG-PC-CTT V3 research derivation — observation-conditioned quotient + host-aware bridge

Date: 2026-08-27  
Status: **THEORY / DIAGNOSTIC PROTOTYPE ONLY**  
Parent: `research/cg-pc-ctt-fasttrack-closedloop-prep`  
Frozen V2 is not modified by this document.

## 0. Scientific problem exposed after V2

Gate V2 correctly repairs the finite-M source-mean noise failure of V1, but its statistic is computed on the whole candidate x transport-member forward field. It therefore answers:

> Does the forward-model family contain a stable source-sensitive structure?

It does **not** answer:

> Do the observations actually collected by the robot so far contain enough source-specific information to resolve the local source alternatives that matter now?

This distinction is now empirical, not speculative:

- H03 full bank `phi[10,206,8,626]`: global V2 = 10/10 PASS.
- Deterministic feature-axis stress 626 -> 313 -> 157 -> 79: still 10/10 PASS.
- A recovered H02 feasibility context `166 x 8 x 631`: global V2 also strongly PASS.
- On H03, global V2 still passes 10/10 when only four randomly selected query-cell features are retained, while local nearest-neighbour source-pair reproducibility is poor at such sparse support.

Across five frozen random subsets per support size and all ten H03 contexts, the mean fraction of nearest-neighbour physical source pairs with exact member sign-flip `p<=0.01` is approximately:

| observed/query support Q | pair p<=0.01 | pair p>0.05 |
|---:|---:|---:|
| 1 | 0.038 | 0.912 |
| 2 | 0.067 | 0.831 |
| 4 | 0.157 | 0.736 |
| 8 | 0.266 | 0.526 |
| 16 | 0.380 | 0.390 |
| 32 | 0.529 | 0.264 |
| 64 | 0.696 | 0.132 |
| 128 | 0.800 | 0.069 |
| 256 | 0.871 | 0.050 |
| 626 | 0.907 | 0.021 |

The next research object must therefore be **observation-conditioned spatial resolution**, not another global threshold on V2.

---

## 1. 2026 cross-domain theoretical sources and what is actually borrowed

This is not a literature-name collage. Each source contributes one explicit mathematical design principle.

### 1.1 Geometry-aware brain source imaging — Nature Biomedical Engineering 2026

Wang et al., *A geometry aware framework enhances noninvasive mapping of whole human brain dynamics*, Nature Biomedical Engineering (2026), DOI `10.1038/s41551-026-01664-0`.

Key transferable idea:

> An ill-conditioned source inverse problem should be represented in the geometry of the physical source domain, rather than in arbitrary sensor/source indices.

They use participant-specific cortical geometric eigenmodes as an anatomical constraint. Our transfer is narrower and simpler:

- candidate IDs are not physical states;
- exact duplicate source coordinates are one physical source class;
- local source comparisons are defined on a geometry graph over the physical source support;
- a future optional extension may use graph/Laplacian source modes, but V3 first uses only the geometry quotient and local adjacency.

### 1.2 OSDR — temporal tissue dynamics from a spatial snapshot — Nature 2026

Somer, Mannor & Alon, *Temporal tissue dynamics from a spatial snapshot*, Nature 650, 490–499 (2026), DOI `10.1038/s41586-025-09876-1`.

Key transferable idea:

> Sparse observations can still carry dynamical information if the observation contains a marker with temporal meaning.

OSDR uses a division marker in one tissue snapshot to infer rates. We do **not** transfer its biological equations. We transfer the principle into a fixed within-stop sensor marker: one PMFS StopAndMeasure block contains multiple gas samples, so one spatial stop can provide a short dynamical waveform rather than one static hit/no-hit bit.

### 1.3 Host-aware intrinsic parameter identification — Nature Communications 2026

Picó et al., *Host-aware Identification of Intrinsic Gene Expression Biopart Parameters using Combinatorial Libraries*, Nature Communications (2026), DOI `10.1038/s41467-026-76332-7`.

Key transferable idea:

> Separate intrinsic object parameters from context/host-dependent effects by conditioning a mechanistic/digital-twin model on measured host state.

Mapping:

- intrinsic object = source coordinate `S`;
- host/context = wind, pose/action and map context `R`;
- unresolved host variation = latent transport realization `U`;
- observed response = gas/sensor block `Y`.

This motivates a host-aware residual bridge `Y = b(R) + delta(R,S) + noise`, rather than asking one model to explain both common context variation and source-specific variation in one undifferentiated score.

### 1.4 Systema — systematic variation can mimic perturbation-specific success — Nature Biotechnology issue 2026

Viñas Torné et al., *Systema: a framework for evaluating genetic perturbation response prediction beyond systematic variation*, Nature Biotechnology 44, 1050–1059 (2026 issue), DOI `10.1038/s41587-025-02777-8`.

Key transferable idea:

> High global predictive scores can be dominated by systematic/common variation and must be tested on perturbation-specific discrimination.

Mapping:

- systematic variation = common wind/transport/model shift shared across source candidates;
- perturbation-specific effect = source-specific candidate contrast;
- our primary offline endpoint remains true-vs-hard-negative source margin, never full-field similarity alone.

### 1.5 TxPert — split-half reproducibility as an empirical information ceiling — Nature Biotechnology 2026

Wenkel et al., *TxPert: using multiple knowledge graphs for prediction of transcriptomic perturbation effects*, Nature Biotechnology (2026), DOI `10.1038/s41587-026-03113-4`.

Key transferable idea:

> Compare learned effects with split-half experimental reproducibility and use context-matched controls; do not interpret one noisy realization as stable biology.

Transfer:

- accepted source evidence is divided into even/odd block folds;
- a source-vs-rival ordering must have the same sign in both folds before release;
- this adds no temperature or learned confidence threshold.

### 1.6 Field-level inference in weak lensing — astronomy 2026

Omori et al., *Towards Practical Field-Level Inference for Weak Lensing*, arXiv:2606.12255 (2026).

Key transferable idea:

> Compare observations to forward-modelled fields at the level actually observed, and verify calibration/coverage; summary information outside the observed field must not be counted as evidence.

Transfer:

- introduce an observation operator `H_t` that restricts M1 predictions to the robot's actual measured space-time support;
- full 626-cell source structure remains a model-side premise only;
- current localization evidence is computed from `H_t phi`, not from unvisited cells.

### 1.7 Physics-informed digital twins from limited patient data — medicine 2026

Briggs et al., *Towards a physics informed digital twin to predict cerebral blood flow and cerebral vascular regulation*, npj Digital Medicine (2026), DOI `10.1038/s41746-026-02600-x`; and 2026 digital-twin work in Nature Biomedical Engineering emphasizes initialization from early measurements and updating as new measurements arrive.

Transfer:

> The source model is allowed to start coarse and become more personalized/resolved as data arrive. Lack of early information should produce coarse uncertainty, not false point precision.

---

## 2. Variables and causal boundary

At completed measurement block `e`:

- `S`: queried physical source coordinate/class.
- `U_e`: unresolved plume/transport realization.
- `R_e`: **source-independent pre/current context only**: measured wind, pose, map geometry, action/previous motion known before the block outcome.
- `Z_e(S)`: source-dependent M1 physical proxy restricted to the current observation support.
- `Y_e`: current block gas/sensor response marker.

Important V3 correction:

**Do not put gas encounter count, inter-hit gap, current/past concentration, or sensor transient state into `R` when making a proximal-causal claim.** Those variables are downstream of the physical source through plume exposure. They may be used in a non-causal comparator, but not in the primary proximal `R` contract.

Conceptual graph:

`S -> transport/plume U_e -> Y_e`

`R_e -> transport/plume U_e -> Y_e`

`(S,R_e,U_e) -> Z_e(S)` through the M1 physics proxy.

The bridge is an operational finite-dimensional proximal moment model; the project must not claim that this graph alone proves the full proximal identification theorem.

---

## 3. Physical source quotient: remove candidate-ID aliases before reasoning about localization

Candidate IDs are a discretization artifact. Define the base physical equivalence relation

`i ~0 j  iff  ||x_i - x_j|| <= eps_coord`,

with `eps_coord` fixed only for floating-point equality (current diagnostic uses 1e-7 decimal rounding, not an outcome-tuned spatial radius).

The physical source set is

`S0 = S_id / ~0`.

For a valid keyed transport bank, exact coordinate aliases must have identical member-wise forward fields. If not, provenance is invalid.

Empirical H02 correction:

- 166 candidate IDs -> 144 physical coordinates;
- most previously reported weak nearest-neighbour pairs were exact coordinate aliases;
- after coordinate quotient, 95.83% of nearest unique-coordinate pairs in the recovered H02 context satisfy exact `p<=0.01` at full 631-cell support; only one reciprocal 0.30 m pair is clearly weak (`p=0.2265625`).

Therefore duplicate IDs are a representation problem, not physical localization error.

---

## 4. Observation operator: only observed support can justify current localization precision

Let the full M1 member response be

`phi_{s,m}`.

Define a truth-free observation operator `H_e` from the actual measured trajectory/block history. Then

`z_{s,m,e} = H_e phi_{s,m}`.

`H_e` may select or summarize only:

- cells/locations actually queried by the robot;
- time bins causally available by event `e`;
- fixed local features derived from those observations.

It may not use future path positions or source truth.

This is the central V3 change:

`global V2: phi -> replicated rank`

becomes

`V3 resolution: H_e phi -> local replicated source resolution`.

---

## 5. Observation-conditioned replicated pair separation

Use the same V2 pair-difference nuisance scaling, but on `z = H_e phi`.

For feature `d`:

`v_d = mean_{s,m<n} (z[s,m,d]-z[s,n,d])^2 / 2`

`W_d = 1/sqrt(v_d + ridge)`.

For a local physical source pair `(i,j)`:

`d_{ij,m} = W ( z[i,m] - z[j,m] )`.

Define the cross-member replicated pair strength

`eta_ij = [sum_{m != n} <d_{ij,m}, d_{ij,n}>] / [M(M-1)]`.

Equivalent computational form:

`eta_ij = ( ||sum_m d_{ij,m}||^2 - sum_m ||d_{ij,m}||^2 ) / [M(M-1)]`.

This removes same-member self-squares exactly as V2 does.

For M=8, retain the exhaustive member sign-flip diagnostic (`128` unique patterns) and also add a threshold-free leave-one-member-out stability requirement:

`eta_ij^(-r) > 0  for every r in {1,...,M}`.

Operational resolved-edge rule for the V3 prototype:

`resolved(i,j) := eta_ij > 0  AND p_signflip <= 0.01  AND min_r eta_ij^(-r) > 0`.

The sign-flip value remains an operational screen requiring approximate sign symmetry; it is not described as a universal exact theorem.

---

## 6. Geometry graph and the observational quotient

Build a truth-free local adjacency graph `G=(V,E_geo)` on physical source classes.

Preferred runtime adjacency:

1. touching/adjacent PMFS quadtree source regions using map geometry;
2. Delaunay adjacency on unique source coordinates only as an offline/fallback representation.

Do not choose K by H02 outcome.

Define unresolved edges

`E_unres(e) = {(i,j) in E_geo : resolved_e(i,j) = false}`.

The connected components of `(V,E_unres)` define the **observation quotient**

`Q_e = S0 / ~e`.

Interpretation:

- one component = all source positions still observationally indistinguishable at current support;
- as observations accumulate, unresolved edges disappear and components split;
- the method obtains progressively finer spatial resolution without inventing information.

Useful logged diagnostics:

- `resolution_fraction = |Q_e| / |S0|`;
- maximum component size;
- maximum component spatial diameter;
- component containing the current posterior mode.

No fixed minimum resolution is required for evidence processing; insufficient resolution simply forces equal evidence within the unresolved component.

---

## 7. Optional local tangent Fisher diagnostic: source dimension is 2, not rank_k=3

For a physical source coordinate `x=(x,y)`, fit member-specific local response Jacobians from geometry neighbours:

`Delta z_{j,m} ~= J_{i,m} Delta x_j`.

Then form the cross-member tangent information matrix

`F_i = [sum_{m != n} J_{i,m}^T W^2 J_{i,n}] / [M(M-1)]`.

`F_i` is 2x2 because the physical source coordinate has two dimensions.

A local continuous inverse problem is well-conditioned when

`lambda_min(F_i) > 0`.

Relative local conditioning:

`gamma_xy(i) = sqrt( max(lambda_min,0) / max(lambda_max,eps) )`.

This is a diagnostic alternative to the arbitrary global third eigen-direction. It is not required for the first fast-track closed loop; pairwise quotient resolution is cheaper and directly tied to hard negatives.

---

## 8. OSDR-inspired block dynamical marker: make one spatial stop information-rich

PMFS already collects multiple gas measurements inside one StopAndMeasure block. Do not collapse that block to one static bit.

For a block of L gas samples `c_k` at fixed causal times `tau_k`, define

`u_k = log(1 + max(c_k,0))`.

Primary fixed four-dimensional outcome marker:

1. `y_mean = mean(u_k)`
2. `y_sd = std(u_k)`
3. `y_hit = mean( c_k > thresholdGas )`
4. `y_slope = sum((tau_k-tbar)(u_k-ubar)) / sum((tau_k-tbar)^2)`

Thus

`Y_e = [y_mean, y_sd, y_hit, y_slope]`.

This uses the OSDR principle that a snapshot containing a temporally meaningful marker can encode dynamics. It is not claimed that OSDR's biological rate equations transfer to gas transport.

Why this matters for sparse data:

- two physical stops provide two block-level events for the existing even/odd evidence architecture;
- each event carries amplitude, intermittency and within-block trend, not just one hit/no-hit value;
- no future sample is used.

---

## 9. Host-aware residual proximal bridge

Current direct bridge scoring risks spending capacity on source-independent context variation. V3 separates it explicitly.

Model:

`Y = b(R) + delta(R,S) + epsilon`.

`b(R)` is the host/context baseline. `delta(R,S)` is the source-specific residual response.

Training requirement:

- source-balanced synthetic intervention contexts;
- within one training context, `R` is byte-identical across source interventions;
- `b(R)` is fitted from the source-averaged outcome in that context, not from an arbitrary source-biased row distribution.

Residual outcome:

`Y_delta = Y - b(R)`.

Proximal moment condition:

`E[ g(Z,S) * { Y_delta - h_delta(R,S) } ] = 0`.

At runtime:

`Y_delta_obs = Y_obs - b(R_obs)`

and candidate score is based on

`|| Y_delta_obs - h_delta(R_obs,S_candidate) ||`.

This is the direct mathematical transfer of the 2026 host-aware intrinsic/context decomposition and Systema's warning about systematic common variation.

The existing V15 sieve-GMM architecture remains the base implementation: `Z` is used only in the moment equation and is not an input to `h_delta` at runtime.

---

## 10. Absolute observation adequacy: stop 'all models are wrong but one is least wrong'

Even a correctly ranked bridge can fail if every candidate is outside the model's predictive support.

Define a development-calibrated nonconformity score

`a_e(s) = || Y_delta_e - h_delta(R_e,s) ||_{Sigma_Y^{-1}}^2`.

Use a frozen calibration set of true synthetic/held-out rows to obtain a split-conformal reference distribution `{a_cal}`.

Candidate adequacy p-value:

`p_adeq(s) = [1 + #{a_cal >= a_e(s)}] / [n_cal + 1]`.

Event-level adequacy:

`ADEQUATE_e := max_s p_adeq(s) > 0.10`.

If false, the event is exact ABSTAIN regardless of candidate ranking.

This is the protection against a shared model bias that all eight transport members reproduce consistently.

No H02 outcome is used to choose 0.10; it is pre-registered as a model-support safety level before hard-28 evaluation.

---

## 11. Quotient-aware source evidence

Suppose bridge candidate score `r_e(s)` is higher when candidate `s` better matches the observed block.

For each observational component `C in Q_e`, collapse the event score within the unresolved component before rank normalization:

`rQ_e(s) = sum_{j in C(s)} w_j r_e(j)`

with fixed-prior weights

`w_j = q0(j) / sum_{k in C(s)} q0(k)`.

Every candidate in the same unresolved component receives the same event score.

Meaning:

> the event may move probability between resolved source regions but cannot create false precision inside a region that its own observations cannot resolve.

Later events may split that region and add finer evidence.

---

## 12. Split-half reproducibility release

Retain the scale-free V11-style normal-mid-rank architecture.

Accepted, adequate, quotient-collapsed event scores are converted to normal ranks and assigned alternately to even/odd folds.

Let fold aggregates be `z_E(s)` and `z_O(s)`.

Let `B` be the tied best physical source class/component under the combined score, and let `rival` be the best candidate/class outside `B`.

Release only when the source-vs-rival direction agrees in both folds:

`mean_{s in B} z_E(s) > z_E(rival)`

AND

`mean_{s in B} z_O(s) > z_O(rival)`.

This is threshold-free sign consistency. If it fails, retain evidence but do not release a posterior change yet.

This directly imports the 2026 split-half reproducibility principle into source evidence.

---

## 13. Reversible posterior remains the outer update

For released evidence:

`g(s) = [z_E(s)+z_O(s)]/sqrt(2)`

`q_t(s) proportional to q0(s) exp(g(s))`.

Important contracts remain:

- fixed prior `q0`;
- rejected/inadequate events never enter the reservoir;
- no temperature;
- no blend weight;
- ties use mid-ranks;
- recomputation is reversible from retained evidence.

---

## 14. What to do if information remains sparse

Do **not** immediately tune a weaker gate.

Primary behavior:

- keep the source posterior coarse through the observation quotient;
- continue the unchanged PMFS planner;
- accumulate additional block markers.

Only if full closed-loop evidence shows that the quotient remains too coarse for too long should a separately versioned active-acquisition module be considered.

A possible future objective is expected resolution gain / information gain:

`a* = argmax_a E[ log |Q_{e+1}(a)| - log |Q_e| ]`

or a local tangent-information objective based on `lambda_min(F)`. This planner modification is **HOLD**, not part of the first V3 fast-track test.

---

## 15. Code alignment

### Frozen / retained

- `experiments/cg_pc_ctt/completeness_gate.py` — V2 model-side premise only.
- `closed_loop/cg_pc_ctt/reversible_rank_posterior.py` — base outer architecture.
- V15 sieve-GMM bridge form `E[g(Z,S)(Y-h(R,S))]=0`.

### V3 prototype additions

- `experiments/cg_pc_ctt/observation_quotient_gate.py`
  - exact coordinate quotient;
  - geometry-local pair edges;
  - observation-conditioned cross-member pair statistic;
  - leave-one-member-out stability;
  - unresolved connected components.

- `experiments/cg_pc_ctt/sparse_observation_stress.py`
  - diagnostic only;
  - demonstrates sample-support vs source resolution without tuning the frozen V2 threshold.

### Required bridge-data contract before model fitting

Primary `R` must not contain gas-derived source-downstream features.

Required metadata arrays:

- `r_feature_name`
- `y_feature_name`
- `z_feature_name`

Any primary proximal dataset containing `gas`, `hit`, `concentration`, `encounter`, `sensor_state` in `R` is rejected unless the variable is demonstrably source-independent (normally it is not).

---

## 16. Pre-registered falsification tests before any V3 claim

1. **Sparse-support monotonicity**: reducing actual observation support must not create finer quotient resolution on average.
2. **Coordinate-alias invariance**: duplicating a candidate ID at the same `(x,y)` cannot change physical class posterior.
3. **Candidate-order invariance**.
4. **Member-order invariance**.
5. **Member-label destruction**: independent source shuffle by member must collapse pair resolution.
6. **Shared-bias adequacy**: a synthetic common model bias may leave pair replication strong but must fail absolute observation adequacy when observations leave model support.
7. **R causal audit**: no gas-derived source-downstream feature in primary `R`.
8. **Z destruction**: Z/source shuffle must erase proximal bridge gain.
9. **Time destruction**: block temporal reversal must damage any gain attributed to `y_slope`/dynamic marker.
10. **Split-half disagreement**: contradictory even/odd source orderings must withhold posterior release.
11. **Exact abstention**: inadequate/rejected events leave posterior unchanged and cannot re-enter later.

---

## 17. Fast-track decision logic

Do not delay the already prepared H02 -> full multi-seed path merely to complete every V3 research idea.

When exact H02 hard-28 + valid bridge panels arrive:

1. run frozen V2 hard-28 evaluation;
2. run physical-coordinate quotient/local-pair diagnostic;
3. audit bridge data against the V3 `R/Y/Z` causal contract;
4. run host-aware residual bridge if the structured source-balanced training contract is available; otherwise run the already frozen V15 bridge and label the host-aware version `CURRENTLY TESTING`;
5. run negative controls;
6. if the frozen fast-track bridge verdict passes, proceed directly to the pre-registered 3-House x 10-seed OFF/ON closed-loop matrix.

The observation-quotient mechanism should enter that first full sweep only if its runtime inputs can be materialized without changing the frozen planner or inventing H02-specific thresholds. Otherwise it remains a separately versioned diagnostic for the next iteration.
