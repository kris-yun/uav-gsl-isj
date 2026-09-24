# POST-PRO SYNTHESIS V2 — Mainline Decision

Date: 2026-09-25

Status: PRIMARY-THREAD DECISION AFTER AUXILIARY-PRO REVIEW

## 1. Mainline claim

The main scientific claim is now frozen at the conservative level:

Multiscale statistical source identifiability under stochastic plume realizations

The motivating framework remains causal emergence / multiscale information, but 'causal emergence' is not treated as an established physical result.

The stronger phrase 'causal-emergence-inspired source macrostates' is allowed only if later gates additionally establish a nontrivial fidelity certificate, ordinary-baseline separation, and protocol/cross-environment mechanism predictions.

## 2. What is superseded

The pre-data local merge rule DeltaF < Q/(2 n N) is no longer the primary candidate algorithm.

Reason: it is best interpreted as a first-order MDL/pooling heuristic and its summed marginal fidelity cost must not be called full-path information loss.

The implementation remains useful as a preregistered ordinary/theory baseline.

The old D1C random-effects / nested source+realization primary bootstrap is also superseded for the fixed 168-source panel estimand.

## 3. Primary candidate

The primary candidate becomes IF-CV: information-fidelity-constrained connected pooling selected by nested microcell proper-score cross-validation.

Key properties:
- fixed micro support of 168 source cells;
- fixed micro prior pi_s = 1/168;
- connected source groups only;
- no fake source transition matrix;
- reference-only partition/model selection;
- macro probabilities lifted honestly to the original 168 cells;
- raw concentration retained in the predictive model;
- marginal encounter/mark channels used only for fidelity auditing/constraints;
- final validation uses fresh-target microcell proper scores.

## 4. Two claim layers

Strong mainline ADVANCE requires a nontrivial connected partition with preregistered fidelity constraints, stability, and reference OOF score better than identity and the locked ordinary champion.

If predictive pooling works but the distribution-free fidelity certificate is vacuous or forces identity, state = D1R_HOLD_WEAK_PREDICTIVE_POOLING_ONLY. This is not enough for the intended main innovation.

If the candidate cannot beat the strongest ordinary portfolio or the structure is unstable, state = D1R_STOP_FSEI_NOT_DISTINCT_FROM_ORDINARY_POOLING.

Only strong ADVANCE can authorize D1C.

## 5. Common predictive likelihood

All hard-pooling, identity and ordinary hard-pooling comparisons should use the same registered raw-input working family: zero-hurdle + log-amplitude Student-t posterior predictive.

This is a predictive working model, not a claim that the 300-D plume path distribution has been recovered.

## 6. Strong ordinary portfolio

Before D1C, lock one ordinary champion from the same references:
- geometry-only connected pooling;
- binary encounter-profile clustering;
- amplitude-aware mark-profile clustering;
- empirical hierarchical shrinkage;
- Bayesian tree pooling/model averaging;
- MDL/prequential pooling;
- posterior projection / partial projection.

Identity and all-in-one remain mandatory controls.

## 7. Fixed-panel D1C estimand

All 168 sources are target truths with equal target count J.

Primary uncertainty is realization uncertainty conditional on this fixed panel. The primary bootstrap keeps all 168 source labels and resamples whole target realizations within source.

Source-level resampling is not the primary CI because the 168 sources are not a random sample from a declared source population.

## 8. Real-flight interpretation

The 168x16 bank is a development/reference asset, not an online operational requirement.

A transferable method must later show that the selection principle transfers or can be calibrated with limited real data; it must not require rebuilding a full 168x16 bank in every real environment.