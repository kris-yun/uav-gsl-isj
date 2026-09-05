# CSTAR: causal source–transport active resolution for bank-free robotic GSL

Date: 2026-09-06
Base commit: `2387668ec6345d273a8d630af069d65af710850f`
Branch: `g3-cstar-causal-redesign-20260906`
Status: THEORY/REFERENCE FREEZE — no House experiment authorized by this document.

## 0. Scientific identity

The paper-level main innovation remains causal. The new method is **CSTAR (Causal Source–Transport Active Resolution)** and implements one closed causal experiment:

`fixed source S -> stochastic transport C -> sensor memory M -> observation Y -> causal source belief pi -> do(route) -> future observation -> belief update`.

CSTAR is not a renamed Bayesian marginalization, not a scene-specific predictive bank, and not a collection of three unrelated heuristics. Its three modules have different scientific responsibilities and different distant-field mother principles:

1. **M1 PICR — Perturbation-Invariant Causal Representation**. Mother field: single-cell perturbation biology / functional genomics. Infer source identity while separating transport, amplitude and sensor-context effects.
2. **M2 CPO — Committor Predictive Operator**. Mother field: chemical physics / rare-event and transition-path theory. Predict the action-conditioned first-passage/encounter law, with the verified physical solver as a prior rather than predicting only an average concentration.
3. **M3 PHS — Prospective Hypothesis Sweeps**. Mother field: systems neuroscience of hippocampal prospective sweeps and human information symmetry. Evaluate complete feasible future route sweeps and choose the route whose predicted observations best separate the currently competing source hypotheses.

The main causal thesis is therefore stronger than “use a causal network”: **source identity must be invariant to nuisance interventions, future observations must be predicted under an explicit action intervention, and the robot must choose the intervention that resolves causal alternatives.**

## 1. Causal variables and timing

Variables:

- `S`: stationary source location/region (target latent cause).
- `A`: source-strength/release-amplitude nuisance.
- `U_t`: transport/wind state and unresolved dispersion nuisance.
- `G`: geometry/occupancy at navigation height.
- `C_t`: latent concentration/transport state.
- `M_t`: sensor memory state.
- `X_t`: executed robot pose.
- `Y_t`: measured gas observation.
- `R_1:t`: executed route/history; this is an intervention history, not a random covariate selected independently of the algorithm.
- `tau`: candidate future route intervention.

Structural order:

`(S,A,U_1:t,G) -> C_t -> M_t -> Y_t`

`do(R_1:t) -> X_1:t -> which local U_t and Y_t are observed`

`(Y_1:t,U_1:t,X_1:t,G,M_t) -> M1 -> pi_t(S)`

`(S,G,U_1:t,X_t,M_t,do(tau)) -> M2 -> P_tau(O_future | S)`

`(pi_t, {P_tau(.|S)}, feasible routes) -> M3 -> do(tau*)`.

No module may read source truth, future wind, future gas, House ID, simulator member ID, or a site-specific predictive bank at deployment.

## 2. M1 PICR — Perturbation-Invariant Causal Representation

### 2.1 Distant-field mother principle

Single-cell perturbation biology increasingly separates an intrinsic cellular state from the effect of a controlled intervention and from microenvironmental effects. 2026 examples include:

