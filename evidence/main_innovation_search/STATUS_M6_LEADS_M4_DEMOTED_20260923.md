# Main Search Status Update — M6 Leads, M4 Demoted

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Current ordering

### #1 — M6 Dynamics-Lifted Physics Foundation PMFS
Status: `LEAD / ADVANCE`

Why:
- ICML 2026 GeoPT provides a released cross-physics pretrained model;
- official volume representation maps unusually well to indoor free-space geometry;
- wind fits the released dynamics-prompt semantics;
- real House02 token/runtime probe is cheap;
- gas-specific source injection can be added without changing the pretrained input projection;
- no direct GSL foundation-model collision found so far.

Hard unresolved gate:
- actual checkpoint load on Codex/VM;
- low-data pretrained-vs-random-init advantage;
- downstream truth-source rank.

### #2 — M3 Physics-Anchored Stochastic Plume World Model
Status: `KEEP / DATA-HEAVIER`

Main unresolved gate:
- stochastic OFM must beat deterministic forward correction.

### M4 — Causal Compositional Plume World Model
Status: `HOLD / DEMOTED`

Historical 2×2 source×transport data are clean interventions, but:
- zero-parameter composition does not improve held-out plume reconstruction over simply reusing the same source under the other transport;
- source identification reaches 12/12 at 180/240 s for both;
- therefore existing data do not demonstrate a unique need for causal composition.

### M5 — Generative Lagrangian Filament World Model
Status: `KEEP SECOND-TIER / POSSIBLE AUXILIARY`

## M6 novelty boundaries added

The following already exist:

- general Earth-system foundation models including air-pollution forecasting (Aurora, Nature 2025);
- physics-guided topography/wind pollutant prediction (TopoFlow, 2026);
- gas-specific learned obstacle-aware dispersion models (PHOENIX-UNet, Building and Environment 2026);
- gas PINN/PINO/source-conditioned learned forward models.

Therefore M6 must not claim:
- first foundation model for environmental prediction;
- first learned pollutant field model;
- first unseen-wind/source generalization;
- first geometry/wind-conditioned gas surrogate.

The specific hypothesis is:

> **cross-physics geometry–dynamics pretraining can reduce gas-specific high-fidelity data demand for PMFS candidate forward modeling and improve source identity under scarce plume supervision.**

## Immediate required comparison

M6 only advances scientifically if:

[
	ext{pretrained GeoPT}
>
	ext{same GeoPT architecture random-init}
]

in:
- low-data held-out plume prediction;
- unseen source/wind;
- and finally truth-source candidate rank.

Architecture superiority alone is irrelevant.

## Relevant recent boundaries

- Aurora, Nature 2025: large Earth-system foundation model, including air-pollution forecasting.
- PHOENIX-UNet, Building and Environment 2026: gas-specific obstacle-aware surrogate, unseen source/wind.
- GeoPT, ICML 2026: cross-physics dynamics-lifted geometric pretraining.

The novelty lives in **transfer into PMFS source inference**, not in any one of those ingredients alone.
