# E4A — H02 Dev Holdout: Environment-Deformation Subspace Gate

Date: 2026-09-25

Status: **ONE-TIME SCIENTIFIC UNSEAL AUTHORIZED FOR H02 DEV ONLY**

Do not unseal H01 DEV.
Do not unseal House03.

## Frozen data roles

OPEN training/discovery:
- H02 W0 = `3,5-1_slow`;
- H02 W2 = `4,5-3_slow`.

SEALED_DEV target to unseal once:
- H02 W1 = `3,5-1_fast`.

Same six E1 sources, same 30 probes, same four realizations/source.

## Frozen representation

Use only 300-D `log(1+ppm)` observations from the frozen 10x30 contract.

No feature search, amplitude normalization, neural model, or alternate representation is permitted in E4A.

## OPEN deformation subspace

Using all four OPEN realizations/source:

1. compute source means M_W0(s), M_W2(s);
2. compute D_02(s)=M_W2(s)-M_W0(s);
3. center across the six sources: C_02 = D_02 - mean_s D_02;
4. take the top two right singular vectors V_OPEN of C_02.

V_OPEN is frozen before W1 scientific data are opened.

## Target deformations

After one-time W1 unseal, compute:

C_01 from W1-W0 after source-common shift removal;
C_21 from W1-W2 after source-common shift removal.

## Primary predictive statistic

For each target C,

  capture(C) = ||C V_OPEN||_F^2 / ||C||_F^2.

Primary gate uses the mean of capture(C_01) and capture(C_21).

### G1
Mean capture >= 0.70.

### G2
Both individual captures >= 0.55.

These thresholds are below OPEN split-replication capture (~0.90-0.93) but far above random-subspace and registered seed-noise controls.

## Low-rank consistency

For C_01 and C_21 independently compute top-2 singular-energy fraction.

### G3
Both >= 0.80.

## Effect-size validity

Compare ||C_01||_F and ||C_21||_F to the registered within-W0/W2 2+2 seed-half deformation norms.

If both target deformation norms are below the maximum same-wind seed-half deformation norm, return:
`E4A_HOLD_TARGET_WIND_SHIFT_TOO_SMALL_FOR_SUBSPACE_TEST`

rather than PASS/FAIL.

## No posterior/rank tuning

E4A does not evaluate a localization algorithm.
No source posterior, classification score, field MSE, or closed loop is allowed to modify the mechanism gate.

## Decision

PASS only if G1, G2, G3 all pass and the effect-size validity check is met:
`E4A_PASS_REUSABLE_ENVIRONMENT_DEFORMATION_SUBSPACE_H02`.

Otherwise:
`E4A_FAIL_STOP_DEFORMATION_SUBSPACE_MAINLINE`.

If PASS, only then may H01 DEV be unsealed for a cross-House property test.