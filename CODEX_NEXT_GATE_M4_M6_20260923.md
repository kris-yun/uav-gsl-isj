# CODEX NEXT GATE — M6 checkpoint load + one-source GADEN benchmark

Date: 2026-09-23  
Branch: `research/main-innovation-search-parallel-v1`

## Priority 1 — M6 actual pretrained checkpoint load

Use official:

- repo: `Physics-Scaling/GeoPT`;
- model repo: `GeoPT/GeoPT_Pretrained_Models`;
- checkpoint: `GeoPT_8layers.pt`;
- expected SHA256:
  `c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2`.

Instantiate exact official config:

- Transolver;
- space_dim=3;
- fun_dim=11;
- hidden=256;
- heads=8;
- layers=8;
- mlp_ratio=2;
- slice_num=32.

Report:
- checkpoint tensor count;
- model tensor count;
- exact loaded tensors;
- exact excluded tensors;
- loaded parameter percentage;
- shape mismatches;
- checkpoint SHA256.

Then build the House02 GeoPT input using:

`research/geopt-physics-foundation-pmfs-v1/evidence/geopt_physics_foundation_pmfs_v1/build_pmfs_geopt_features.py`

Use recovered Native ground-truth wind if available.

Run one forward pass with actual pretrained weights.

No plume training yet.

## Priority 2 — one new-source GADEN-RT benchmark

Before the 16-run shared pilot:

- House02;
- one new source position selected source-blind;
- one existing physical wind condition;
- one plume seed;
- GADEN-RT RunningSimulation;
- saveResults=false.

Export:
- sensor-height concentration slices on the PMFS free grid;
- filament states on a predeclared temporal schedule;
- wind field;
- exact manifest.

Record:
- simulated duration;
- wall-clock;
- CPU/GPU;
- RAM;
- slice-query overhead;
- filament-export overhead;
- disk size.

Do not launch the 16-run batch until this benchmark is committed.

## Shared-pilot contract

If both gates pass, follow:

`evidence/main_innovation_search/SHARED_PILOT_M3_M4_M5_M6_DATA_CONTRACT_20260923.md`

Do not invent a different dataset per candidate.

## Immediate decision rules

### M6 demote if
- pretrained internal layers do not load at high coverage;
- House02 input requires changing the pretrained input projection;
- actual pretrained forward is impractical.

### Shared pilot stop if
- one-source generation is unexpectedly expensive;
- output fields/filaments cannot be exported reproducibly.

Commit after each priority separately.
