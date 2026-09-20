# M1-Only Screening Loop — 2026-09-20

Branch: research/remote-paradigm-loop-20260919
Status: M1 ONLY / OFFLINE FALSIFICATION / M2-M3 FROZEN

## Goal

Confirm one paper-defining M1 before discussing auxiliary innovations.

M1 must:
- be a 2025/2026 top-venue paradigm-level idea from a remote field;
- change how source evidence is represented/inferred, not merely add a planner or loss;
- preserve a PMFS-compatible source-location probability map;
- survive direct GSL collision search;
- be supported by at least two independent existing project evidence families;
- remain lightweight enough for multi-dataset validation.

## Literature survivors

### A. Predictive self-supervised physical representation
Primary anchor:
- ICLR 2026 — Qu et al., *Representation Learning for Spatiotemporal Physical Systems*.
  JEPA-style latent prediction consistently beats pixel-level masked autoencoding for estimation of governing physical parameters on active matter, shear flow and Rayleigh-Bénard convection.
Supporting anchors:
- ICLR 2025 — DynCL, *Self-supervised contrastive learning performs non-linear system identification*.
- ICLR 2025 — physics-informed SSL for energy landscapes.
- NeurIPS 2025 — self-supervised representations robust to sensor failures.

Potential GSL thesis:
> treat source location as a governing physical parameter of a stochastic plume and learn a predictive latent representation from unlabeled plume histories before decoding a source-probability map.

Collision boundary:
- generic self-supervised source localization is not new: underwater acoustic source localization used CPC in 2021/2022.
- generic OSL representation learning is not new: 2026 OSL work uses unsupervised manifold learning for diffusion-state classification.
- direct 2025/2026 gas/odor source-localization work using JEPA-style latent prediction for source-map inference was not found in the current search.
- therefore novelty, if any, must be specifically physical-parameter-oriented predictive latent learning for turbulent plume histories, not “use SSL/CPC”.

Status: SURVIVES LITERATURE, NEEDS STRONGER DATA SUPPORT.

### B. Self-supervised nonlinear system identification
Primary anchor:
- ICLR 2025 — DynCL.
  Provides identifiability results showing contrastive time-series learning can recover latent variables and latent dynamics under stated conditions.

Potential GSL thesis:
> infer source from identified latent plume dynamics rather than from raw concentrations.

Project proxy:
- source-blind AR/system-identification coefficients were fitted to existing H01/H02/H03 source×wind histories.
- H02 becomes source-identifying only after enough exposure; H03 is source-stable at 120–180 s.
- however H01 at 180–240 s and H03 at 240 s show transport variation comparable to or larger than source separation, reducing held-wind identity to 1/2.

Decision:
- low-order source-conditioned dynamics are not reliably stable across wind.
- explicit “identify the plume dynamics and source follows” is too brittle as the paper M1.

Status: REJECTED AS PRIMARY M1.

### C. Contextual / in-context dynamics adaptation
Top-venue anchors:
- ICLR 2025 — *Neural Context Flows for Meta-Learning of Dynamical Systems*.
- ICML 2025 — *DISCO: learning to DISCover an evolution Operator for multi-physics-agnostic prediction*.
- ICML 2025 — *Zebra: In-Context Generative Pretraining for Solving Parametric PDEs*.

Potential thesis:
> infer a short-trajectory transport context/operator online, then localize the source conditionally.

Project proxy:
- adding explicit local wind context to a source-blind predictive proxy did not improve transport/source separation consistently and often made it worse.
- earlier project audits also show candidate-dependent transport errors cannot be removed by one shared nuisance/context correction.

Decision:
- context adaptation may remain an implementation tool, but current evidence does not support it as the main scientific contribution.

Status: DEMOTED.

### D. Invariant-function / causal-mechanism discovery
Primary anchor:
- ICML 2025 — *Discovering Physics Laws of Dynamical Systems via Invariant Function Learning*.

Decision:
- theoretically strong but collides with the project’s already-failed causal/invariance line.
- existing evidence shows source-vs-transport structure is not uniformly invariant, especially before sufficient exposure.

Status: REJECTED AS M1.