- Guo et al., *Modelling drug-induced cellular perturbation responses with a biologically informed dual-branch transformer*, Nature Machine Intelligence 8, 96–112 (2026), DOI `10.1038/s42256-025-01165-w`. XPert separately encodes pre/post-perturbation states and models dose–time response.
- Driessen et al., *Conditional Monge Gap enables generalizable single-cell perturbation modelling*, Nature Machine Intelligence 8, 984–996 (2026), DOI `10.1038/s42256-026-01242-8`. A single conditional map models response across drug/dose/cell contexts and unseen conditions.
- Shen et al., *Spatial perturb-seq: single-cell functional genomics within intact tissue architecture*, Nature Communications 17, 3018 (2026), DOI `10.1038/s41467-026-69677-6`. Target-cell and microenvironment effects are measured separately in intact tissue.
- Nourreddine et al., *A genome-scale CRISPRi perturbation atlas of human induced pluripotent stem cells*, Nature Biotechnology (2026), DOI `10.1038/s41587-026-03199-w`. Perturbation phenotypes map causal regulatory structure at large scale.
- Dimitrov et al., *Interpretation, extrapolation and perturbation of single cells*, Nature Reviews Genetics 27, 349–370 (2026), DOI `10.1038/s41576-025-00920-4`, explicitly frames the shift from descriptive associations to causal/mechanistic perturbation modelling.

The transferred principle is not the biological architecture itself. Our second innovation is to treat **transport/source-strength/sensor changes as controlled nuisance interventions around a persistent physical source**, and to learn a source representation that is stable across those interventions.

Causal-representation theory used to make this scientifically testable rather than rhetorical:

- Kim et al., *On Causal Representation Learning with Internal Auxiliaries*, UAI 2026 / PMLR 337:3061–3082. Observable variables inside a mixing process can act as internal auxiliaries under explicit assumptions.
- Baumgartner et al., *Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention*, CLeaR 2026 / PMLR 323:119–165. Local state-dependent causal structure can be necessary for disentangling stable system parameters from trajectories.
- Li et al., *CARL: Preserving Causal Structure in Representation Learning*, ICLR 2026. Representation learning is explicitly constrained to avoid destroying causal conditional-independence/Markov-boundary structure.

### 2.2 What changes relative to the current code

The current `CPIR.cpp::applyCPIRPosterior()` reduces observations to a per-cell historical maximum, normalizes away amplitude, compares this shape with a Gaussian plume using SSE and exponentiates `-100*SSE/N`. PICR removes this as the scientific M1 path. It also removes the current MAP-chase heuristic as the definition of M1.

PICR consumes **all causally stamped 0.2 s frames**, including motion, instead of only accumulated cell peaks. The already-audited timestamp/pose/wind/sensor-history logic is infrastructure and is retained.

### 2.3 Runtime input

`PICRInput_t`:

- all executed frames through time `t`: `(stamp, pose_xy, gas_ppm, local_wind_uv)`;
- navigation-height geometry `G`;
- current audited FOPDT/sensor memory state;
- arbitrary free candidate source cells/regions in the current map;
- no source truth, future data, House label or predictive bank.

Wind, pose, geometry and sensor state are **internal causal auxiliaries** explaining how the latent source is mixed into the observed gas history. They are not appended as generic features and then ignored.

### 2.4 Representation and candidate scoring

Use two causal branches plus a candidate scorer:

1. `response branch E_y`: gas/sensor temporal response tokens;
2. `context branch E_c`: local wind, executed pose, geometry descriptors and time;
3. `candidate scorer H_s`: cross-conditions the encoded history on a candidate source location/region and outputs a log compatibility.

Only past-to-present attention is legal. Sparse/local attention is encouraged where a source–observation pair has plausible transport support; the exact support rule must be frozen and falsified rather than tuned on localization outcomes.

The encoder returns a source-stable subspace `zS`, a nuisance subspace `zN`, and an amplitude/release head `aHat`. Candidate scores are normalized over the current map:

`pi_t(s) = softmax_s( score_theta(zS, candidate=s, geometry=G) )`.

Because the scorer evaluates arbitrary coordinates/regions, it is not a fixed House classifier.

### 2.5 Causal training objects

Existing simulations/banks may be used **offline as intervention data**, never as runtime lookup.

Construct paired intervention episodes:

- same `S`, different transport/wind realization;
- same `S`, different source strength/release realization;
- same `S`, different sensor-memory initialization/parameters where physically licensed;
- matched nuisance/context, different `S`;
- cross-House and geometry perturbations.

The load-bearing constraints are:

