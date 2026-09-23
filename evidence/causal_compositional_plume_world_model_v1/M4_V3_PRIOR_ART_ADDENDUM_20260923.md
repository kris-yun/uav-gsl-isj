# M4-v3 Prior-Art Addendum — 2026-09-23

This addendum narrows the claim boundary after checking very recent source-localization literature. It does not alter any D0 metric or threshold.

## A. Deep probabilistic indoor GSL with physical dependencies — August 2026

Seunghwan Kim, Hyungjin Kim, Junhee Lee, Hyondong Oh,  
*Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*, arXiv:2608.16221, submitted 17 Aug 2026.

The paper explicitly moves beyond an end-to-end source predictor and encodes physical dependency structure through sequential conditional inference. Public descriptions of DGSE-S specify:
- map/inlet information -> wind-field inference;
- wind plus concentration observations -> concentration-field inference;
- wind and concentration fields -> source posterior;
- uncertainty is propagated through intermediate wind/concentration fields by Monte Carlo sampling.

### Consequence for M4-v3

The following claims are forbidden:
- first causal/physical-dependency decomposition for indoor GSL;
- first wind-concentration-source sequential probabilistic model for GSL;
- first deep probabilistic source posterior using intermediate wind/concentration fields.

M4-v3 is structurally different only if it demonstrates that **candidate source hypotheses are interventions on the forcing term of one shared source-agnostic evolution propagator**, rather than labels/latent inputs of a source predictor.

## B. Structure-preserving learned digital twin for source localization — September 2025

Benjamin David Shaffer et al.,  
*Physics-informed sensor coverage through structure preserving machine learning*, arXiv:2509.10363.

This work uses conditional neural Whitney forms / finite-element exterior-calculus structure in a learned digital twin for adaptive source localization, preserving discrete physical structure and using the twin for source recovery and sensor placement.

### Consequence for M4-v3

The following claims are forbidden:
- first structure-preserving machine-learning model for source localization;
- first learned digital twin with physical conservation for source localization;
- first operator-learning approach to source recovery with structural guarantees.

## C. IROS 2026 PINO-GSL boundary

Quanqi Zheng, Lei Chen,  
*A physics-informed neural operator for gas source localization in turbulent environments*, IROS 2026 accepted.

The full method was not publicly inspectable in the present audit. Therefore M4-v3 conservatively assumes all generic novelty claims around:
- neural operators for GSL;
- physics-informed operators for GSL;
- turbulent-environment neural-operator GSL

are unavailable.

## D. Remaining defensible novelty target

The manuscript-level novelty target is narrowed to the conjunction of four properties:

1. **Interventional forcing semantics**  
   Every candidate source changes only the forcing/injection field (Q_s). It does not condition transport weights.

2. **Shared non-autonomous transport propagator**  
   All source candidates under the same environment use the same (U_{W(t),O}), driven by the measured/canonical time-varying wind history.

3. **Characteristic action of wind**  
   Wind changes the spatial flow map through explicit semi-Lagrangian backtracing before any learned local closure. Wind is not merely concatenated, embedded, or used as an amplitude gate.

4. **Inverse-localization falsification**  
   The mechanism must pass intervention-response parity, source-superposition, characteristic-ablation, unseen source×wind recombination, unseen-House transfer, and finally multi-candidate truth-rank improvement in the PMFS probability-map setting.

The intended contribution is therefore not “physics-informed GSL” in general. It is a **source-agnostic interventional evolution operator as the reusable forward hypothesis generator inside probabilistic gas-source localization**.

## E. Distinguishing tests that must appear in the paper if M4-v3 survives

- Prove/source-audit that source ID and coordinates cannot reach transport conditioning.
- Numerically verify source superposition for fixed wind/geometry.
- Report real-vs-predicted W1→W2 intervention magnitude, not only field MSE.
- Disable characteristic advection while retaining the wind-conditioned local closure.
- Reverse wind as a diagnostic and verify transport displacement changes direction.
- Use a dense geometry-only source candidate bank and report truth rank.
- Repeat on untouched Houses; House02 remains development-only.

If these tests are omitted, M4-v3 collapses back into an already-occupied generic “physics-guided / causal-dependency / neural-operator GSL” category.