### E. Temporal point-process / event-stream modeling
Top-venue anchors:
- ICML 2025 — *Residual TPP: A Unified Lightweight Approach for Event Stream Data Analysis*.
- ICML 2025 — *Evolving Minds: Logic-Informed Inference from Temporal Action Patterns*.

Positive project evidence:
- native 0.2-s first-passage timing is strongly source-informative;
- survival/count-only and coarse 8-block HIT representations lose information;
- time permutation and phase-label shuffle materially degrade native source ranking.

Risk:
- odor plume literature already uses whiff/blank timing and first-arrival concepts;
- prior CTT work in this project already built candidate-conditioned first-passage likelihoods and failed to obtain a robust trainable surrogate.
- this would likely resurrect a previously exhausted line rather than create a new paper-level M1.

Status: REJECTED / COLLIDES WITH PROJECT HISTORY.

## Existing-data M1 discriminators

### D1. Native temporal-information premise
Frozen project result:
- native first-passage mean normalized rank 0.1417;
- survival-only 0.2564;
- time-permute 0.1573;
- phase-label shuffle 0.3040;
- extremely significant pairwise wins for full first passage.

Interpretation:
- high-resolution temporal structure is genuinely load-bearing;
- a viable M1 should use temporal structure, not coarse count/HIT summaries.

### D2. Naive predictive compression test
A causal smoothing / next-window predictive proxy was tested on the existing 12 controlled histories.

Positive:
- after support appears, predictive components often reduce wind/source separation in H02/H03 and sometimes H01.

Negative:
- simple prediction can suppress rare source-defining events and reduce H01 held-wind identity.

Interpretation:
- “predict everything common” is not enough;
- but this does not falsify JEPA-style representation learning, because ICLR 2026’s claim is latent physical-parameter retention, not low-pass forecasting.

### D3. Linear future-prediction proxy
A stronger source-blind ridge future predictor was trained on fast-wind windows and evaluated on slow wind.

Results:
- H01 10-s windows: held-wind source identity improved from 12/22 to 16/22.
- H02: no improvement.
- H03: predictive representation underperformed raw context on both 5-s and 10-s windows.

Interpretation:
- linear future prediction alone is insufficient and cannot justify M1.
- any M1 confirmation must rely on representation-learning evidence beyond a linear predictor.

### D4. Low-order system-identification proxy
AR coefficient representations were compared across source and wind.

Results:
- H02 240 s: same-source wind/source ratio ~0.49 with 2/2 held-wind identity.
- H03 120–180 s: strong source identity, but 240 s falls to 1/2.
- H01 240 s: wind/source ratio >1.4–2.1 and only 1/2 identity.

Interpretation:
- source identity is not a stable low-order dynamical parameter in all Houses.
- this rejects DynCL/system-ID as the current M1.

## Current M1 decision

### Active candidate
**Physical-Parameter Predictive Representation Learning**

Paradigm:
- self-supervised predictive representation learning / JEPA-class latent prediction.

Paper-level scientific framing:
> A turbulent gas-source location is treated as a governing physical parameter that should be recoverable from a predictive latent representation of plume histories, rather than from direct discriminative mapping or reconstruction of stochastic plume realizations.

Why this is still alive:
1. latest direct top-venue physical-systems evidence (ICLR 2026) specifically shows latent predictive representations improve governing-parameter estimation in fluid-like spatiotemporal systems;
2. existing GSL evidence proves fine temporal structure contains source information and coarse representations destroy it;
3. generative inversion, causal invariance, low-order system identification, temporal first-passage modeling and simple context adaptation all have stronger direct collisions or project-specific negative evidence;
4. no direct gas/odor GSL JEPA-style source-map method was found in the current collision search.

Why it is NOT YET CONFIRMED:
- linear predictive proxies are mixed and sometimes worse than raw signals;
- therefore the core JEPA-specific premise still needs one trained, source-blind latent-prediction falsification on existing data.

## Required final M1 gate

Before promoting M1:
1. train a lightweight source-blind latent-prediction encoder on existing source×wind histories without source labels;
2. compare frozen embeddings against:
   - direct supervised/raw encoder;
   - masked reconstruction/autoencoding baseline;
   - temporal-order destruction;
   - target-time permutation;