`zS(S, do(N=n1)) ≈ zS(S, do(N=n2))` for nuisance interventions,

while `zS(S1, N)` and `zS(S2, N)` remain separable for source intervention `S1 != S2`.

Use a constrained objective rather than closed-loop coefficient tuning:

- source proper scoring loss / candidate contrast as the primary objective;
- intervention invariance constraint on `zS`;
- conditional nuisance leakage test (transport/amplitude/sensor labels must not be recoverable from `zS` beyond the predeclared tolerance after conditioning on `S`);
- reconstruction/prediction through `zN` and `aHat` so invariance cannot be achieved by collapsing all information.

Lagrange multipliers for constraints may be optimized as dual variables; they are not House-specific planner weights.

### 2.6 Runtime output

`PICROutput_t`:

- `source_posterior[candidate]`;
- `source_representation` and per-candidate compatibility diagnostics;
- nuisance/amplitude state needed for audit/model checking, not for secretly changing the source truth;
- `valid/abstain` with explicit reason when the causal support/history is insufficient.

### 2.7 M1 falsification gate

Before any new closed loop, PICR must pass all of:

1. fixed-trajectory source log score / localization error better than the current peak-SSE M1 and a matched ordinary temporal encoder;
2. same-source transport intervention changes `zS` substantially less than the unconstrained encoder;
3. different-source matched-context separation does not collapse;
4. source-strength intervention does not move the source representation enough to reproduce the historical RMFE fixed-amplitude failure;
5. source-label permutation destroys the gain;
6. House ID is absent and leave-one-House-out performance remains directionally valid;
7. removing the intervention-pair constraint removes a measurable part of the source gain.

If only task accuracy improves but the causal intervention tests fail, M1 is not accepted as a causal contribution.

## 3. M2 CPO — Committor Predictive Operator

### 3.1 Distant-field mother principle

Chemical physics and transition-path theory do not summarize a rare transition only by its mean state. They use the **committor**: the probability that the dynamics reach a target event before returning/escaping. Relevant 2026 work:

- Breebaart et al., *Understanding Mechanisms of Molecular Rare Events from Start to Finish*, Physical Review Letters 136, 168001 (2026), DOI `10.1103/lk32-njx7`. It calls the committor the ideal reaction coordinate and reconstructs it through iterative path ensembles.
- Contreras Arredondo et al., *Learning the committor without collective variables*, Nature Computational Science 6, 350–357 (2026), DOI `10.1038/s43588-026-00958-2`. A graph model predicts committor directly from complex configurations without hand-crafted reaction coordinates.

For bank-free geometric generalization and model–reality correction, CPO additionally borrows two 2026 scientific-ML principles:

- Long et al., *Deep neural operator for free boundary problems*, Nature Machine Intelligence 8, 806–817 (2026), DOI `10.1038/s42256-026-01233-9`: operator learning across changing domains through explicit geometry structure.
- Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*, Nature Communications 17, 7877 (2026), DOI `10.1038/s41467-026-74002-2`: retain a trusted executable physics prior and learn structured discrepancy rather than replacing the prior wholesale.

### 3.2 Why committor belongs in M2, not M1

Historical first-passage/temporal features were unstable when reused directly as source evidence. CSTAR does not revive that failure. M2 predicts **future encounter events under `do(route)`**; only M1 produces the current source posterior.

For gas threshold `gamma` fixed by the sensor/event contract, define first-passage time along a future route:

`T_gamma = min{j >= 1 : Y_{t+j} > gamma}`.

For each candidate source `s` and route `tau`, CPO predicts the categorical law

`P_s^tau(T_gamma=1), ..., P_s^tau(T_gamma=H), P_s^tau(T_gamma>H)`.

Equivalently, with conditional hazard `h_j`:

`P(T=j) = h_j prod_{r<j}(1-h_r)`

`P(T>H) = prod_{r<=H}(1-h_r)`

and finite-horizon committor

