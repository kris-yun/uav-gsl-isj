# CODEX TASK — E4B H02 Untouched Factorial Corner

Branch:
`research/generalization-refoundation-v0`

Authoritative files:
- `research/environment_level_benchmark_v0/E4A_FAILURE_POSTMORTEM_20260925.md`
- `research/environment_level_benchmark_v0/E4B_H02_FACTORIAL_CORNER_GATE_20260925.md`

## Hard scope

Generate and analyze only:
`House02 / 4,5-3_fast` (W3).

Do NOT unseal H01 DEV.
Do NOT unseal House03.
Do NOT generate any other reserve wind.

## Pre-run lock

Before the first W3 plume run:

1. Recompute C_speed_A = W1-W0 and C_family_slow = W2-W0 using the frozen 300-D log(1+ppm) representation.
2. Freeze V_SPEED and V_FAMILY (top-2 right singular vectors, deterministic SVD sign convention).
3. Save their arrays and SHA256 hashes.
4. Freeze all G1-G5 thresholds exactly as written in E4B.
5. Save a pre-run lock JSON with all input hashes, source/probe contract hashes, wind hashes, scorer hash and thresholds.

Only after that lock exists may W3 plume generation begin.

## Acquisition

Exactly:
- 6 E1-frozen H02 sources;
- 4 independent realizations/source;
- source z=0.20 m;
- frozen 10x30 probe/time contract;
- 24 new plume runs total.

Use a deterministic new seed block documented before the first run.
Retain complete 10x83x119 concentration cubes and hashes.

No seed may be added because of scientific outcomes.

## Scoring

Compute exactly:
- C_speed_B = Bfast-Bslow;
- C_family_fast = Bfast-Afast;
- Q = Bfast-Bslow-Afast+Aslow after source centering;
- capture_speed in frozen V_SPEED;
- capture_family in frozen V_FAMILY;
- mean capture;
- target top-2 energy fractions;
- same-wind 2+2 noise norms W0/W1/W2/W3;
- Nmax;
- ||Q|| and 2*Nmax;
- target effect norms.

Apply G1-G5 and effect-size validity without modification.

## Decisions

Return exactly one:
- `E4B_PASS_FACTORIZED_ENVIRONMENT_DEFORMATION_H02`
- `E4B_FAIL_STOP_FACTORIZED_DEFORMATION_MAINLINE`
- `E4B_HOLD_TARGET_FACTOR_EFFECT_TOO_SMALL`

## Forbidden

- no neural model;
- no source posterior/rank;
- no alternate normalization;
- no field MSE optimization;
- no threshold change;
- no opening H01 DEV / House03;
- no interpretation as E4A PASS.

## Deliverables

- pre-run lock JSON;
- V_SPEED / V_FAMILY hashes;
- 24-run manifest and cube hashes;
- G1-G5 result table;
- decision;
- branch/final commit;
- review package path/bytes/SHA256.

Stop immediately after E4B.