3. evaluate source discrimination only after freezing the encoder;
4. use held wind/context for the decisive test;
5. require improvement or at minimum no degradation in H01/H02/H03 simultaneously;
6. if this fails, reject predictive representation M1 and restart the remote-paradigm search.

M2/M3 remain frozen until this gate is resolved.


## Loop 2 — predictive-representation M1 does not clear the data gate

A source-blind linear predictive-subspace proxy was added to directly compare latent future-predictive directions against PCA/reconstruction-style directions.

Protocol:
- 5 s and 10 s windows from 120–240 s;
- training uses fast-wind histories from both source interventions without source labels;
- predictive subspace = top eigen-directions of context→future cross-covariance;
- reconstruction baseline = top PCA directions of context covariance;
- frozen representations evaluated on slow wind by source-prototype separation.

Result:
- H01: predictive and PCA are essentially tied; only small differences.
- H02: predictive and PCA are essentially identical across 2/4/8 latent dimensions.
- H03: predictive gives only a marginal 5 s gain and is otherwise tied.
- no 3/3 House advantage over reconstruction/PCA appears.

Combined with the earlier ridge future-predictor results (mixed and sometimes worse than raw context), the present evidence does **not** support claiming that latent prediction itself is the unique load-bearing source-identification mechanism on current data.

Decision:
**Physical-Parameter Predictive Representation Learning = DEMOTED FROM ACTIVE M1.**
It remains a possible implementation component, not the paper-defining innovation.

## Loop 2 new M1 search — Extreme-Event-Aware Learning

### Primary 2026 remote-domain anchor

- Nature Communications 2026 — Kai Chang & Themistoklis P. Sapsis, *Extreme Event Aware (η-) Learning*.
  Core principle: rare/extreme regimes are underrepresented in finite data; ordinary learning fits quiescent/common regimes and remains uncertain or wrong in extremes. η-learning injects statistics of an observable that characterizes extremeness as a training constraint, with optimal-transport theory supporting the construction.

Independent recent support:
- Physical Review Fluids 2026 — data-driven latent-space modeling/control of extreme events in turbulent flows.
- ICML 2025 — extreme-value learning/optimization explicitly argues that expectation-based objectives can ignore rare but high-impact tail events.
- The modern turbulence literature continues to treat intermittent bursts as the scientifically distinct events that standard mean behavior fails to capture.

### Why this maps to the project

The current project repeatedly shows a rare-event structure:
- H01 source evidence can arrive only very late (~229 s in the controlled pair);
- H02 has no usable source signal at early horizons and becomes strongly identifiable only after plume exposure appears;
- native first-passage timing is strongly source-informative, while coarse HIT compression removes much of that information;
- standard predictive compression can erase H01's late source-defining event;
- therefore mean/reconstruction/prediction objectives can emphasize the common zero/quiescent regime and underweight the rare observations that actually distinguish source hypotheses.

### GSL novelty collision boundary

Not novel:
- plume intermittency;
- whiff/blank statistics;
- intensity/timing features for odor localization.

Those are established, including eLife 2022 work showing both intensity and timing of turbulent odor bursts predict source location.

Potentially novel:
> import **extreme-event-aware learning as the training principle** for source-probability inference: preserve/regularize source-informative tail and intermittent-event statistics so the learned likelihood/map cannot optimize the dominant quiescent regime by washing out rare source evidence.

Current search did not find η-learning / extreme-event-aware statistical regularization applied to robotic gas/odor source localization.

### Existing-data fixed η-observable screen

Using only the existing 12 factorial histories, a source-blind fixed feature split was evaluated.

Bulk features:
- mean, standard deviation and central quartiles of log concentration.

Extreme/intermittency observables:
- q95, q99, maximum and top-1% mean;
- fixed-threshold exceedance fractions;
- first arrival at the pre-existing 0.1 ppm floor;
- whiff/blank duration and burst-count statistics.

Held-wind source identity:

H01:
- 180 s: bulk 1/2; η 1/2; bulk+η 2/2.
- 240 s: bulk 1/2; η 2/2; bulk+η 2/2.
- wind/cross-source distance ratio at 240 s: bulk 0.568; η 0.159.

H02:
- 60 s: all zero — no method fabricates source information.
- 120 s: all unresolved — source and transport remain tied.
- 180 s: bulk 2/2, η 2/2; ratio 0.382 vs 0.037.
- 240 s: bulk 2/2, η 2/2; ratio 0.649 vs 0.146.

