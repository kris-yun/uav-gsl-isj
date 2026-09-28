# MPDI v0 — Marginal-Preserving Dependence Inference
## D0 mechanism preregistration — 2026-09-28

**Branch:** `research/marginal-preserving-dependence-v0-20260928`  
**Base:** `47e2934c0c7fa34977ff5cd794c663403810868c`  
**Status:** `D0_PREREG_ONLY / OPEN_READ_ONLY / NO_NEW_PLUME / NO_VGR`

## 1. Why this branch exists

The project now has four hard constraints that must be respected simultaneously:

1. **AOD is a real but heterogeneous readout signal.** Removing the amplitude-channel blur can improve exact unique source identification on the frozen fresh House03 full-support panel, but it does not improve the complete candidate ordering globally.
2. **Better predictive fit is not enough.** The stopped AOD conditional-filter line improved observation predictive density while producing poor source identification.
3. **Better model confidence / separability is not enough.** BRG could become confidently wrong, and HD-PLF v0 showed that a model-only template-separation action score is not a stable cross-House predictor of realized B2 source-identification gain.
4. **Global invariance is false.** The stopped `realization-invariant-source-signature-v0` D3 showed that absolute plume mass is nuisance-dominated in some source regions but source-discriminative in others. Therefore the next route must not globally remove amplitude, morphology, memory, or any other observable component.

The next scientific question is therefore not “which information should be deleted?” but:

> **Can robust marginal source evidence be preserved exactly while modelling only the additional source-conditioned dependence that is lost when realization pairing is destroyed?**

This is deliberately different from TNQC/global canonicalization, MZ global normalization, causal-compositional M4, BRG, and HD-PLF v0.

## 2. Mother theory and transfer

### 2.1 Primary 2026 mother paper

David Huk and Theodoros Damoulas, **“Diffusion and Flow-based Copulas: Forgetting and Remembering Dependencies,” ICLR 2026**.

Official proceedings:
https://proceedings.iclr.cc/paper_files/paper/2026/hash/41ca8a0eb2bc4927a499b910934b9b81-Abstract-Conference.html

Code:
https://github.com/Huk-David/Diffusion-and-Flow-based-Copulas

The transferable principle is not “use a copula because it is new.” It is the stronger construction:

> **forget dependence while leaving marginals unchanged, then learn only the missing dependence.**

### 2.2 Minimal 2025 estimator anchor

David Huk, Mark Steel, Ritabrata Dutta, **“Your copula is a classifier in disguise: classification-based copula density estimation,” AISTATS 2025**.

Proceedings:
https://proceedings.mlr.press/v258/huk25a.html

Code:
https://github.com/Huk-David/Ratio-Copula

This supplies a practical density-ratio interpretation: distinguish samples from a joint law from samples drawn from an independence / dependence-destroyed reference law.

### 2.3 Important discrete-data boundary

The current encounter representation is binary. Classical uniqueness claims for continuous copulas must **not** be transferred carelessly to Bernoulli trajectories.

For D0 we therefore use the safer object:

[
R_s(y)=S(Q_s,y)-S(P_s,y),
]

where:
- (P_s) is the intact source-conditioned trajectory ensemble;
- (Q_s) is a **marginal-preserving dependence-destroyed null**;
- (S) is the same fair empirical Energy Score.

This is a dependency-residual diagnostic. It does not claim a unique Bernoulli copula.

## 3. Existing evidence that motivates D0

The already-frozen OPEN dependence work established that cross-time realization pairing can carry source identity under an 18-source development panel. The strongest current baseline, however, is the complete marginal encounter field; a joint score is not allowed to replace that strong marginal evidence.

The new route therefore obeys:

[
oxed{	ext{marginal evidence stays; dependence is only an incremental residual}}
]

No global normalization, no source-independent nuisance deletion, and no action policy are introduced in D0.

## 4. D0 input contract

Use only the already OPEN 18-source / 16-realization stochastic benchmark assets used by `DEPENDENCE_LAYER_D0_V2` and the complete 300-D full-field reanalysis.

No:
- new GADEN plume;
- new PMFS forward;
- House03 AOD target;
- ROS/VGR execution;
- neural network training;
- source/probe/time selection after seeing results.

Reproduce the archived source axis, realization splits, binary pooling and hashes before scoring.

Primary directed splits remain:
- A: refs 1..8, targets 9..16;
- B: refs 9..16, targets 1..8.

Robustness remains:
- C: odd refs, even targets;
- D: even refs, odd targets.

These are cross-fit directions, not independent scientific replications.

## 5. Two dependency nulls

For candidate source (s), each realization is a binary tensor (Yin{0,1}^{10	imes30}).

### Q-time — primary

Within source and each time (t), permute the intact 30-D snapshots across reference realizations independently for each (t), then concatenate times.

This preserves:
- the complete empirical 30-D snapshot distribution at every time;
- every 300 coordinate marginal;
- hit counts and support at every time.

It destroys:
- which time snapshots belong to the same plume realization.

This is the existing C2 semantics and isolates **cross-time dependence**.

### Q-coordinate — secondary diagnostic only

Independently permute each of the 300 binary coordinates across reference realizations.

This preserves each univariate Bernoulli marginal but destroys within-time spatial and cross-time dependence.

It diagnoses total dependence beyond the complete marginal field. It is not allowed to replace the primary Q-time interpretation.

Use exactly 500 surrogate banks with a new fixed RNG seed chosen and committed before execution.

