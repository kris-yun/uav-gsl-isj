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
