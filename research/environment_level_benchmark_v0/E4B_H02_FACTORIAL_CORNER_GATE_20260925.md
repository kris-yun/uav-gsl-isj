# E4B — Untouched H02 Factorial-Corner Test

Date: 2026-09-25

Status: **PRE-DATA FACTORIAL MECHANISM GATE — 24 NEW PLUME RUNS AUTHORIZED ONLY FOR W3**

Upstream:
- E4A single reusable deformation-subspace hypothesis: STOP;
- E4A postmortem identifies two distinct, seed-stable perturbation subspaces.

Do NOT reinterpret E4B as a rescue of E4A.

## 1. Frozen 2x2 factorial

House02, same six E1 sources, same 30 probes, same z=0.20 m:

- A/slow = W0 `3,5-1_slow` (OPEN);
- A/fast = W1 `3,5-1_fast` (already consumed DEV);
- B/slow = W2 `4,5-3_slow` (OPEN);
- B/fast = W3 `4,5-3_fast` (untouched reserve).

Only W3 may be generated in E4B.
H01 DEV remains sealed.
House03 remains sealed.

## 2. Representation

Exactly the frozen 300-D `log(1+ppm)` 10x30 observation vector.

No alternate normalization, feature search, neural model, posterior, rank score, or field-MSE endpoint.

## 3. Discovery factor effects

Using all four existing realizations/source:

Speed effect at family A:

  C_speed_A = center_s(M_Afast - M_Aslow) = C01.

Family effect at slow speed:

  C_family_slow = center_s(M_Bslow - M_Aslow) = C02.

Freeze:
- V_SPEED = top-2 right singular vectors of C_speed_A;
- V_FAMILY = top-2 right singular vectors of C_family_slow.

Before W3 generation, save both arrays and hashes.

Known pre-data discovery facts:
- speed C01 top2 energy ~0.921;
- family C02 top2 energy ~0.931;
- speed split cross-capture ~0.847/0.860;
- family split cross-capture ~0.903/0.930;
- speed and family top-2 subspaces are distinct (principal angles ~85.2 deg / 72.9 deg).

## 4. Pre-data W3 predictions

After W3 is generated, define:

Speed effect at family B:

  C_speed_B = center_s(M_Bfast - M_Bslow).

Family effect at fast speed:

  C_family_fast = center_s(M_Bfast - M_Afast).

Factorial interaction:

  Q = center_s(M_Bfast - M_Bslow - M_Afast + M_Aslow).

Equivalent additive source-centered prediction:

  S_Bfast_pred = S_Bslow + S_Afast - S_Aslow.

where S_E = M_E - mean_s(M_E).

## 5. Primary transfer gates

### G1 — speed-mode transfer

capture_speed = ||C_speed_B V_SPEED||_F^2 / ||C_speed_B||_F^2.

Require:
`capture_speed >= 0.55`.

### G2 — family-mode transfer

capture_family = ||C_family_fast V_FAMILY||_F^2 / ||C_family_fast||_F^2.

Require:
`capture_family >= 0.55`.

### G3 — joint transfer

Require:
`(capture_speed + capture_family)/2 >= 0.70`.

These thresholds are below within-factor split replication (~0.85-0.93) but remain far above random 2D-subspace capture.

## 6. Low-rank consistency

Compute top-2 singular-energy fraction of C_speed_B and C_family_fast.

### G4
Both must be >=0.80.

## 7. Factorial-interaction gate

For each of W0,W1,W2,W3 compute the frozen same-wind 2+2 seed-half source-centered noise norm.

Let:

  Nmax = max(noise_W0, noise_W1, noise_W2, noise_W3).

### G5

Require:

  ||Q||_F <= 2 * Nmax.

The factor 2 is frozen before W3 generation and is intentionally conservative relative to the quadrature error expected from four R=4 environment means.

## 8. Effect-size validity

If either ||C_speed_B|| or ||C_family_fast|| is <= Nmax, return:

`E4B_HOLD_TARGET_FACTOR_EFFECT_TOO_SMALL`

rather than PASS/FAIL.

## 9. Acquisition

Generate exactly:
- one environment: H02 `4,5-3_fast`;
- six E1 sources;
- four independent realizations/source;
- total 24 new plume runs.

Use E2 deterministic seed style with a new reserved environment index recorded before first run.

Retain full cubes and hashes.

No extra seed may be added after outcomes are seen.

## 10. Decision

PASS only if effect-size validity holds and G1-G5 all pass:

`E4B_PASS_FACTORIZED_ENVIRONMENT_DEFORMATION_H02`.

Otherwise:

`E4B_FAIL_STOP_FACTORIZED_DEFORMATION_MAINLINE`.

or the explicit HOLD above.

## 11. Consequence

PASS does NOT establish a main innovation.

PASS only authorizes a later cross-House structural-property test using H01 DEV.

FAIL retires:
- reusable low-rank environment-deformation adaptation;
- factorized speed/family deformation as the main mechanism;
- this route as justification for IPTO/context adaptation.

H01 DEV and House03 remain protected after a FAIL.