# IPTO + LSC Synthesis — Mechanism-Constrained In-Context Transport World Model

Date: 2026-09-25

Status: **MAIN-INNOVATION CANDIDATE SYNTHESIS; NO NEW SIMULATION AUTHORIZED**

## 1. Why the synthesis is needed

Historical M4 evidence shows a recurring failure mode:
- a forward/world model can improve field prediction;
- it can retain some source structure;
- yet source ranking / reusable transport mechanism can still fail.

M4-v2 explicitly concluded that a local field-MSE advantage was real but did not establish the reusable wind-conditioned transport mechanism.
M4-v3 again stopped despite partial field-prediction positives because the frozen wind-response mechanism gates failed.

Therefore field reconstruction error alone is not an adequate development objective for a source-localization world model.

## 2. New mechanism evidence from D1R

LSC established on the dense 168-source House02/W2 bank:

- neighboring source-conditioned plume distributions have reproducible stochastic distinguishability;
- pairwise train-half distinguishability predicts opposite-half fresh binary source-confusion error;
- a Bhattacharyya decision-theory proxy predicts fresh pairwise confusion with Spearman about 0.77-0.83;
- aggregated local confusion mass predicts fresh 168-cell posterior NLL with Spearman about 0.60-0.64;
- most strongest confusers lie within 0.6-0.9 m;
- direct posterior smoothing/pooling gives only ordinary small gains;
- LSC-specific local-discriminant learning does not stably beat a strong ordinary global LDA.

Thus LSC is best treated as a **mechanism/evaluation geometry**, not as a standalone posterior algorithm.

## 3. Main scientific reframing

A transport world model for GSL should not merely approximate plume fields.

It should infer an environment-specific stochastic transport operator whose source-conditioned outputs preserve the **local statistical distinguishability geometry of competing source hypotheses**.

Let E index House/wind/geometry regime and G_E be the stochastic transport operator.

Desired model:

  context examples from E -> inferred operator posterior q(G_E | context)

then for candidate source s:

  G_E(s, query) -> predictive observation distribution P_hat(Y | s,E).

The key inverse-problem constraint is:

  Dist(P_hat(Y|s,E), P_hat(Y|n,E))

should preserve the corresponding local source-distinguishability ordering for spatial neighbors n of s, not merely minimize pointwise field error.

## 4. Distinguishability-preservation objective

For frozen neighboring source edges (s,n), define a training/reference distinguishability quantity D_ref(s,n) using a preregistered statistical distance such as a Bhattacharyya/Hellinger/Chernoff-compatible proxy.

An inferred operator should be evaluated by two separate endpoints:

### Forward fidelity
- field/observation prediction error;
- physical transport diagnostics.

### Inverse identifiability fidelity
- rank correlation between predicted and reference local pairwise distinguishability;
- error in predicted local confusion mass;
- fresh source posterior proper score;
- fresh truth-source rank.

A model that improves field MSE while degrading inverse-identifiability fidelity is not a successful GSL world model.

## 5. Difference from M4

M4 asked whether source injection and transport could be compositionally factorized within a fixed learned model.

The new candidate asks a higher-level problem:

> can one model infer a new environment-specific transport operator from a small context set, without weight updates, while preserving the inverse problem's local source-distinguishability geometry?

This adds two requirements absent from M4:
- in-context / few-shot operator identification across environments;
- distinguishability preservation as a localization-mechanism constraint.

## 6. Mother-theory anchors

### In-context operator learning
ICON (PNAS 2023) learns a new differential operator from condition-solution data prompts at inference time without weight updates.

### Probabilistic in-context operator learning
GenICON / probabilistic operator learning (2025) interprets ICON as posterior-predictive operator inference and extends it to uncertainty-aware generative operator prediction.

### Multiple-operator generalization
2026 multiple-operator learning theory provides statistical generalization/sample-complexity analysis across unseen operator instances.

### Finite-sample stochastic distinguishability
2026 complex-systems inference-limit theory motivates treating source hypotheses as stochastic models whose empirical distinguishability depends on finite observations.

These theories are complementary: operator learning supplies transfer across E; decision-theoretic distinguishability supplies the inverse-problem mechanism that must be preserved.

## 7. Existing-data limitation

The historical real-GADEN M4 bank contains only:
- 2 source interventions (S1,S2);
- 2 wind regimes (W1,W2);
- 2 plume realizations/cell;
- total 8 realizations.

This is enough for the original 2x2 recombination audit, but not enough to validate few-shot identification of an unseen operator and unseen query-source locations.

Therefore no honest zero-new-simulation IPTO confirmation is currently possible.

## 8. What Pro / primary thread must decide before acquisition

Before any new GADEN run:

1. direct GSL prior-art overlap for in-context/few-shot transport-operator identification;
2. whether the operator-context requirement is realistic in real flight;
3. smallest number of environment/operator instances needed to make an unseen-operator test meaningful;
4. context-source/query-source split;
5. strongest equal-budget baselines: fixed global operator, target fine-tuning/meta-learning, ordinary interpolation, M4-style fixed operator;
6. whether local distinguishability preservation is a training constraint, a model-selection gate, or both.

## 9. Kill rules

STOP the candidate if:
- few-shot context does not improve unseen-source proper score in a new operator;
- ordinary fine-tuning/meta-learning matches it under the same context budget;
- field MSE improves but local source-distinguishability fidelity / source proper score does not;
- the method requires dense source coverage in each new House/wind regime;
- direct GSL prior art already implements the same in-context operator-identification mechanism.

## 10. Current decision

**HOLD FOR PRO THEORY/PRIOR-ART RETURN AND MINIMAL CROSS-OPERATOR DESIGN.**

Do not authorize a large bank.
Do not authorize closed loop.
Do not treat LSC graph smoothing or global LDA as the main innovation.
Use LSC as the scientifically validated mechanism that any future transport-world-model mainline must preserve.