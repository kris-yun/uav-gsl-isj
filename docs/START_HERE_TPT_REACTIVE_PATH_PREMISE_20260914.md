# START HERE — TPT Reactive-Path Premise

Date: 2026-09-14
Research-control branch: `project/research-master-20260914`
Latest experimental evidence: `1be4363959fcf7909e935568bb74d0a0dbd4328b`

## Decision

The next authorized scientific task is a single offline falsification of one big-science candidate:

**Source-Conditioned Transition-Path Fingerprint（源条件过渡路径指纹）**

Mother theory: **Transition Path Theory, TPT（过渡路径理论） / committor（承诺概率） / reactive current（反应流）** from statistical and chemical physics.

This is NOT yet the paper main innovation.

## Why this candidate survived collision screening

Do NOT claim novelty for:

- scalar source-to-sensor reachability / committor;
- first-passage or detection probability;
- generic Bayesian source inference with TPT;
- generic TPT origin inversion;
- generic reactive transport corridor.

Those have direct or near-direct precedents in robotic OSL and environmental transport.

The only remaining candidate worth falsifying is narrower:

> Conditioned on successful finite-time source-to-sensing transport, does the **directed geometry of the successful transition-path ensemble** preserve source identity across transport regimes better than scalar hit probability, first-entry statistics, and unconditional plume occupancy?

If NO, TPT is demoted to diagnostic language and the route stops.

## Read exactly in this order

1. `docs/TPT_COLLISION_SCREEN_V3_20260914.md`
2. `docs/TPT_THEORY_FREEZE_V1_20260914.md`
3. `docs/TPT_DATA_SEMANTICS_AUDIT_V1_20260914.md`
4. `docs/TPT_REACTIVE_PATH_GATE_V1_20260914.json`
5. `docs/CODEX_TPT_REACTIVE_PATH_PREMISE_V1_20260914.md`

## Critical data rule

The existing 12 R3B concentration caches are **one stochastic realization per source×wind**. Eulerian concentration snapshots are not a transition-path ensemble and cannot be relabeled as a committor.

Codex must first identify the exact GADEN stochastic transport kernel / filament trajectory semantics. If stable paths or exact seeded replay cannot be established, stop with:

`D. TPT_TRAJECTORY_ENSEMBLE_NOT_IDENTIFIABLE`

## First executable branch

Create from the current research-control HEAD:

`codex/tpt-reactive-path-premise-20260914`

Then follow the execution contract exactly.

No PMFS modification, no planner, no neural network, no closed loop, no W_altfast before design freeze.

## Only success state

Even if all premise gates pass, the authorized statement is only:

> In the controlled House02 stochastic transport bank, successful source-to-sensing transition-path geometry carries cross-transport source identity beyond marginal hit/entry/occupancy statistics.

Return to GPT before any PMFS integration, planner design, cross-House test, or novelty claim.
