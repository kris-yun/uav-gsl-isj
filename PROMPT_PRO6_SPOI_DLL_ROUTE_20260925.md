# PRO6 NEXT TASK — SPOI / Diffusion Last Layer Route

Date: 2026-09-25

Primary-thread status:
- CESS/FSEI: STOP;
- successor/occupation mainline: STOP;
- RR-MVSI mainline: STOP;
- no new GADEN plume simulation is authorized.

Current candidate route:
**Sparse-Observation Stochastic Plume Operator Inversion (SPOI)**

Mother theory:
Park, Zhou, Kim & Barati Farimani, ICML 2026,
*Generative Neural Operators through Diffusion Last Layer*, arXiv:2602.04139, official code `sungwpark/dll-no`.

## Existing D1R facts

168 sources x16 independent realizations x10 times x30 probes.

Empirical facts:
- source-conditioned expected plume/encounter structure is strongly low-dimensional;
- plume stochastic spread is source-dependent;
- a fixed shared low-rank basis with source-conditioned latent spectrum improves proper source score over the same global-spectrum model in all four source-heldout diagnostics;
- under strict nested source-CV with full 300 queries, rank selection collapses to rank 0;
- sparse 20/100-query diagnostics sometimes select nonzero rank, but sourceheldout improvement is not uniform;
- neural input-dependent basis using only source x-y or simple free-space geometry is not stable and mostly collapses to rank 0.

Therefore current state is HOLD pending existing W2 wind + occupancy context. No new plume data.

## Critical 2026 GSL prior art

Kim et al., arXiv:2608.16221,
*Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*.

It already:
- infers a source posterior from sparse gas/wind/map observations;
- estimates wind and concentration fields;
- uses heteroscedastic diagonal Gaussian field uncertainty;
- performs active GSL and real-robot tests.

ICRA 2023 Jin et al. already combine a learned plume surrogate with probabilistic STE.

Therefore 'probabilistic GSL', 'learned plume model', 'wind/map context', 'heteroscedastic uncertainty', and 'source posterior' are all occupied claims.

## Your task 1 — derive the exact GSL second-order innovation

Formulate the distinction:

source / wind / geometry context a_s
 -> correlated conditional random plume function p(C | a_s)
 -> sparse UAV observation operator H_T
 -> likelihood p(y_T | a_s,H_T)
 -> Bayesian PMFS source posterior.

Clarify mathematically why this is not equivalent to:
- DGSE-S direct/inverse posterior learning;
- deterministic surrogate + MCMC/STE;
- diagonal heteroscedastic field regression;
- generic conditional diffusion.

## Task 2 — DLL applicability audit

Read the ICML 2026 DLL formulation carefully.

Identify:
- exact role of input-conditioned KL basis phi_k(a);
- coefficient distribution p(xi|a);
- whether a stochastic plume with independent filament seeds fits its assumptions;
- how irregular sparse observations should be handled without reconstructing the whole plume first;
- whether likelihood evaluation requires Monte Carlo or can use an analytic/importance approximation.

Propose the smallest GSL adaptation that preserves DLL's scientific principle but is computationally feasible for PMFS candidate updates.

## Task 3 — strongest novelty attack

Deeply compare against:
- Kim et al. 2026 DGSE-S;
- Jin et al. ICRA 2023 data-driven plume surrogate + STE;
- Prieto Ruiz et al. 2024 physics-guided neural GSL;
- probabilistic neural operator / MC-dropout / latent diffusion baselines from DLL;
- any GSL/olfaction work using stochastic or generative forward plume distributions.

State exactly what result would be needed before SPOI is publishably distinct.

## Task 4 — existing-data D1 design

No new simulation.

Use the completed D1R plus existing House02 W2 wind/occupancy context only.

Design a frozen sourceheldout sparse-observation gate comparing:
1. deterministic context-to-mean model;
2. diagonal heteroscedastic model;
3. shared low-rank covariance;
4. source-conditioned-spectrum model;
5. input-dependent-basis DLL-lite;
6. strongest ordinary direct source-posterior/metric baseline.

Primary endpoint must be full-168-support proper source log score and calibration, not field reconstruction MSE.

The stochastic component must improve source inference, not merely plume-field quality.

## Task 5 — sim-to-real / bank dependence

The final real UAV must not require repeated releases at every candidate source.

Explain how a model trained on simulation source ensembles could transfer using:
- known/estimated map;
- online wind observations/field;
- limited sensor calibration;
- single unknown-source plume observations.

Give a hard STOP condition if the forward operator fundamentally requires a full repeated-source bank in every new environment.

## Deliver only

1. SPOI_DLL_THEORY_BRIDGE.md
2. SPOI_PRIOR_ART_BOUNDARY.md
3. SPOI_EXISTING_DATA_D1_GATE.md
4. SPOI_SPARSE_LIKELIHOOD_DERIVATION.md
5. SPOI_SIM_TO_REAL_AUDIT.md
6. one-page GO/HOLD/STOP recommendation.

Do not run simulations.
Do not generate final targets.
Do not revive previous stopped routes.
Do not call 'apply DLL to GSL' sufficient novelty.