# Post-M4 Main-Innovation Search Screen — 2026-09-23

Branch: \`research/mori-zwanzig-plume-belief-v1\`

## Evidence to explain

Frozen M4-v3 D0:
- wind-response amplitude: approximately 0.58–0.64 of truth;
- centroid magnitude and relative wind/source response passed;
- no-characteristic ablation retained only approximately 0.107–0.111 of the wind-response norm;
- full wind-intervention cosine: only approximately 0.34–0.38;
- all four wind-cosine gates failed.

Interpretation to explain:
**coarse wind transport exists, but the projected deterministic field dynamics have the wrong internal response geometry.**

## Candidate screen

| Candidate | Scientific parent | Matches D0 failure? | Can preserve useful M4 signal? | Main risk | Decision |
|---|---|---|---|---|---|
| deterministic residual corrector | generic residual learning | superficially | yes | post-hoc patch; can overwrite mechanism | reject |
| memory-only operator | Mori–Zwanzig / ICLR 2025 MemNO | strong for hidden-history error | yes | deterministic output still misses stochastic filament variability | retain as auxiliary |
| stochastic diffusion/flow closure only | JCP 2025 stochastic closure; ICML 2025 AFM | strong for unresolved plume microstructure | yes | may generate plausible fields without correct temporal causality; compute cost | retain as auxiliary |
| latent Mamba / generic SSM operator | ICML 2025 LaMO | moderate | yes | architecture-first rather than failure-mechanism-first | not main |
| full-field generative plume model | diffusion / flow matching | can fit geometry | weak | likely replaces physical transport and is too expensive per source candidate | reject as main |
| **Mori–Zwanzig plume-belief dynamics** | MZ projection + Generalized Langevin reduced dynamics | **direct** | **yes: M4 becomes Markov term** | novelty must be in GSL/inverse-likelihood integration, not MZ itself | **promote** |

## Why memory-only is insufficient

The two independent plume realizations are different stochastic trajectories under the same source/wind intervention, while a deterministic Markov or deterministic-memory model still maps the same forcing/history to a single field.

Memory can correct hidden-history effects but cannot by itself represent the distribution of unresolved turbulent outcomes.

## Why stochastic-only is insufficient

A stochastic residual generator can restore high-frequency/intermittent structure, but without a causal history state it can learn a static conditional texture model rather than a reduced dynamical law.

The D0 failure is temporal/structural, not merely super-resolution.

## Proposed unified scientific statement

The physically resolved plume representation used for localization is a coarse projection of a high-dimensional turbulent filament process. Consequently its exact reduced dynamics contain:

1. a current-state Markov transport term;
2. a history-dependent memory term;
3. unresolved orthogonal stochastic dynamics.

This is the Mori–Zwanzig / Generalized Langevin decomposition.

## Role assignment

### Main innovation
**MZ-PBD: Mori–Zwanzig Plume Belief Dynamics**

### Auxiliary A
**Finite-memory closure**
- causal history only;
- lightweight SSM/time-delay operator;
- ablation: memory kernel zero.

Scientific anchors:
- ICLR 2025: *On the Benefits of Memory for Modeling Time-Dependent PDEs*;
- PNAS 2026: *Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows*;
- 2026 MZ-GNN preprint for turbulent tracer transport.

### Auxiliary B
**Constrained stochastic orthogonal closure**
- low-rank conditional flow/diffusion model;
- residual only;
- hard projection prevents trivial overwrite of coarse mass/centroid during development;
- ablation: zero stochastic residual / posterior mean.

Scientific anchors:
- JCP 2025: stochastic closure via conditional diffusion + neural operator;
- ICML 2025: Adaptive Flow Matching for small-scale physics;
- NeurIPS 2025: Physics-Constrained Flow Matching.

## GSL novelty boundary

Already occupied:
- physics-guided NN GSL;
- Green-function GSL;
- generic physics-informed neural-operator GSL (IROS 2026 accepted);
- generic MZ turbulence modeling.

Potentially defensible if verified:
**MZ reduced stochastic-memory plume dynamics used to produce a marginalized candidate observation likelihood for probabilistic gas-source localization.**

Targeted searches on 2026-09-23 did not reveal a direct prior work combining Mori–Zwanzig plume reduced dynamics with gas-source candidate Bayesian ranking. This is not an exhaustive novelty clearance.

## First kill test before any new model training

Do not immediately train the full MZ-PBD.

First run a source-blind residual-memory audit on the existing House02 development sequence:

1. reconstruct frozen M4-v3 one-step / finite-horizon residuals;
2. measure temporal autocorrelation / mutual information of residuals after conditioning on current resolved state and wind;
3. compare residual predictability from current state only vs finite history;
4. measure whether residual energy concentrates in higher spatial frequencies / obstacle-wake regions;
5. test whether residual distributions differ between plume realizations under the same S/W condition.

Kill rules:
- if residuals have no material temporal memory, reject MZ memory auxiliary;
- if residuals are nearly deterministic conditional on history, stochastic auxiliary is unnecessary;
- if residual error is dominated by a simple coordinate/sign/data-interface error, stop and fix the interface rather than claim MZ;
- if neither memory nor stochasticity explains the D0 response-geometry error, reject MZ-PBD.

Only after this diagnostic may a development architecture be frozen.