`q_h = P(T<=h) = 1 - prod_{r<=h}(1-h_r)`.

CPO also outputs conditional log-ppm location/scale (or predeclared intensity-bin probabilities) after encounter, so the provider can later support richer marked observations without changing M3’s API.

### 3.3 Runtime input

`CPOInput(s,tau)`:

- one source hypothesis/region `s`;
- geometry `G`;
- current/recent causally available local wind/context;
- current transport summary and audited FOPDT sensor state;
- a physically feasible future route `tau = (x_{t+1},...,x_{t+H})` sampled at the same causal cadence;
- no source truth, future wind/gas or House-specific bank.

### 3.4 Physics-seeded operator

Retain `CTPIOnlineCoreV2::Transport` and `Fopdt` as the executable prior. The prior generates candidate-conditioned concentration/sensor trajectories from causally available wind prediction. A learned geometry/context-conditioned correction models only the discrepancy needed for the encounter law.

Conceptually:

`eta_j = eta_phys,j + Delta_theta(G, wind_history, route, source, prior_state)`

`h_j = sigmoid(eta_j)`.

The learned correction is trained once across heterogeneous source/transport/geometry interventions. At deployment there is no per-site GADEN bank or source-truth calibration.

### 3.5 Runtime output

`CPORouteLaw`:

- `first_hit_prob[H+1]` including no-hit-by-H;
- `committor[H]`;
- `logppm_mean[H]`, `logppm_scale[H]` or a frozen marked-observation discretization;
- calibration/validity diagnostics.

The first-hit vector is normalized and is the primary M3 planning distribution.

### 3.6 M2 falsification gate

On held-out transport realizations and leave-one-House-out geometry:

1. first-passage NLL/Brier score and committor calibration must beat the current plume provider and the uncorrected physics prior;
2. future log-ppm CRPS/NLL must not degrade catastrophically;
3. rare encounter/non-encounter tails must be reported separately, not hidden by average RMSE;
4. route shuffle and source permutation must destroy the expected predictive structure;
5. no held-out-House bank may be queried at runtime;
6. the learned correction must remain useful under source-strength and wind perturbations.

If the learned CPO does not beat a simple causal baseline, it does not proceed to closed loop.

## 4. M3 PHS — Prospective Hypothesis Sweeps

### 4.1 Distant-field mother principle

Systems neuroscience in 2026 provides two transferable natural-science objects:

- Tang et al., *Goal-directed hippocampal theta sweeps during memory-guided navigation*, Nature Neuroscience 29, 2214–2224 (2026), DOI `10.1038/s41593-026-02364-3`: learning-dependent hippocampal sequences sweep ahead and predict upcoming goal-directed trajectories.
- Yu et al., *Hippocampal theta sweeps indicate goal direction during navigation*, Nature Neuroscience 29, 2225–2236 (2026), DOI `10.1038/s41593-026-02365-2`: theta sweeps form vectors toward remembered goals and stronger goal modulation precedes correct choices.
- D’Ambrogio et al., *Interpretable abstractions of artificial neural networks predict behavior and neural activity during human information gathering*, Nature Neuroscience 29, 2036–2047 (2026), DOI `10.1038/s41593-026-02342-9`: information gathering depends strongly on **relative evidence across alternatives / information symmetry**, rather than independent absolute uncertainty of each option.

CSTAR does not copy a neural circuit. It transfers two principles: **prospectively sweep complete candidate future trajectories**, and value information by how well it resolves competing alternatives relative to one another.

### 4.2 Replace the current M3 objective

Current `CTPI.cpp::evaluateCTPIActionInformation()` collapses each region source to its centroid, uses a one-step Gaussian-plume binary hit model, then multiplies mutual information by `(1 + 20 * posteriorMass)`. PHS removes all three scientific shortcuts.

A source region is marginalized over a deterministic frozen placement quadrature; it is never silently replaced by its 2x2 center.

