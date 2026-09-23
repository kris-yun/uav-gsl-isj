# DECISION — Demote M3 Monolithic Generative Plume World Model as Main Thesis

Date: 2026-09-23
Branch: \`research/wind-referenced-plume-world-model-v1\`

## Decision

\`DEMOTE AS MAIN SCIENTIFIC THESIS\`

Retain only as a possible stochastic residual implementation inside a stronger mechanism-level model.

## New direct/adjacent 2026 collisions

The gas-dispersion literature has now moved beyond deterministic surrogate prediction.

### Collision 1 — conditional diffusion gas-field prediction

A 2026 *Computers & Chemical Engineering* paper,
*Spatiotemporal prediction of gas dispersion field in chemical industrial parks based on the improved conditional denoising diffusion probability model*,
uses a conditional denoising diffusion probabilistic model for gas-dispersion field prediction.

Therefore the broad claim

> generative model / diffusion-style model for stochastic gas-dispersion fields

is already occupied.

### Collision 2 — conditional FNO with analytical prior

A 2026 work,
*Conditional Fourier Neural Operator with Analytical Prior for Spatio-Temporal Forecasting of Gas Dispersion*,
uses a conditional FNO with a physical/analytical prior to forecast full spatiotemporal gas-dispersion fields from release/wind parameters.

Therefore the broad claim

> neural operator + physical prior for source/wind-conditioned gas dispersion

is also crowded.

### Existing GSL-specific collisions

- 2024 physics-guided NN GSL.
- Publicly listed IROS 2026 physics-informed neural operator GSL.

## Consequence

Operator Flow Matching may still be technically newer than DDPM/FNO and useful for stochastic residuals, but that difference is now too implementation-level to carry the requested paper thesis.

Do not frame the paper as:
- first generative plume model;
- first stochastic plume world model;
- first neural-operator plume world model;
- first physical-prior gas-field generator.

## What survives

The following M3 components remain useful only inside M4 or another higher-level thesis:

- function-space stochastic residual modeling;
- non-zero wind-referenced residual dynamics;
- hard physics-constrained generation;
- GADEN multi-source field-generation benchmark.

These are implementation/auxiliary candidates.

## Main-search implication

Prioritize a scientific representation that is not simply a better source-to-field predictor.

Current stronger candidate:

\`M4 — INVARIANT-MECHANISM PLUME WORLD MODEL\`

Its thesis is mechanism reuse/composition across environments, not the choice of field generator.
