# CODEX TASK — E4A H02 One-Time Dev Unseal: Deformation-Subspace Gate

Branch:
`research/generalization-refoundation-v0`

Authoritative files:
- `research/environment_level_benchmark_v0/E3_OPEN_STRUCTURAL_AUDIT_20260925.md`
- `research/environment_level_benchmark_v0/E4A_H02_DEV_DEFORMATION_SUBSPACE_GATE_20260925.md`

## Hard scope

Unseal and analyze **only**:
`House02 / 3,5-1_fast` (SEALED_DEV_HOLDOUT).

Do NOT unseal:
- House01 DEV `2,4-1_fast`;
- either House03 final environment.

Do not generate any new plume.
Do not train any neural model.
Do not alter the frozen representation or thresholds.

## OPEN inputs

Use the already-open House02 environments:
- W0 = `3,5-1_slow`;
- W2 = `4,5-3_slow`.

Use exactly:
- six E1-frozen sources;
- four realizations/source;
- frozen 10x30 observation contract;
- 300-D `log(1+ppm)` vector.

## Frozen computation

1. From OPEN W0/W2 source means compute the centered source-dependent deformation C_02.
2. Freeze V_OPEN = top-2 right singular vectors of C_02.
3. Unseal W1 = `3,5-1_fast` once.
4. Compute C_01 and C_21 exactly as specified.
5. Report capture(C_01), capture(C_21), their mean.
6. Report top-2 singular-energy fractions for C_01 and C_21.
7. Compute same-wind 2+2 seed-half deformation norms for W0 and W2 and apply the frozen effect-size validity rule.

## Decision

Return exactly one:
- `E4A_PASS_REUSABLE_ENVIRONMENT_DEFORMATION_SUBSPACE_H02`
- `E4A_FAIL_STOP_DEFORMATION_SUBSPACE_MAINLINE`
- `E4A_HOLD_TARGET_WIND_SHIFT_TOO_SMALL_FOR_SUBSPACE_TEST`

Do not report a scientific mechanism outside this gate.
Do not tune a posterior or run closed loop.

## Deliverables

- exact OPEN V_OPEN hash / source data hashes;
- C_01/C_21 capture values;
- top-2 energy fractions;
- deformation norms and same-wind noise norms;
- threshold table PASS/FAIL;
- branch/final commit;
- review package path/bytes/SHA256.

Stop after E4A.