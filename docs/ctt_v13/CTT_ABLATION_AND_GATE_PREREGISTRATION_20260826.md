# Causal Transport Tomography: module gates and ablation preregistration

Date: 2026-08-26  
Status: pre-formula preregistration; no House held-out truth may be read from this point until the freeze manifest is complete.

## Purpose

The final method may enter expensive House01/House02/House03 closed-loop qualification only after every named module supplies positive information for its own scientific estimand and the composition supplies incremental information beyond its parts. Offline/replay gates are premise tests, not performance claims.

## Frozen module responsibilities

### M1 — physics-constrained transport phase field

Inputs: candidate location, robot location, occupancy/obstacle geometry, wind vector/history, and the frozen physical response bank.  
Output: a candidate-conditioned first-passage/arrival-hazard field over delay, not a source coordinate or posterior weight.

M1 gate metrics:

- held-out-transport-member next-event log score and integrated Brier score;
- first-passage/peak-delay error against an independently simulated transport realization;
- joint map/route/wind SE(2) transform residual;
- CPU inference time and deterministic replay equality.

Pass rule: the paired bootstrap lower confidence bound for M1 minus the fixed analytical-response baseline must be positive for predictive score, with no House showing a directionally negative median. Equivariance and replay are hard numerical contracts, not performance averages.

### M2 — intermittent phase association tomography

Inputs: M1 delay/hazard fields and a completed block of observed hit-burst onset/offset events.  
Output: an explicit candidate evidence term decomposed by burst, delay and transport path. Association is performed between observed event measure and predicted candidate arrival measure; no source truth enters online association.

M2 gate metrics:

- true-versus-best-false pre-Bayesian evidence margin after evaluator-only truth reveal;
- truth-carrier rank and pairwise win rate;
- association stability under removal of one burst and under time-order permutation control;
- evidence replay equality from the frozen event block.

Pass rule: after scorer and library hashes are frozen, the paired bootstrap lower confidence bound of the M1+M2 margin improvement over M1 must exceed zero, and time-order permutation must remove the claimed gain. A positive single seed is insufficient.

### M3 — causal miss-survival evidence

Inputs: the M1 hazard and elapsed intervals in which the candidate predicts arrival but no hit occurs.  
Output: a candidate-wise survival log-likelihood term, separately logged from hit/burst association evidence.

M3 gate metrics:

- incremental true-versus-best-false evidence margin conditional on M1+M2;
- false-candidate minus truth-candidate accumulated survival penalty;
- calibration of predicted no-hit survival on held-out transport members;
- negative control obtained by shifting miss intervals outside the predicted arrival window.

Pass rule: the paired bootstrap lower confidence bound of the M1+M2+M3 margin improvement over M1+M2 must exceed zero; the shifted-window control must remove the gain. M3 fails if it merely reduces posterior variance or applies a candidate-independent penalty.

## Learning-component admission rule

A neural field/operator is admitted only inside M1 to approximate a physical first-passage/hazard field, or as a separately logged low-dimensional discrepancy of that field. It is prohibited from receiving source truth, final localization error, seed success, PMFS posterior entropy or distance-to-truth. It must beat the fixed physical field on M1's direct held-out-transport score. If it does not, it is removed before qualification; the paper must not keep an inactive network for novelty.

## Pre-registered ablation ladder

| Arm | Components | Question |
|---|---|---|
| A0 | native PMFS | frozen baseline identity |
| A1 | M1 field + iid event-time conditional likelihood \(J_1\) | does the physical phase field alone add predictive source information? |
| A2 | M1 field + M2 structured conditional likelihood \(J_2\), replacing \(J_1\) | does temporal/path association add ordering information beyond independent event scoring? |
| A3 | \(J_2+J_3\), adding M3 count/survival factor | do physically timed misses add independent falsification evidence without recounting positive events? |
| A3-P | A3 with event-time permutation | does the gain require real temporal structure? |
| A3-S | A3 with shifted miss windows | does negative evidence require predicted arrival timing? |

The scientific full method is A3. M1 is a field provider, so its A1 score is an ablation comparator and is not also multiplied into A3. A3 may proceed only if A1>A0 on the M1 direct estimand, A2>A1 on the M2 margin estimand, and A3>A2 on the M3 margin estimand. Closed-loop final error is not used to rescue a failed module gate.

## Evidence-use boundary

1. Build a development mechanism library from frozen physical simulations and already-revealed development routes. It may be used for architecture selection but never for final qualification claims.
2. Freeze equations, network architecture, optimizer/selection rule, response banks, event parser, scoring code and all hashes.
3. Run truth-blind mechanism gates on realizations excluded from architecture selection. Reveal truth only after artifact integrity passes.
4. If any module gate fails, stop before new House closed-loop seeds. Preserve the negative result and redesign the failed module as a new version.
5. Only after all gates pass, select previously unseen House01/House02/House03 seeds and run paired A0/A3 full 300-second closed loops. Do not stop at the first accepted update.
6. The held-out generalization pass requires the preregistered pooled improvement threshold, the House-level consistency rule, and no catastrophic regression; module ablations cannot be tuned on these held-out outcomes.

## Required artifacts before qualification

- formula/code symbol map for M1/M2/M3;
- source, model and binary SHA-256 manifest;
- immutable response-bank and mechanism-library manifests;
- exact scorer and bootstrap script hashes;
- a table of module Gate results and controls;
- final seed file created only after all prior hashes exist;
- paired runtime manifests and complete 300-second posterior/trajectory traces.
