# Post-PRO Mainline Revision — Source-Contrast Operator Identifiability

Date: 2026-09-25

Decision: **IPTO MAIN-INNOVATION HOLD; SOURCE-CONTRAST MECHANISM APPROVED FOR ZERO-SIMULATION THEORY/AUDIT ONLY**

## 1. Why the previous 48-run draft is not authorized

The auxiliary Pro review correctly identifies that the current IPTO task is not yet proven to be algorithmically distinct from Neural Processes, GP/Bayesian calibration, meta-learning, or ordinary latent adaptation.

The previous House02-only 48-new-run design also contains only one locked target wind/operator and therefore cannot carry a strong cross-operator main-innovation claim.

Conversely, the Pro 144-run design requires six additional valid House02 operators. The verified House02 inventory contains four canonical physical wind configurations total, so that design is not currently executable without generating additional physical wind/CFD assets.

Therefore neither 48 nor 144 runs are authorized now.

## 2. Mechanism that survives Pro + LSC

Calibration is useful for source localization only if it changes the **relative evidence between candidate sources**.

Let z parameterize an environment/transport operator and let

  p(y | s,z)

be the source-conditioned observation law.

For a neighboring/confusable source pair e=(s,n), define the source log-likelihood contrast

  c_e(y,z) = log p(y|s,z) - log p(y|n,z).

For a small operator perturbation dz around z0,

  dc_e ~= g_e(y)^T dz,

where

  g_e(y) = grad_z log p(y|s,z0) - grad_z log p(y|n,z0).

Only operator directions with nonzero projection onto g_e can change the local source odds to first order.

## 3. Source-contrast-relevant operator subspace

For the frozen local source-confusion graph E, define

  G = sum_e w_e E_y[g_e(y) g_e(y)^T].

The range of G is the **source-contrast-relevant operator subspace**.

Any operator perturbation dz in null(G) changes neither of the registered local source log-odds to first order:

  g_e^T dz = 0 for every frozen edge e.

Such a direction can still strongly change the forward field or reduce field MSE.

Therefore:

> forward-operator accuracy and inverse source identifiability are not equivalent objectives.

This is the mechanism-level explanation suggested by the historical M4 failure and independently supported by the D1R LSC result.

## 4. Context usefulness under operator uncertainty

Let a context set C induce an operator posterior with covariance Sigma_C.

To first order, the residual variance of local source log-odds caused by operator uncertainty is governed by

  Var[c_e | C] ~= g_e^T Sigma_C g_e.

Aggregate task-relevant operator uncertainty:

  U(C) = tr(G Sigma_C).

A context set adds localization information only if it reduces U(C), changes the relevant contrast means correctly, or both.

Reducing posterior uncertainty only in null(G) may improve field reconstruction while leaving source localization unchanged.

## 5. Falsifiable predictions

The source-contrast mechanism predicts before any new acquisition:

1. Context source-label derangement should reduce or destroy improvements in local source odds even if common plume amplitude statistics remain available.
2. Wrong-operator context should distort contrast-relevant adaptation more than an unpaired/global-summary control if source->response pairing is truly used.
3. Contexts that mainly constrain common-mode plume changes may improve field error without improving source proper score.
4. A strong ordinary GP/NP/meta-calibration method that reduces the same U(C) should match IPTO; if so, IPTO is not a distinct main innovation.
5. A candidate world model that improves field MSE but fails to preserve the D1R-style local distinguishability graph must fail the GSL mechanism gate.

## 6. Link to historical M4 evidence

M4-v2 had a real held-out field-MSE advantage, but its frozen operator captured only about 5-6% of the physically observed relative wind/source response and was declared NO-GO as a reusable transport mechanism.

M4-v3 again showed partial field-prediction positives but failed every frozen wind-response cosine gate and STOPPED.

The old two-source sparse-rank diagnostic could not establish meaningful source-discrimination improvement because both ordinary and operator models trivially ranked the true source first among only two candidates.

These historical outcomes are consistent with, but do not prove, the source-contrast-nullspace mechanism above.

## 7. Relation to LSC

D1R LSC established that local neighboring-source stochastic distinguishability predicts fresh pairwise confusion and fresh 168-cell posterior NLL.

Therefore the frozen local source graph provides the task geometry that a transport model must preserve.

LSC is not itself the main algorithm; it supplies the inverse-problem mechanism/evaluation object.

## 8. Novelty boundary

The following are not novel:
- Neural Processes;
- ICON / GenICON;
- Bayesian/GP calibration;
- few-shot adaptation;
- no-weight-update inference;
- neural operators;
- probability maps;
- source-discriminant losses.

A future main contribution would require a demonstrably useful **task-relevant operator-identification principle** that:

- separates contrast-relevant from contrast-null operator directions;
- predicts when limited context can/cannot improve source odds;
- survives strong NP/GP/meta-learning baselines;
- improves unseen-source proper score on locked new operators;
- remains feasible with sparse real-site calibration.

## 9. Current action

Do not run the 48-run draft.
Do not run the Pro 144-run draft.
Do not generate additional CFD/wind assets.

Next actions are zero-simulation only:

1. audit whether the source-contrast subspace result is already standard under goal-oriented/task-aware operator learning or inverse-problem literature;
2. derive an implementable ordinary baseline and a genuinely distinct candidate, if any;
3. use existing M4 2x2 assets only as a mechanism sanity check, not as main confirmation;
4. only then redesign the smallest cross-operator acquisition.