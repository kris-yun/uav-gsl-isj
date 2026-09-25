# E4A Failure Postmortem — Distinct Environment Perturbation Axes

Date: 2026-09-25

Frozen upstream decision:
`E4A_FAIL_STOP_DEFORMATION_SUBSPACE_MAINLINE`.

## 1. E4A remains a valid FAIL

Frozen results:
- capture(C01)=0.043113;
- capture(C21)=0.752514;
- mean capture=0.397814;
- top2 energy C01=0.921491;
- top2 energy C21=0.925615;
- effect-size validity passed.

The reusable single-subspace hypothesis is therefore stopped.

## 2. Algebraic clarification

With source-centered environment deformations:

C01 = W1-W0;
C02 = W2-W0;
C21 = W1-W2 = C01-C02.

Therefore high capture(C21) in V(C02) cannot be interpreted as an independent third-wind confirmation.

## 3. Distinct perturbation axes

Using the frozen E4A arrays:

- C01 and C02 Frobenius cosine = -0.1265;
- top-2 subspace principal angles between C01 and C02 = 85.2 deg and 72.9 deg;
- only 4.31% of C01 energy lies in V(C02);
- only 2.96% of C02 energy lies in V(C01).

Thus the speed perturbation and wind-family perturbation are nearly orthogonal in observation-deformation space.

## 4. Each perturbation type is nevertheless internally low-rank and seed-stable

Speed change within `3,5-1` family (W0<->W1):
- first-half top2 energy = 0.911;
- second-half top2 energy = 0.893;
- half-to-half subspace angles ~16.0 deg / 11.5 deg;
- cross-half capture ~0.847 / 0.860.

Wind-family change at slow speed (W0<->W2):
- first-half top2 energy = 0.938;
- second-half top2 energy = 0.910;
- subspace angles ~7.6 deg / 4.0 deg;
- cross-half capture ~0.903 / 0.930.

## 5. New narrow hypothesis

Do NOT revive the stopped single-subspace hypothesis.

A distinct new hypothesis is allowed:

> environment response may be approximately factorized by perturbation type, with different low-dimensional source-dependent deformation modes for speed and wind-family changes.

This is a 2x2 factorial hypothesis, not a universal shared-subspace claim.

House02 has an ideal untouched fourth corner:
- A/slow = W0 `3,5-1_slow`;
- A/fast = W1 `3,5-1_fast`;
- B/slow = W2 `4,5-3_slow`;
- B/fast = W3 `4,5-3_fast` (still ungenerated).

## 6. Why W3 is now scientifically valuable

W3 can test two pre-data transfer predictions simultaneously:

1. speed effect transfer:
   B/fast - B/slow should lie largely in the speed-deformation subspace learned from A/fast - A/slow;

2. family effect transfer:
   B/fast - A/fast should lie largely in the family-deformation subspace learned from B/slow - A/slow.

Equivalent additive-factorial prediction:

  S_Bfast ~= S_Bslow + S_Afast - S_Aslow

for source-centered mean signatures S.

Failure retires the factorized-environment-deformation mechanism.

## 7. Governance

- H01 DEV remains sealed.
- House03 remains sealed.
- W3 is the only additional environment that may be consumed for this hypothesis.
- no theory label or neural architecture is selected before W3.