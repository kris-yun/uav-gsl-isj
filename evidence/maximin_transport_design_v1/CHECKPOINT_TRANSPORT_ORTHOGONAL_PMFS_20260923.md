# CHECKPOINT — Transport-Orthogonal PMFS Main-Innovation Search

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`

## 1. Current status

This branch started from a generic maximin / distributionally robust experimental-design idea, but several novelty collisions forced a progressively narrower and stronger formulation.

### V1 — Maximin robust information
Initial idea:
- robust Bayesian experimental design;
- Sibson/Rényi information under likelihood misspecification.

**Demoted.**

Reason:
- 2025 Rényi-infotaxis / Rényi information already exists in OSL;
- generic robust OED and robust sensor placement are established;
- would risk becoming “replace PMFS reward with another information metric.”

### V2 — Transition-Ambiguous PMFS
Key move:
- put uncertainty on PMFS's actual stochastic filament transition law;
- derive local KL radius from wind-drift mismatch.

For official PMFS filament dynamics

\[
X_{k+1}=X_k+\Delta t [w(X_k)+\epsilon_k],
\qquad
\epsilon_k\sim N(0,\sigma^2I),
\]

a drift error \(\delta w\) gives

\[
D_{KL}(P_{w+\delta w}\Vert P_w)
=
\frac{\|\delta w\|^2}{2\sigma^2}.
\]

Thus ambiguity has a physical wind-error interpretation.

**Kept as theoretical foundation.**

### V3 — Shared Adversarial Transport Identifiability (SATI)
Instead of allowing an independent worst-case hit probability for every source candidate, all source hypotheses share the same physical transport perturbation \(a\):

\[
h_s(x;a)\approx h_s(x)+g_s(x)^Ta.
\]

Define

\[
V_{\rm SATI}(x)
=
\min_{\|a\|\le r}
\operatorname{Var}_{s\sim\pi}
[h_s(x)+g_s(x)^Ta].
\]

This is a convex trust-region problem.

**Kept as finite-radius robustness extension.**

### V4 — Nuisance-Orthogonal Source Information
Remove the component of candidate-source disagreement explainable by transport nuisance:

\[
V_\perp
=
h^TCh-h^TCG(G^TCG)^\dagger G^TCh.
\]

Transport confounding ratio:

\[
\kappa_{\rm tr}
=
\frac{V_0-V_\perp}{V_0}.
\]

Interpretation:
- \(\kappa\approx0\): source discrimination is transport-orthogonal;
- \(\kappa\approx1\): nominal PMFS candidate variance can almost entirely be explained by transport change.

**Kept as source-blind diagnostic.**

### V5 — Transport-Orthogonal Sequential Source Identification
Current preferred main formulation.

For source pair \(s,r\), over measurement history \(B\):

\[
d_{sr,B}
=
[
h_s(x)-h_r(x)
]_{x\in B},
\]

\[
J_{sr,B}
=
[
g_s(x)-g_r(x)
]_{x\in B}.
\]

Define pairwise transport-orthogonal separation:

\[
D^\perp_{sr}(B)
=
\min_a
\|d_{sr,B}+J_{sr,B}a\|^2
=
\|P^\perp_J d\|^2.
\]

Posterior-weighted accumulated identifiability:

\[
\mathcal I_\perp(B)
=
\frac12
\sum_{s,r}\pi_s\pi_rD^\perp_{sr}(B).
\]

Next-cell utility:

\[
U_{\rm TO}(x|B)
=
\mathcal I_\perp(B\cup\{x\})
-
\mathcal I_\perp(B).
\]

### Required reduction

When transport nuisance is zero:

\[
U_{\rm TO}(x|B)
=
\operatorname{Var}_{s\sim\pi}[h_s(x)],
\]

so V5 reduces exactly to the statistic used by native PMFS movement.

**This is the current lead candidate.**

---

## 2. Why V5 is scientifically stronger

The intended paper-level problem is no longer generic “robust PMFS.”

It is:

> **transport-confounded source information:** disagreement among candidate plume simulations is not necessarily source information because plausible transport perturbations can produce the same disagreement.

The proposed solution is:

> actively collect complementary spatial observations whose joint source signature has a component orthogonal to the transport-nuisance tangent space.

This explains the previously observed empirical pathology:

- nominal PMFS candidate-variance maps were highly stable across simulator seeds;
- nevertheless selecting high-variance cells often worsened truth-source candidate rank.

Stability of self-discrimination is therefore not enough; the source signal must be identifiable independently of transport nuisance.

---

## 3. Hard novelty boundaries already found

Do NOT claim any of these as novel:

- robust / worst-case OED;
- sequential OED;
- active model discrimination;
- model discrimination with nuisance parameters;
- DRO gas sensor placement under wind uncertainty;
- multiple wrong plume-model ensembles for OSL;
- Rényi information / Rényi-infotaxis for OSL;
- nuisance-invariant GSL in general;
- joint inference of source and physical parameters in general.

Relevant collisions include:

1. Zi et al., IEEE Sensors Journal 2022 — DRO fixed methane sensor placement under wind uncertainty.
2. Piro et al., Journal of Turbulence 2025 — “many wrong models” odor-source localization.
3. Jia et al., Entropy 2025 — Rényi-based odor-source exploration.
4. Shen, Dong & Huan, CMAME 2025 — sequential OED with nuisance parameters and multiple models/model discrimination.
5. Niu, Shen & Yong, Automatica 2026 — multi-stage active model discrimination under bounded uncertainty.
6. Jin et al., arXiv 2026 — calibration-free GSL removing a sensor-response nuisance.

The defensible novelty must remain at the PMFS-specific interface:
- stochastic filament transport;
- transport tangent / sensitivity of candidate hit maps;
- source-vs-transport confounding;
- sequential spatial deconfounding;
- exact reduction to native PMFS variance.

---

## 4. Remote-field parent ideas

Useful parent concepts, not direct algorithm transfers:

- semiparametric experimental design / orthogonalized regression:
  - Kim, Kim & Oh, COLT 2025;
  - Kim, AISTATS 2026.
- active learning with nuisance parameters:
  - Sloman et al., UAI 2024.
- Bayesian OED with nuisance uncertainty:
  - Bartuska, Espath & Tempone, Statistics and Computing 2025.
- distributionally robust transition models:
  - Shafiei et al., Nature Communications 2025;
  - Li & Shapiro, Mathematical Programming 2025.

Important restriction:
the AISTATS/COLT semiparametric-bandit XY-design is **not directly transferable** to PMFS because PMFS is a nonlinear stochastic simulator over discrete source hypotheses, not their linear semiparametric reward model.

---

## 5. Existing source-blind code on this branch

- \`probe_gsi_f0.py\`
  - interval robust-variance algebra;
  - point intervals reduce to native variance;
  - common-overlap intervals collapse guaranteed variance to zero.

- \`probe_sati_f0.py\`
  - shared-adversarial transport trust-region solver;
  - parameter-free nuisance-orthogonal source-variance diagnostic.

- \`probe_transport_orthogonal_sequential_f0.py\`
  - V5 sequential orthogonalized pairwise-identifiability algebra.

F0 properties already encoded:

1. zero nuisance -> exactly native PMFS variance;
2. common-mode transport shift -> no false penalty;
3. source signal entirely in nuisance span -> zero orthogonal information;
4. two individually confounded measurements can become jointly source-identifying;
5. accumulated orthogonal identifiability is monotone with added measurements.

---

## 6. Current unresolved scientific bottleneck

Before touching the repaired House data, the remaining question is:

> Under controlled PMFS-like stochastic transport with deliberate forward-model wind mismatch, does V5 choose complementary measurements that improve source identity relative to native candidate variance?

This can be falsified without the old R2 baseline and without waiting for Codex.

---

## 7. Immediate next experiment — TOY-B0

Build a minimal 2-D drift-diffusion / filament-inspired synthetic environment with:

- multiple discrete source candidates;
- nominal wind used by planner;
- different true wind used by observation generator;
- binary or hit-frequency observations;
- source posterior update fixed and identical across methods;
- equal measurement budget.

Compare:
1. native PMFS candidate variance;
2. V5 transport-orthogonal marginal gain;
3. random reachable control.

Run multiple independent true plume realizations.

Primary metric:
- truth-source candidate rank after equal observations.

Mechanism checks:
- matched-wind regime should make V5 approach native;
- moderate mismatch should favor V5 if mechanism is correct;
- source/transport sensitivity shuffle should destroy V5 advantage;
- no parameter tuning on truth.

If TOY-B0 cannot produce the expected mechanism under a deliberately controlled source/transport confounding setup, **kill or redesign V5 before using House data.**

---

## 8. Branch checkpoint commits prior to this file

- \`dd1d441210ab606509f4c3a717f6cc8a56d9b2aa\` — initial adversarial transport candidate.
- \`f5f242bdfe4f4d20b1beb2def9c98c1783e4fff6\` — many-wrong-models novelty collision.
- \`437c6e4886b426efc4fa1b59c4d7e66805131a79\` — Rényi-infotaxis collision.
- \`5cbf435bc6b40a05adbbbcf1e7df7b4a66d72af2\` — transition-ambiguous PMFS derivation.
- \`7d7ff19c8b9a24cab97d7ae8454001f613e09998\` — GSI F0 probe.
- \`b334ae928af4623e27bb51eed3faf6522644f0d6\` — shared adversarial transport derivation.
- \`f969bc0a8e7c0f14f04063ac2ca7394769e10298\` — SATI trust-region probe.
- \`722ffd8137e13679fb785f4c9873a65cc87e661a\` — nuisance-orthogonal source-information derivation.
- \`79014c9a94db6a6b4a0d37eabcc160ef03cc275a\` — parameter-free NOSI probe.
- \`e7f1ec958c738d605db5a0ae4ff71735205260b0\` — V5 sequential transport-orthogonal derivation.
- \`da27eb3c28d14c27d81c64388e9ecdeee123e149\` — V5 F0 algebra probe.
- \`d34cf17a23f084eeb2ecf4bcf7e978c50a6eef17\` — novelty audit v2.

---

## 9. Current decision

**Do not promote V5 to the final main innovation yet.**

Status:

\`KEEP — STRONG CANDIDATE, PENDING CONTROLLED MECHANISM FALSIFICATION + REPAIRED NATIVE HOUSE TEST\`
