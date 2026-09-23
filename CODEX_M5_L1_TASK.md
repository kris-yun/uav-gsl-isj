# CODEX M5 PARALLEL TASK — Source-Agnostic Generative Lagrangian Transport

Date: 2026-09-23

## Branch

Work on:

`research/generative-lagrangian-filament-world-model-v1`

Read in this order:

1. `evidence/generative_lagrangian_filament_world_model_v1/M5_V2_SOURCE_AGNOSTIC_LAGRANGIAN_WORLD_MODEL_20260923.md`
2. `evidence/generative_lagrangian_filament_world_model_v1/L0_RECOVERABLE_TRAJECTORY_INTERFACE_20260923.md`
3. `evidence/generative_lagrangian_filament_world_model_v1/L0_B_FINAL_SERIALIZATION_PROVENANCE_20260923.md`
4. `evidence/generative_lagrangian_filament_world_model_v1/M5_PMFS_VS_GADEN_PHYSICAL_GAP_AUDIT_20260923.md`
5. `evidence/generative_lagrangian_filament_world_model_v1/L1_GENERATIVE_NECESSITY_HARD_GATE_20260923.md`

Use the corrected:

`recover_filament_pseudo_ids.py`

at commit `791a15a9960da5f32e32438cba813ee5cda4bc14`.

## Immediate execution

Do **not** train a diffusion/flow/PhysCtrl model yet.

### L1-E0 — trajectory extraction

Start with:

- development:
  `/home/zyc/hcmc_v1_independent_data_20260922/H02_R2026092211/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20`

- validation:
  `/home/zyc/hcmc_v1_independent_data_20260922/H02_R2026092212/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20`

Use the exact GADEN PlaybackSimulation API from the seed-patched build.

Fail closed unless:
- 1803 frames are present;
- sigma-age match passes ≥99.99%;
- pseudo-ID uniqueness/order checks pass;
- disappeared IDs do not reappear.

Export transition-level features and hashes.

### L1-E1 — simple-model kill test

Compare exactly the L1 charter baselines:

- B0 PMFS-like local drift;
- B1 global Gaussian;
- B2 small context-conditioned heteroscedastic Gaussian;
- B3 known-physics reference where practical.

Run independent seed only after all B0–B3 choices are frozen.

Report:
- NLL / calibration;
- residual skew/kurtosis;
- temporal dependence;
- wall-distance/wind/age dependence;
- destructive nulls.

## Main decision

Only return `GENERATIVE_NEEDED` if a simple conditional Gaussian / known-physics reference leaves reproducible, context-dependent, non-Gaussian structure on the independent seed.

Otherwise:

`GAUSSIAN_SUFFICIENT — M5 NO-GO AS MAIN`.

Do not rescue M5 by training a large generative network after a negative L1.

## Important scientific warning

GADEN itself uses Gaussian positional noise plus known obstacle/wind/buoyancy physics.

The purpose is not to rediscover GADEN.

The purpose is to determine whether a reusable source-agnostic learned transport law contains source-localization-relevant structure beyond Native PMFS and simple explicit corrections.

## Git discipline

Commit/push immediately after:
1. extractor + provenance report;
2. development-seed B0–B3 metrics;
3. frozen independent-seed metrics/nulls;
4. L1 decision.

Do not delete failed evidence.