H03:
- 120 s: bulk 1/2; η 2/2; ratio 0.451 vs 0.210.
- 180 s: both 2/2; η ratio 0.179 vs bulk 0.294.
- 240 s: bulk 2/2; η 1/2; combined bulk+η restores 2/2.

Interpretation:
- extreme/intermittency observables are markedly more transport-stable than bulk statistics in the key H01/H02 late-support cases and H03 120–180 s;
- η-only is not universally sufficient (H03 240 s), so the scientific claim must be “do not let learning ignore the rare-event channel”, not “only extremes matter”;
- zero-support cases remain zero, satisfying the physical-support constraint.

### Amplitude-tail vs temporal-extreme split

The η vector was split without tuning:

Amplitude-tail branch:
- upper quantiles, maximum/top-tail mean, threshold occupancy.

Temporal-extreme branch:
- first arrival, whiff/blank durations, burst count.

Result:
- H01 240 s: both branches identify 2/2 sources; temporal ratio 0.153, amplitude ratio 0.164.
- H02 180–240 s: both branches identify 2/2; amplitude branch is especially stable.
- H03 120–180 s: both branches identify 2/2.
- H03 240 s: amplitude branch falls to 1/2 while temporal branch retains 2/2.

Thus no single hand-engineered extreme statistic explains all Houses. Tail amplitude and event timing carry complementary source evidence — exactly the condition under which an η-learning objective over a vector observable is scientifically more appropriate than a fixed feature heuristic.

## Current M1 ranking after Loop 2

1. **Extreme-Event-Aware Source Learning / η-GSL** — ACTIVE PRIMARY CANDIDATE.
2. Predictive self-supervised physical representation — DEMOTED; possible implementation.
3. Self-supervised nonlinear system identification — REJECTED.
4. Context/meta dynamics — DEMOTED.
5. Temporal point-process / first-passage — REJECTED as primary due project-history collision.
6. Causal/invariant-function discovery — REJECTED as primary.

## Final confirmation still required for η-GSL

M1 is not yet frozen. Before promotion, require:

1. a minimal η-regularized source estimator on existing data, not just hand-crafted η features;
2. compare against the same estimator without η regularization;
3. require no worse source ranking in H01/H02/H03 and a clear gain in at least the known rare-event failure cases;
4. time/order destructive controls must show that the gain is not just concentration amplitude reweighting;
5. direct 2025/2026 GSL collision search for EVT, tail-risk, rare-event regularization and extreme-aware learning;
6. confirm the method can be defined on VGR/GADEN, DNS turbulent plume data and real wind-tunnel trajectories.

M2/M3 remain frozen.


## Loop 3 — M1 challenger comparison: η-learning vs adaptive olfactory coding vs spectral dynamics

### Challenger F — Adaptive olfactory coding / sensory habituation

2026 remote-domain support is strong:
- Nature Communications 2026 — *Fast efficient coding and sensory adaptation in gain-adaptive recurrent networks*: fast gain adaptation dynamically reallocates sensory coding resources under changing stimulus priors.
- Nature Communications 2026 — *Intelligent artificial olfactory nervous system with sensory adaptation capabilities*: adaptive artificial receptor neurons filter background interference and improve gas identity recognition across environments.
- PRX Life 2026 — *Manifold Learning for Olfactory Habituation to Strongly Fluctuating Backgrounds*: in turbulent stochastic backgrounds, manifold habituation outperforms predictive filtering and mean-background subtraction.

However, the GSL novelty collision is severe:
- J. Neurosci. 2019 *Olfactory Navigation and the Receptor Nonlinearity* already derives an encoding strategy optimized specifically for source-location information and explicitly notes that rare high concentrations can deserve disproportionate coding resources.
- biological olfactory-navigation literature already treats adaptation/intermittency as navigation-relevant.
- 2026 npj Robotics directly transfers insect adaptive behavior to robotic odor-source localization, albeit at the behavior/policy layer.

