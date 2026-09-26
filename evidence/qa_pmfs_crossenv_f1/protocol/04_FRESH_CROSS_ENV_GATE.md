# 4. Next gate — cross-environment QA confirmation

## Purpose

Do not test whether dependence exists again.
Test whether the **same timescale-separated QA structure** generalizes beyond
the R0 House02/W2 development condition.

## Preferred data order

1. Reuse already-generated JTD E2 raw reference/target banks if present on the
   execution machine.
2. Do not generate new plumes merely because those archives are not in this
   review ZIP.
3. If the exact JTD E2 raw arrays cannot be found and hash-verified, return
   `QA_F1_HOLD_EXISTING_CROSSENV_ASSETS_NOT_FOUND`.  Do not silently substitute
   another bank.

Existing JTD E2 result establishes there were three OPEN environments:
- House01 / `1,3-2,4_fast`
- House02 / `3,5-1_slow`
- House02 / `4,5-3_slow`
with 18 source units, 12 references/source and 4 fresh targets/source.

## Frozen models

For every environment independently, using exactly the same source support,
observation operator and reference/target split:

### M0 — independent full marginal
Estimate `p_s(t,q)` from reference only and score the target by the independent
Bernoulli likelihood.

### M1 — transient latent environment
Use the marginal-preserving probit likelihood with `L=1`.
Select rho by reference-only leave-one-realization-out.

### M2 — quasi-quenched latent environment
Search only:
`L in {2,5,T}` and `rho in {0.1,...,0.8}`.
Select `(L,rho)` by reference-only leave-one-realization-out.

### M3 — fixed transfer
No tuning:
use the R0-discovered `L=T, rho=0.6`.

No target may alter smoothing, L, rho, source support, observation threshold or
posterior calibration.

## Primary comparison

The main scientific quantity is the incremental source evidence of M2/M3 over
M0, not merely likelihood fit.

Report by environment:
- source-averaged mean true rank;
- Top-1 / Top-3;
- MRR;
- true-source posterior NLL;
- MAP spatial error;
- number of source units improved / harmed.

Also compare M2 vs M1 to test whether the persistent timescale matters beyond
same-time overdispersion.

## Confirmation label

`QA_F1_CROSS_ENV_CONFIRMED` only if:

1. M3 (`rho=0.6`, episode-shared) does not worsen mean true rank versus M0 in
   all three environments;
2. M3 improves mean true rank in at least two of three environments;
3. M3 does not worsen Top-1 by more than one target in any environment;
4. M2 reference-only selection chooses a persistent block `L>1` in at least
   two environments;
5. M2 is no worse than M1 in mean true rank in at least two environments;
6. pooled M3 posterior NLL is lower than M0;
7. no environment shows a catastrophic calibration failure comparable to the
   old JTD FULL model.

If 1-3 fail:
`QA_F1_NOT_CROSS_ENV_GENERAL`.

If rank is neutral but NLL improves:
`QA_F1_CALIBRATION_ONLY` — do not promote as main innovation.

If assets are missing/incomplete:
`QA_F1_HOLD_EXISTING_CROSSENV_ASSETS_NOT_FOUND`.

STOP after this gate.  No PMFS closed-loop yet.