Each current feasible endpoint produces a **route sweep**: the navigation path from the current pose to the endpoint, sampled at 0.2 s, then dwell as needed so every candidate has the same fixed future observation horizon. PICR is explicitly allowed to consume the stamped observations during motion, so predicted path observations are not decorative.

### 4.3 Symmetric causal-resolution objective

For source `s` and candidate route `tau`, M2 returns categorical future law `P_s^tau(k)` over first-hit time/no-hit. For two source hypotheses `i,j`, define the Bhattacharyya coefficient

`BC_ij(tau) = sum_k sqrt(P_i^tau(k) P_j^tau(k))`.

`BC=1` means the two sources make identical predictions on this route; `BC=0` means their predicted first-passage outcomes are disjoint.

Use current M1 posterior `pi`. Define pairwise posterior confusion

`B_t(tau) = sum_{i<j} sqrt(pi_i pi_j) BC_ij(tau)`.

Normalize by `Z_t = sum_{i<j} sqrt(pi_i pi_j)` and report

`Resolution(tau) = 1 - B_t(tau)/Z_t` when `Z_t>0`.

Select the feasible route with maximum `Resolution`. Route length is **not** added with a fitted lambda. Feasibility and a fixed common horizon provide the cost constraint; shorter travel is only a deterministic tie-break.

This objective is our mathematical adaptation of information symmetry: it explicitly attacks ambiguity among the posterior alternatives that are currently competing. It is also connected to classical Bhattacharyya pairwise bounds on Bayesian classification confusion, rather than to an arbitrary explore/exploit weight.

### 4.4 Runtime input/output

`PHSInput`:

- `PICROutput.source_posterior`;
- `CPORouteLaw[source][route]`;
- feasible route set from existing navigation/map checks;
- no truth, House ID or future observations.

`PHSOutput`:

- selected route/goal;
- resolution score;
- pairwise confusion diagnostics;
- deterministic tie-break metadata.

### 4.5 M3 falsification gate

With a fixed baseline predictive provider and held-out outcome realizations, compare native PMFS, MAP exploit, current one-step M3 and PHS. PHS must improve the preregistered temporal source-risk/error metric over the baseline provider before full CPO is substituted. Route/source-law shuffling must remove the gain. No planner weight sweep is permitted.

## 5. Full runtime chain and exact module boundaries

At every 0.2 s frame:

1. strict ingress binds gas, local wind and pose by timestamp;
2. V2 sensor state advances causally;
3. M1 PICR consumes the newly executed frame and produces/updates `pi_t(S)`;
4. when a decision is due, navigation generates feasible equal-horizon route sweeps;
5. M2 CPO predicts `CPORouteLaw` independently for every `(source hypothesis, route)` using only causal history and `do(route)`;
6. M3 PHS combines the M1 posterior with the M2 route laws and chooses `tau*`;
7. the robot executes `tau*`; its actual new frames return only to M1 on the next update.

M2 never writes source posterior. M3 never alters M1 or M2 parameters. M1 never sees a future route outcome before it happens.

## 6. Code alignment at commit 2387668

### Keep as infrastructure / physical prior

- `closed_loop/ctpi/ctpi_v2_ingress.py`: strict timestamped gas/wind/pose join.
- `ros2_package/src/gsl_server/algorithms/PMFS/CTPIOnlineCoreV2.hpp`: conservative transport, FOPDT, predict-before-observe stream.
- `CTPIDualClockV2.hpp`: explicit native/sensor clocks.
- corrected wind observation and common navigation-height geometry adapters.
- `MovingStatePMFS.cpp`: feasible action/open-move construction, navigation checks and audit plumbing.

### Remove from new scientific path after offline gates pass

