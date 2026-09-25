# IPTO Post-Pro Decision — 2026-09-25

Decision: **HOLD_MAIN_INNOVATION / GO_ZERO_SIMULATION_MECHANISM_ONLY**

## What is not authorized

- no 48-run House02 D0;
- no Pro 144-run D0;
- no new CFD/wind generation;
- no Codex execution;
- no closed loop.

## Why

1. The broad IPTO task is scientifically distinct from the executed M4 task, but not yet algorithmically distinct from Neural Processes, GP/Bayesian calibration, latent MAP/Laplace adaptation, or meta-learning.
2. Recent GSL/source-inversion prior art already occupies physics-guided operator learning and observation-conditioned digital-twin/source inference.
3. The Pro 144-run design requires six additional valid House02 operators; the verified House02 canonical inventory contains four total wind configurations, so the design is not currently executable without new physical wind/CFD assets.
4. The earlier 48-run design has only one locked operator and is insufficient for the intended main-innovation claim.

## Approved narrow mechanism

Source-contrast operator identifiability:

For local candidate-source edge e=(s,n), define

c_e(y,z)=log p(y|s,z)-log p(y|n,z).

Only operator directions that change these local contrasts can improve source localization to first order.

Define

g_e(y)=grad_z c_e(y,z0),

and task-relevant operator metric

G=sum_e w_e E[g_e g_e^T].

Directions in null(G) can change the forward field while leaving registered local source odds unchanged to first order.

If context induces operator posterior covariance Sigma_C, the first-order task-relevant uncertainty is

U(C)=tr(G Sigma_C).

Context adds localization information only if it reduces U(C), shifts source contrasts correctly, or both.

## Empirical motivation

- D1R LSC: local stochastic distinguishability predicts fresh pairwise source confusion and 168-cell proper NLL.
- M4-v2: field-prediction advantage existed while reusable wind/source response mechanism failed.
- M4-v3: partial field positives survived but frozen wind-response gates failed.

These facts are consistent with forward-error improvements occurring in source-contrast-null operator directions.

## Prior-art boundary

Not novel:
- goal-oriented model reduction;
- parameter-to-observable operator learning;
- task-aware surrogates;
- NP/GP/Bayesian calibration;
- ICON/GenICON;
- neural operators;
- observation-conditioned digital twins.

Potential novelty remains only in a GSL-specific, stochastic, local source-likelihood-contrast formulation that:
- is measured on the candidate-source confusion graph;
- predicts whether context can improve source odds before target evaluation;
- is not reproduced by strong ordinary calibration under the same context;
- preserves PMFS microcell posterior support;
- transfers with sparse real-site calibration.

## Next zero-simulation gate

Before any acquisition:

1. derive a strong ordinary GP/latent-calibration baseline in the same source-contrast coordinates;
2. derive one structurally distinct candidate, if one exists;
3. show a pre-data falsifiable difference between them;
4. audit direct literature for likelihood-ratio/posterior-odds-preserving operator identification;
5. only then redesign a minimal multi-operator D0 with at least two locked operators.

If step 2 fails because the candidate is mathematically equivalent to ordinary NP/GP calibration, STOP IPTO as the main innovation before collecting new data.