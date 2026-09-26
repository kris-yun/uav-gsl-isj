# QA-PMFS MAINLINE V0 — 2026-09-26

## Decision

**PROMOTE TO MAIN-INNOVATION CANDIDATE; NOT YET CLOSED-LOOP LICENSED.**

Working name:

**QA-PMFS — Quasi-quenched / Annealed Random-Environment PMFS**

The proposal is not "add temporal memory" and not "average more wind models".

It separates two stochastic timescales:

1. fast transport / wind uncertainty is **annealed** inside each event's
   marginal probability;
2. slow episode-level plume/environment variability is treated as a
   **quasi-quenched latent state**, shared by an observation episode and
   marginalized exactly once over the episode.

Core likelihood:

`L_QA(s) = ∫ p(z) ∏_e [ E_(W_e|z) p(y_e | s, W_e, z) ] dz`

The PMFS source-location probability map is retained:

`q(s|y) ∝ pi(s) L_QA(s)`.

## Evidence already established

Input hashes:

- Dependence D0 V2 review: `5016e8a56ff747d153c332d0346a0e4f8beed648757e4136b5e808f9267d6c7f`
- Wind alignment D0 review: `a20c5d6bd66c37f7039f4059f6a419fa333b0a62936e87177536a2d77435180f`

R0 OPEN panel:
- all four reference-only split searches independently selected `L=10, rho=0.6`;
- primary A+B mean rank: 1.125000
  -> 1.062500;
- primary Top-1: 89.93%
  -> 95.49%;
- robustness C+D mean rank: 1.142361
  -> 1.062500;
- robustness Top-1: 89.24%
  -> 94.79%.

House01 PMFS bridge with `rho=0.6` transferred without House01 truth tuning:
- historical static marginals: truth rank 47 -> 66;
- P1 height-only: 49 -> 68;
- C1 multi-state/site-pooled: 31 -> 23;
- P2 event-matched multi-state: 28 -> 25.

Therefore the latent-regime correction is **not a generic score hack**.
It helps only after the fast transport marginal is made more appropriate.

## Interpretation boundary

This evidence supports a two-timescale random-environment hypothesis.
It does not yet establish:
- a final cross-House deployment model;
- a calibrated source posterior under real UAV trajectories;
- a closed-loop improvement.

Run `04_CODEX_EXECUTE_ONLY.txt` next.  Do not return to MaxCal, JTD, or a neural
world model unless the QA fresh/cross-environment gate fails for a specific,
documented reason.