Existing-data adaptation proxy:
- causal percentile/rank coding and divisive normalization were tested at fixed 25 s and 60 s adaptation windows.
- H01: rank coding modestly reduces same-source wind/source confusion.
- H02: rank coding destroys an otherwise clean 2/2 source identity at 180 and 240 s (drops to 1/2; ratio rises from ~0.08 to ~0.83–0.95).
- H03: adaptive coding is mixed and does not repair the early 120 s failure.
- simple exponential adaptation previously rescued some H03/H01 cases but worsened other conditions.

Decision:
**Adaptive olfactory coding = REJECTED AS PRIMARY M1.**
The paradigm is scientifically rich, but both direct olfactory-navigation precedent and the H02 destructive counterexample make it a poor paper-defining main innovation for this project.

### Challenger G — Koopman / latent transfer-operator dynamics

Latest remote-domain support:
- ICML 2025 — *ResKoopNet: Learning Koopman Representations for Complex Dynamics with Spectral Residuals*.
- UAI 2026 — *Deep Spectral Learning of Embedded Latent Transfer Operators for Stochastic Dynamical Systems*.
- Nature Communications 2026 — *Adversarial dynamical systems characterize when data-driven learning succeeds or fails*, with convergent Koopman spectral learning and high-dimensional fluid examples.
- Physical Review Fluids 2025 — deep Koopman latent dynamics for complex mixing.

A fixed Hankel-spectrum proxy was tested:
- H01: source-stable spectra across winds at 120–240 s.
- H02: unresolved at 120 s; mixed at 180 s; good only after strong source support by 240 s.
- H03: good at 120–180 s, but at 240 s the source spectra become less separated than the wind-induced change (0/2–1/2 depending fixed delay length).

Decision:
**Koopman / transfer-operator M1 = REJECTED.**
The source is not expressed as a stable transport spectral fingerprint across all Houses/horizons; the apparent early success is often exposure/no-exposure structure rather than a source-specific operator invariant.

### η-learning collision audit tightened

Two important pre-existing GSL facts limit the claim:
- eLife 2022 already shows that intensity and timing statistics of intermittent odor bursts predict source location and that mixed intensity+timing features can outperform either family alone.
- J. Neurosci. 2019 already argues that rare high concentrations can be especially valuable localizing cues and derives a source-location-oriented receptor coding allocation.

Therefore the M1 claim **cannot** be:
- rare whiffs are informative;
- use tail statistics;
- weight high concentrations more;
- use whiff/blank timing.

The only surviving cross-domain novelty is the 2026 η-learning mechanism itself:

> standard empirical-risk learning can fit the dominant quiescent regime while being statistically wrong in the rare-event regime; constrain the learned source-evidence model by the push-forward distribution of a physically chosen intermittency/extreme observable.

The theory-specific object is not a hand-crafted feature vector. It is the reference observable law

[
\nu_{\eta}
]

and a distributional constraint such as

[
W_1((g\circ f_\theta)_\#\mu,\nu_{\eta}),
]

which is justified in η-learning as a way to control tail approximation error under rare-event data scarcity.

This distinction is mandatory for novelty.

### Current M1 score after Loop 3

| M1 candidate | Remote 25/26 strength | Unique theory object | GSL collision room | Existing-data support | Cross-dataset/lightweight | Decision |
|---|---:|---:|---:|---:|---:|---|
| Extreme-event-aware / η-learning | 10 | 10 | 7 | 9 | 9 | ACTIVE |
| Adaptive olfactory coding | 10 | 8 | 3 | 5 | 9 | REJECT |
| Koopman/transfer operators | 10 | 10 | 9 | 4 | 7 | REJECT |
| Predictive latent / JEPA | 10 | 7 | 8 | 5 | 9 | DEMOTED |

### M1 is still not frozen

η-learning remains the only active candidate, but promotion now requires a stricter test:

1. formulate an η-constrained **candidate source-evidence model**, not a feature concatenation;
2. the same base model with λ=0 is the comparator;
3. the η reference law must be frozen from simulator-only or unlabeled physical data and must not use localization error;
4. evaluate held-wind candidate ranking / proper score;
5. prove the effect is not equivalent to simple high-concentration reweighting by matching a tail-weighted ERM baseline;
6. preserve the zero-support behavior: η regularization must not fabricate source evidence when no plume reaches the sensing history.

M2/M3 remain frozen.
