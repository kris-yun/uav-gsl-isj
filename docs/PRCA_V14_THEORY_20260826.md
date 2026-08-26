# PRCA V14 — Proximal Replicated Causal Assimilation

Status: DEVELOPMENT CANDIDATE — REVEALED-DATA OFFLINE GATE ONLY

Base source: `664b2f9f3ec728d7677ab080629c076ef018f335`

## 1. Failure that V14 addresses

RCEC V13 used causal/PMFS ranks to reconstruct a new source state from a geometry-only prior. The H02 prospective stress test showed that this can be unsafe when the inverse-transport model is misspecified: all causal views can agree on a physically wrong basin, and replacement of the sharply informative native PMFS state by a rank-only generalized state can produce catastrophic posterior distortion.

The H02 transport-mismatch audit further showed that simply replacing Euclidean geometry with occupancy geodesics or currently available backward streamlines does not restore true-source ordering. V14 therefore changes **evidence ownership**, not the frozen ACIT transport family.

## 2. Three-part method

### M1 — Replicated amplitude-invariant causal score

Keep the frozen 54-member conditional-on-hit-count inverse-transport score, cumulative evidence reservoir, odd/even temporal folds, and the existing truth-blind identifiability gate. This keeps the useful amplitude-invariant causal diagnostic while acknowledging model misspecification.

For candidate source `s`, transform the two fold scores to standard-normal ranks:

`z_even,t(s), z_odd,t(s)`.

### M2 — Dependent-view lower-envelope consensus

The two folds are generated from the same physical trajectory and transport process. They are therefore **dependent evidence views**, not independent likelihoods. V14 does not multiply them. It uses the finite-view maximin utility

`r_t(s) = min(z_even,t(s), z_odd,t(s))`.

A candidate receives only the support shared by both replicated views. There is no learned weight, House-specific parameter, or independence claim.

### M3 — Native-anchored KL-proximal assimilation

Let `p_native,t(x)` be the native PMFS source state after the current PMFS source update and before any causal injection. Let `s(x)` denote the frozen candidate region containing cell `x`. PRCA defines

`q_t(x) ∝ p_native,t(x) * exp(r_t(s(x)))`.

Equivalently, over distributions supported by the native PMFS state,

`q_t = argmax_q { E_q[r_t(s(x))] - KL(q || p_native,t) }`.

Thus causal evidence can **tilt** the current physical source state but does not replace its probability amplitude or spatial support. The reference distribution is the current native PMFS state, not the previous PRCA state and not a geometry-only prior.

No temperature is fitted. The coefficient of the KL term is one by definition because `r_t` is already frozen on a standard-normal rank scale. Adding any constant to all candidate utilities leaves `q_t` unchanged.

## 3. Deterministic invariants

1. **Support preservation**: if `p_native,t(x)=0`, then `q_t(x)=0`.
2. **Pairwise log-odds correction**:
   `log(q_i/q_j) - log(p_i/p_j) = r_i-r_j`.
3. **Bounded correction**: finite normal ranks imply a finite score range, so the density ratio `q/p_native` is bounded by the exponential of that range.
4. **No causal double counting as Bayes**: `r_t` is a generalized utility, not a likelihood term. PRCA is a KL-proximal decision update.
5. **No temporal median in V14**: ACIT already rescored the complete retained evidence history at each identifiable update. The revealed H02 gate showed that adding a median over already-cumulative score states is redundant and can slightly worsen one stress case.

## 4. Cross-domain theoretical lineage

PRCA borrows **principles**, not formulas claimed as novel in their original fields.

- **Generalised variational inference under misspecification — ICML 2025 Spotlight, FedGVI.** FedGVI explicitly targets robustness to prior and likelihood misspecification and motivates generalized inference when exact Bayesian semantics are unsafe under model mismatch.
- **Consensus of dependent experts — ICML 2025, CoDE-VAE.** CoDE rejects the convenient independence assumption when aggregating correlated expert distributions. PRCA applies the same high-level lesson to even/odd causal evidence from one robot trajectory: they are dependent views and are combined conservatively rather than multiplied.
- **Reference-anchored KL-regularized optimization — ICLR 2026, Robust Multi-Objective Controlled Decoding; ICLR 2026, KL-Regularized Policy Gradient design.** These works treat a reference distribution/policy as an anchor and use KL-regularized improvement to prevent uncontrolled departure from that reference. The resulting best-response distributions are exponential tilts of the reference. PRCA transfers this proximal-update principle from policy optimization/controlled decoding to robotic source-state assimilation.
- **Robust aggregation — ICLR 2026, Robust Federated Inference.** This work formalizes that combining multiple model responses is itself a robustness problem and studies non-linear robust aggregation rather than naive averaging. PRCA similarly treats causal/native combination as an evidence-ownership problem instead of assuming all views should be fused symmetrically.
- **Tilted-risk robustness — ICML 2025.** Recent theory on tilted empirical risk provides generalization/robustness analysis for exponential tilting under heavy-tailed/noisy regimes. PRCA uses exponential tilting as a proximal distributional update, not as an empirical-risk estimator, so this is conceptual support rather than an equivalence claim.

## 5. Scientific claim boundary

Allowed if later closed-loop qualification succeeds:

> PRCA performs a native-anchored, replicated causal correction of the PMFS source state. The correction is a KL-proximal exponential tilt driven by a conservative lower envelope of dependent causal evidence views, preserving native support and avoiding source-state replacement under transport-model misspecification.

Do NOT claim:

- exact Bayesian likelihood fusion;
- independence of the even/odd views;
- a Pearl-style intervention theorem;
- that current ACIT transport geometry is physically exact;
- population-level generalization from revealed offline data;
- that the cross-domain papers above introduced PRCA for gas-source localization.

## 6. Frozen V14 development formula

`r_t(s) = min(z_even,t(s), z_odd,t(s))`

`q_t(x) = p_native,t(x) exp(r_t(s(x))) / Z_t`

No alpha, no temperature, no learned reliability, no House/seed parameter, no temporal median, and no planner change.