- `CPIR.cpp::applyCPIRPosterior()` peak-normalized plume SSE / `-100` score.
- M1 MAP-chase and posterior-guidance multipliers as the definition of the new M1 consumer.
- `CTPI.cpp::evaluateCTPIActionInformation()` carrier-centroid collapse, latest-wind plume, one-step binary MI and `20x` posterior multiplier.
- GMRF as a paper contribution. It may remain an optional wind provider only after it satisfies the same causal input contract as any baseline.

### New isolated components to implement first

- `experiments/ctpi_cstar/m1_picr/` — paired-intervention dataset builder, model, invariance/source-separation tests.
- `experiments/ctpi_cstar/m2_cpo/` — V2-physics wrapper, first-passage/committor learner, calibration and zero-shot tests.
- `experiments/ctpi_cstar/m3_phs/` — route-law scorer and held-out prospective-sweep falsification.
- only after all gates: production adapters `CTPICausalSourceV3`, `CTPICommittorV3`, `CTPIProspectiveSweepV3` with explicit versioned mode.

## 7. Incremental-gain contract

No module is allowed to be decorative. Freeze the downstream sequence before outcomes:

- `A0`: unmodified Classic PMFS.
- `F00`: PICR M1 + the native PMFS information planner. The native planner receives M1 source weights through a deterministic mapping; no MAP chase, no posterior-guidance coefficient and no M3.
- `F10`: PICR M1 + PHS M3 + a frozen **baseline** route-law provider (not the learned CPO). This isolates whether the new prospective/symmetric planner adds value.
- `F11`: PICR M1 + full CPO M2 + the identical PHS M3. This isolates the incremental value of the learned rare-event predictive operator.

Required interpretations:

- M1 downstream increment = `F00 - A0`.
- M3 downstream increment = `F10 - F00`.
- M2 downstream increment = `F11 - F10`.
- full method = `F11 - A0`.

Primary closed-loop metric remains preregistered 240 s localization error AUC unless a new protocol is frozen before any outcome. Full deployable method target remains >=10% relative improvement over Classic PMFS with no systematic House-level catastrophic reversal. Each increment must be directionally beneficial; a strong M1 is not allowed to carry decorative M2/M3.

Before these closed-loop arms, each module must first pass its own fixed-trajectory / held-out scientific gate.

## 8. Baseline provider for the M3-only F10 arm

To isolate M3, F10 must not silently receive full learned M2. Use a versioned analytic route-law provider built from the current causal plume/FOPDT baseline, with all constants frozen before M3 outcomes. It must expose the same `CPORouteLaw` schema so M3 code is identical in F10 and F11. F11 changes only the provider.

## 9. Novelty boundary / collision risk

The 2026 `npj Robotics` review *Advanced electronic noses for future robotic olfaction* (DOI `10.1038/s44182-025-00071-y`) surveys gradient/anemotaxis/probabilistic GSL and highlights turbulence/wind challenges, but does not establish the CSTAR three-part causal-intervention paradigm.

Do not claim “first bio-inspired planner”: 2026 robotic olfaction already includes insect- and bumblebee-inspired strategies. PHS novelty is specifically the transfer of prospective trajectory sweeps + relative hypothesis resolution into an action-conditioned source-confusion objective.

Do not claim “first neural operator for source localization” without a broader collision review: operator methods exist in other source-localization domains, and public 2026 work may also appear in gas/plume contexts. CPO novelty is the bank-free **source-conditioned committor/first-passage observation operator coupled to a verified causal sensor/transport prior**, not the generic use of an operator network.

Likewise, PICR novelty is not “using a Transformer”; it is the intervention-defined source representation and its required causal falsification under transport/amplitude/sensor changes.

## 10. Stop lines

- Do not launch new House experiments from this theory document.
- Do not alter the old negative bundles or call any new component PASS before its gate.
- Do not train on House ID/source truth features that are unavailable at deployment.
- Do not use the held-out House predictive bank at runtime.
- Do not tune planner weights because PHS has no free explore/exploit coefficient.
- Do not modify production `CPIR.cpp`/`CTPI.cpp` until reference math and offline falsification pass.
