# M6 Direct Novelty Audit — Foundation Transfer Boundary

Date: 2026-09-23

## Search result

A targeted literature/web search was performed for combinations of:

- physics foundation model;
- pretrained neural operator;
- transfer learning;
- gas/plume dispersion;
- gas source localization / source inversion.

No direct work was found that applies a cross-physics pretrained simulation backbone as the forward model inside PMFS-style gas-source localization.

This is not proof of absence; final systematic audit remains required.

## Important adjacent work

### Methane foundation-model segmentation

2025 work uses Segment Anything / geospatial foundation models for methane plume segmentation from hyperspectral/satellite imagery.

This is:
- perception/segmentation;
- not physical dispersion simulation;
- not source-conditioned forward modeling;
- not PMFS candidate-source inversion.

### PHOENIX-UNet, Building and Environment 2026

Gas-specific physics-enhanced U-Net:
- obstacle-aware;
- source-conditioned;
- meteorology-conditioned;
- trained directly on gas dispersion simulations;
- generalizes to unseen source/wind conditions.

This directly blocks broad learned-dispersion novelty claims, but it is not a cross-physics foundation transfer method.

### Foundation physics models in other domains

2026 literature now includes pretrained/foundation representations for:
- porous-material diffusion;
- chemical reactor multi-physics;
- two-phase flow reconstruction;
- broad PDE simulation.

This supports M6's remote-field mother-idea status.

## Defensible M6 novelty boundary

Only pursue:

> **cross-physics dynamics-lifted foundation transfer for low-data PMFS candidate forward modeling.**

Do not claim:
- first learned gas simulator;
- first obstacle-aware learned plume model;
- first unseen-source/wind gas generalization;
- first foundation model applied to methane imagery.

## Kill rule

If a final literature audit finds an existing work that:
1. pretrains a broad/multi-physics simulation model;
2. transfers it to gas dispersion/source inversion;
3. uses the transferred forward model for source localization;

then M6 loses main-innovation priority.
