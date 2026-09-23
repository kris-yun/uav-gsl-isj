# Parallel Main-Candidate Checkpoint — M3/M4/M5

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Current ranking

### M4 — Causal Compositional Plume World Model
**Current scientific-theme rank: #1**

Mother idea:
- ICLR 2025 compositional causal world models;
- source candidate interpreted as intervention `do(S=s)`;
- learn reusable mechanisms for source injection, wind transport, obstacles, turbulence and sensing.

Why it is strong:
- changes PMFS's scientific representation, not merely its score;
- candidate-source replay becomes counterfactual world-model inference;
- explicit physical semantics for every module;
- directly targets unseen source×wind×House recombinations.

Main risk:
- requires intervention-structured training/evaluation;
- causality must beat a matched-capacity monolithic model, otherwise the causal claim is branding.

Branch:
`research/causal-compositional-plume-world-model-v1`

Candidate-card commit:
`d9c95895b9d031f2c5fa990646da7575921a4ce8`

### M3 — Physics-Anchored Stochastic Plume World Model
**Current scientific-theme rank: #2**

Mother idea:
- Operator Flow Matching / stochastic process learning in function space;
- world model predicts a distribution over physically plausible plume fields.

Why it is strong:
- captures intermittency and joint stochastic plume structure rather than one mean hit map;
- wind/obstacle/source physics can anchor generative dynamics.

Main risk:
- direct 2026 gas-PINO near-neighbor;
- dense-field data requirement;
- stochastic model must outperform deterministic residual correction in source rank.

Branch:
`research/wind-referenced-plume-world-model-v1`

### M5 — Generative Lagrangian Filament World Model
**Current scientific-theme rank: #3 / high-value auxiliary possibility**

Mother idea:
- NeurIPS 2025 generative physics over particle trajectories;
- learn stochastic Lagrangian filament dynamics conditioned on wind/obstacles/source.

Why it is strong:
- exceptionally native to PMFS/GADEN;
- GADEN exposes filaments directly;
- lower output-data burden than dense stochastic fields.

Main risk:
- learned particle dynamics is established outside GSL;
- may look like a learned simulator unless multimodal/stochastic dynamics materially improve source identity.

Branch:
`research/generative-lagrangian-filament-world-model-v1`

Candidate-card commit:
`a246586850ec6e0a9a0dcc3f823b0e32e840e84b`

---

## Existing intervention coverage — hard finding

The six 2026-09-22 independent GADEN realizations are:

- House01:
  - seed 2;
  - seed 3;
  - source = (-0.40, -2.90, -0.30).

- House02:
  - seed 2;
  - seed 3;
  - source = (0.00, -1.00, 0.20).

- House03:
  - seed 2;
  - seed 3;
  - source = (-0.45, 1.90, -0.10).

Therefore current data vary:
- plume stochastic seed within a House;

but when House changes they also jointly change:
- geometry;
- source;
- wind/configuration.

This is **not sufficient** for a causal/compositional source-vs-wind intervention test.

Do not infer causal disentanglement from these six runs.

---

## Required pilot intervention dataset for M4

Generate in ONE House first.

### Source intervention block
Hold fixed:
- House geometry;
- wind field/configuration;
- all gas-simulation parameters.

Change only:
- source position.

Minimum:
- 4 source positions;
- 2 stochastic plume seeds each.

This estimates whether a source/injection mechanism can be reused under one transport environment.

### Wind intervention block
Hold fixed:
- House geometry;
- source position;
- gas-source parameters.

Change only:
- wind configuration / field.

Minimum:
- 2 distinct wind environments;
- 2 plume seeds each.

### Compositional holdout
Use a sparse cross design.

Example:
- train S1-W1;
- train S2-W1;
- train S1-W2;
- **test S2-W2**.

The causal/compositional claim only survives if M4 predicts the unseen source×wind combination better than a matched-capacity monolithic forward model.

---

## Required first probe for M5

Use one existing GADEN realization root.

Export `GetFilaments()` across fixed timestamps.

Determine:
- whether filament ordering/ID is stable across timesteps;
- what filament attributes are stored;
- whether one-step transition residual relative to known wind is:
  - heteroscedastic;
  - non-Gaussian;
  - multimodal;
  - obstacle-dependent.

If a simple Gaussian residual explains the filament dynamics, M5 is not a main innovation.

---

## Decision discipline

Do NOT merge M3/M4/M5 into one giant architecture yet.

First obtain an independent positive signal for each scientific claim.

Possible future architecture only if supported:

- M4 main thesis: causal compositional plume world model;
- M5 auxiliary: generative stochastic transport mechanism;
- hard physical constraint auxiliary: obstacle/wind/conservation-preserving generation.

But this composition is **not approved** until M4 passes its intervention/generalization gate.