## 6. Dependency-residual score

For candidate (s), target (y):

[
ES(P_s,y)
=
rac1Ksum_i|X_i-y|
-
rac{1}{2K(K-1)}
sum_{i
e j}|X_i-X_j|.
]

For each dependence-destroyed surrogate (Q_s^{(b)}), compute the same fair U-statistic score.

Define:

[
R_s(y)
=
operatorname{median}_{b=1}^{500}
left[
ES(Q_s^{(b)},y)-ES(P_s,y)
ight].
]

Higher (R_s) means the target resembles the intact source-conditioned dependence more than the dependence-destroyed version **for that same candidate**.

No coefficient is fit.  
No (R_s) is added to Brier in D0.  
No posterior is created in D0.

## 7. What D0 actually tests

For every target, first compute the frozen complete 300-D marginal-Brier ranking (M_0).

Then evaluate the dependency residual separately.

### 7.1 Residual source rank

Rank all source candidates by descending (R_s(y)).

Report:
- truth-source rank;
- unique Top1 / Top3;
- MRR;
- source-averaged mean rank.

This answers whether dependence residual by itself contains source identity.

### 7.2 Incremental pair diagnostic against the strong marginal baseline

Let (c(y)) be the strongest wrong candidate under frozen marginal Brier.

Define:

[
G_D(y)=R_{s_*}(y)-R_{c(y)}(y).
]

Report separately:

- **M0-error targets:** fraction with (G_D>0).  
  This asks whether dependence points toward the truth when the marginal baseline is wrong.

- **M0-correct targets:** fraction with (G_D>0).  
  This checks whether the dependence signal is broadly compatible with an already-correct marginal decision rather than systematically opposing it.

Aggregate first within source, then across sources. Also report the two fixed source halves already used by the full-field dependence work.

### 7.3 Destructive controls

Run:
1. candidate/source labels permuted for (R_s);
2. intact-reference realization pairing replaced by Q-time before forming “intact” score;
3. target time order permuted as a diagnostic only.

A true source-conditioned dependence residual should lose its source-ranking advantage under controls 1 and 2.

## 8. Frozen D0 decision

### `MPDI_D0_ADVANCE_DEPENDENCE_RESIDUAL`

All must hold on primary A+B:
1. truth residual rank is better than its source-label-permuted null distribution;
2. both fixed source halves show the same direction;
3. among M0-error targets, source-averaged fraction (G_D>0) is > 0.5;
4. among M0-correct targets, source-averaged fraction (G_D>0) is >= 0.5;
5. the benefit is not attributable to one source only;
6. Q-time destructive control removes the advantage;
7. robustness C+D does not reverse the direction.

This licenses D1 only. It does **not** license VGR or a diffusion model.

### `MPDI_D0_DEPENDENCE_PRESENT_NOT_INCREMENTAL`

Residual source identity exists, but conditions 3–5 fail.

Interpretation: dependence is real but does not currently supply useful incremental evidence beyond the strong marginal source field. Stop the mainline rather than building a larger model.

### `MPDI_D0_NO_SOURCE_DEPENDENCE_SIGNAL`

Residual source rank does not beat the destructive null consistently.

Stop.

### `MPDI_D0_HOLD_INFRASTRUCTURE`

Only for asset/hash/schema/parity failures.

## 9. D1 only if D0 advances

Do **not** begin D1 until D0 is frozen.

If D0 advances, D1 may implement a proper additive factorization:

[
log p_s(y)=log q_s(y)+log r_s(y),
]

where (q_s) is an explicitly defined marginal/reference likelihood and (r_s) is a learned dependency density ratio.

At that stage the 2025 classifier-ratio method is the first implementation candidate. The ICLR 2026 diffusion/flow copula is considered only if the simple ratio estimator cannot represent the confirmed dependency residual.

There must be no tuned mixing coefficient between marginal and dependence terms if the claim is a probability factorization.

## 10. Relationship to AOD

AOD remains frozen as a **separate positive readout result**.

D0 uses binary encounter trajectories because that is the existing dependence bank. It does not use AOD or claim that AOD is irrelevant.

If MPDI survives independently, a later auxiliary study may ask whether amplitude-channel AOD supplies additional marginal/detail evidence. Do not combine AOD with MPDI before the dependence mechanism itself passes.

## 11. Novelty boundary

Do not claim:
- first use of temporal dependence in olfaction;
- first copula in all gas sensing;
- first stochastic source inference;
- first use of diffusion in GSL.

The candidate contribution, if later confirmed, is narrower:

> **PMFS-style source inference in which robust source-conditioned marginal evidence is preserved while a separately identified, marginal-preserving stochastic dependency residual contributes only information that disappears under dependence-destroying interventions.**

A final direct GSL prior-art audit remains mandatory before paper-level novelty language.

## 12. Immediate execution instruction

Implement only a read-only D0 evaluator on the frozen OPEN bank.

Required outputs:
- exact asset/hash manifest;
- reproduction of archived marginal-Brier and intact/C2 reference metrics;
- candidate-wise (R_s(y));
- per-target truth residual rank;
- (G_D) against the marginal-Brier strongest wrong candidate;
- source-level and fixed-half aggregates;
- three destructive controls;
- deterministic repeat hash;
- one decision label from Section 8.

**STOP after D0. Do not connect to PMFS/ROS/VGR and do not tune from D0 outcome.**
