# CTT H01 Final Hazard Solver — Freeze (PHASE 2)

Date: 2026-08-30
Status: **FROZEN_BEFORE_FRESH_TEST_DATA**

Authoritative spec: `experiments/cg_pc_ctt/ctt_final_hazard_20260830/FREEZE_FINAL_HAZARD_SOLVER_20260830.json`.

## What changed vs the rejected model

The rejected model was a 33-dimensional summary MLP (wind collapsed to
stop-mean/std/final + prefix-mean/std) with a factorized
`survival × phase|event` head.

The frozen replacement is a **spatial wind/map encoder + source/query geometric
conditioning + discrete hazard decoder**:

- Spatial encoder: a CNN over a query-centered, world-aligned `32×32` patch of
  three channels — flight-height occupancy, binned causal `wind_u`, binned
  causal `wind_v` — giving a source-independent spatial feature.
- Geometric conditioning: a 16-D MLP over source/query geometry and route
  context.
- Hazard decoder: 128 + 64 → 128 → 80 sigmoid hazards
  `h_j = P(F=j | F>=j, s, X)`.
- Loss: proper discrete event-time hazard log-likelihood (not factorized
  BCE+CE).

## Frozen degrees of freedom (excerpt)

- Patch: 32 cells × 3.2 m, cell 0.1 m; world-aligned, query-centered.
- Wind channels binned from causal local samples (no future samples);
  cells without a sample take the patch mean.
- Static-wind comparator: identical architecture/data/seed/order, wind channels
  replaced by `0.0`.
- Optimizer AdamW, lr `2e-3`, wd `1e-5`, batch 512, max epochs 60, patience 7,
  seed `20260835`, checkpoint = earliest epoch at min validation hazard loss.
- Normalization: geometric vector TRAIN-only mean/std; spatial wind scale
  frozen at `1.0 m/s`; occupancy already `{0,1}`.
- Threshold: strict `measured_ppm > 0.1` (NOT `>= 0.1`); 80 samples per stop.

## Wind deployability

`W_gen` (full CFD field) is simulator-only and never a network input. `W_online`
= causal local wind samples binned onto the patch grid. The experiment is
explicitly scoped `SIMULATION_KNOWN_WIND`; no real-flight claim.

## Consumption / split

Training contexts `0,3,5,6,8,9`; validation `4,7`; fresh confirmatory
`10,11,12,13`; closed-loop `14,15`. Transport keys: train `0..5`, test `6,7`.
Routes: train `4001..4003`, val `4004`, test `4005`. Contexts `1,2` remain
diagnostic-only forever.

## No edits after fresh test

After fresh confirmatory data is opened, the only permitted change is a
documented engineering-bug fix that does not alter scientific semantics.
