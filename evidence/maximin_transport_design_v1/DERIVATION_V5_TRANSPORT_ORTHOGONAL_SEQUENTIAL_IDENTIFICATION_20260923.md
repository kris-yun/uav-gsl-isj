# M1 derivation v5 — Transport-Orthogonal Sequential Source Identification

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`  
Status: **current preferred main-method formulation; source-blind theory stage**

## 0. Main scientific thesis

The core problem is not merely "uncertain wind" and not merely "robust path planning."

It is:

> **source identity and transport misspecification can be observationally confounded.**

A nominal PMFS cell can have high between-source hit-map variance while that entire difference can be reproduced by a plausible change in transport. Such a cell is simulator-discriminative but not necessarily source-identifying.

The proposed principle is therefore:

> design a sequence of measurements so that source-hypothesis differences are **transverse / orthogonal to the transport-nuisance tangent space**.

This is the PMFS-specific transfer of the 2025–2026 semiparametric experimental-design idea that target information should be identified after orthogonalizing nuisance.

Parent ideas:
- Kim, Kim & Oh, *Experimental Design for Semiparametric Bandits*, COLT 2025.
- Kim, *Nearly Optimal Best Arm Identification for Semiparametric Bandits*, AISTATS 2026.
- Sloman et al., *Bayesian Active Learning in the Presence of Nuisance Parameters*, UAI 2024.
- Bartuska, Espath & Tempone, *Laplace-based strategies for Bayesian optimal experimental design with nuisance uncertainty*, Statistics and Computing 2025.

These are conceptual/theoretical parents, not direct algorithms for PMFS.

---

## 1. Local transport-response model

For source candidate \(s\), measurement location \(x\), and low-dimensional shared transport perturbation \(a\),

\[
h_s(x;a)
\approx
h_s(x;0)+g_s(x)^T a.
\]

For first falsification:
- \(a=[\delta u,\delta v]^T\), a global wind-drift perturbation;
- \(g_s(x)\) is estimated by common-random-number central finite differences of the official PMFS filament simulator.

No source truth is used.

---

## 2. Pairwise source difference under the same environment

For two source candidates \(s,r\),

\[
\Delta h_{sr}(x)
=
h_s(x;0)-h_r(x;0)
\]

and

\[
\Delta g_{sr}(x)
=
g_s(x)-g_r(x).
\]

Under one shared physical transport perturbation \(a\), their prediction difference becomes

\[
\Delta h_{sr}(x;a)
\approx
\Delta h_{sr}(x)+\Delta g_{sr}(x)^T a.
\]

This is crucial:

**nature gets one environment, not one independently chosen environment per source candidate.**

---

## 3. Why one measurement is insufficient

For a set of measurement locations \(B=\{x_1,\ldots,x_m\}\), define

\[
d_{sr,B}
=
[
\Delta h_{sr}(x_1),\ldots,\Delta h_{sr}(x_m)
]^T
\]

and nuisance Jacobian

\[
J_{sr,B}
=
\begin{bmatrix}
\Delta g_{sr}(x_1)^T\\
\vdots\\
\Delta g_{sr}(x_m)^T
\end{bmatrix}.
\]

The worst shared-nuisance pairwise discrepancy is

\[
D^\perp_{sr}(B)
=
\min_a
\|d_{sr,B}+J_{sr,B}a\|_2^2.
\]

It has the closed form

\[
\boxed{
D^\perp_{sr}(B)
=
d^T d
-
d^T J
(J^T J)^\dagger
J^T d
}
\]

or equivalently

\[
D^\perp_{sr}(B)=\|P^\perp_J d\|_2^2.
\]

Interpretation:

- \(d\): how the two source hypotheses differ over the chosen measurements;
- \(\operatorname{col}(J)\): how transport perturbation can change that difference;
- \(P^\perp_J d\): source distinction that transport cannot explain away to first order.

### Consequence

For one scalar measurement and a nonzero 1-D/2-D nuisance sensitivity, the nuisance can generally explain the scalar difference, so the unbounded orthogonalized information is zero.

With spatially diverse measurements, \(d\) may leave the nuisance span and become identifiable.

Therefore **deconfounding is intrinsically a multi-measurement / trajectory geometry problem**, not merely a per-cell reward replacement.

---

## 4. Exact connection to native PMFS variance

For one cell \(x\), PMFS uses

\[
V_{\rm PMFS}(x)
=
\operatorname{Var}_{s\sim\pi}[h_s(x)].
\]

Weighted variance has the identity

\[
\boxed{
\operatorname{Var}_{\pi}(h)
=
\frac12
\sum_{s,r}
\pi_s\pi_r
(h_s-h_r)^2.
}
\]

So native PMFS movement already measures posterior-weighted pairwise source separation, but **only under the nominal transport model**.

Define the transport-orthogonal accumulated identifiability

\[
\boxed{
\mathcal I_\perp(B)
=
\frac12
\sum_{s,r}
\pi_s\pi_r
D^\perp_{sr}(B).
}
\]

The next-cell acquisition is the marginal gain

\[
\boxed{
U_{\rm TO}(x\mid B)
=
\mathcal I_\perp(B\cup\{x\})
-
\mathcal I_\perp(B).
}
\]

This is the current preferred main acquisition quantity.

---

## 5. Required reduction theorem

If there is no transport nuisance effect,

\[
\Delta g_{sr}(x)=0
\quad\forall s,r,x,
\]

then

\[
D^\perp_{sr}(B)
=
\sum_{x\in B}
(\Delta h_{sr}(x))^2
\]

and therefore

\[
\mathcal I_\perp(B)
=
\sum_{x\in B}
\operatorname{Var}_{s\sim\pi}[h_s(x)].
\]

Hence

\[
\boxed{
U_{\rm TO}(x\mid B)
=
V_{\rm PMFS}(x).
}
\]

So the proposed criterion is not an unrelated new reward: it is a nuisance-orthogonal sequential generalization of the exact statistic PMFS already uses.

---

## 6. Monotonicity

For every source pair,

\[
D^\perp_{sr}(B\cup\{x\})
=
\min_a
\left[
\sum_{z\in B}
r_{sr}(z,a)^2
+
r_{sr}(x,a)^2
\right].
\]

Since the added term is nonnegative,

\[
D^\perp_{sr}(B\cup\{x\})
\ge
D^\perp_{sr}(B).
\]

Therefore

\[
\boxed{
U_{\rm TO}(x\mid B)\ge0.
}
\]

Adding a measurement cannot reduce accumulated transport-orthogonal pairwise identifiability.

Do **not** claim submodularity unless proven separately.

---

## 7. Sufficient statistics and computational cost

For each source pair maintain

\[
A_{sr}=\sum_{x\in B}\Delta g_{sr}(x)\Delta g_{sr}(x)^T,
\]

\[
b_{sr}=\sum_{x\in B}\Delta g_{sr}(x)\Delta h_{sr}(x),
\]

\[
c_{sr}=\sum_{x\in B}\Delta h_{sr}(x)^2.
\]

Then

\[
D^\perp_{sr}
=
c_{sr}-b_{sr}^T A_{sr}^\dagger b_{sr}.
\]

Adding a new cell is a rank-one update of \(A,b,c\).

For the first probe, nuisance dimension \(d=2\), so the inner linear algebra is tiny.

The naive all-pairs cost is \(O(S^2|\mathcal X|d^3)\), but posterior weights \(\pi_s\pi_r\) naturally make negligible pairs unimportant. Do not introduce an arbitrary top-K truncation before measuring runtime.

---

## 8. Relation to v4 single-cell NOSI

The v4 candidate-space score

\[
V_\perp
=
h^TCh
-
h^TCG(G^TCG)^\dagger G^TCh
\]

remains useful as a **source-blind diagnostic map of transport confounding**.

But v5 is preferred as the algorithmic formulation because:
- it respects the fact that source/transport deconfounding requires spatially diverse observations;
- it is history-aware;
- it has an exact reduction to native PMFS variance;
- it uses one shared transport perturbation over the whole measurement set;
- it exposes a direct pairwise source-identification geometry.

Use v4 \(V_\perp,\kappa_{\rm tr}\) diagnostically; use v5 \(U_{\rm TO}\) as the main first algorithmic candidate.

---

## 9. Connection to semiparametric experimental design

COLT 2025 studies experimental design when the target linear signal is accompanied by an unknown potentially adversarial shift and obtains guarantees through orthogonalized regression.

AISTATS 2026 studies fixed-confidence best-arm identification in the same semiparametric family and introduces an XY-design for orthogonalized regression.

The PMFS transfer is **not** to copy their additive reward model.

The transferable principle is:

> design measurements around the component of target discrimination that is orthogonal to nuisance variation.

Here:
- target = gas-source identity;
- nuisance = transport field / plume dynamics;
- arm/design = UAV measurement location;
- observation model = PMFS candidate hit probabilities;
- target discrimination = pairwise source hit-map difference;
- nuisance tangent = derivative of those differences with respect to shared transport perturbation.

---

## 10. Important novelty boundary: calibration nuisance in GSL

Jin et al., *Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking*, arXiv:2605.13208, 2026, removes a different nuisance: unknown nonlinear sensor calibration, using relative measurement rankings.

Therefore do not claim:
- first nuisance-invariant GSL;
- first method to eliminate a nuisance transformation in probabilistic GSL.

Our narrower distinction is:
- nuisance is **transport**, not sensor calibration;
- the mechanism is **local transport-tangent orthogonalization**;
- the acquisition is sequential and designed to break **source-vs-transport confounding**.

---

## 11. First falsification — TO-B0

Run only after Native PMFS recovery artifacts are available.

Start with one hit-bearing recovered case, then an independent plume realization.

### Inputs frozen before truth reveal

At each selected PMFS source update:
- current candidate source list;
- current candidate weights \(\pi\);
- current measurement history \(B_t\);
- nominal candidate hit maps;
- four common-random-number transport perturbation maps:
  \(+\epsilon u,-\epsilon u,+\epsilon v,-\epsilon v\).

### Source-blind calculations

1. finite-difference \(g_s(x)\);
2. native \(V_{\rm PMFS}(x)\);
3. v4 confounding ratio \(\kappa_{\rm tr}(x)\);
4. v5 marginal transport-orthogonal gain \(U_{\rm TO}(x|B_t)\).

Report before looking at truth:
- Spearman(native, TO);
- top-10/top-20 overlap;
- distribution of \(\kappa_{\rm tr}\);
- fraction of native top cells whose source separation is strongly transport-confounded;
- cross-realization stability;
- finite-difference epsilon consistency.

### Truth reveal / intervention

Replay equal-budget observation subsets selected by:
- Native PMFS variance;
- TO acquisition;
- random reachable control.

Keep the **same Native PMFS source update** in this first test.

Hard endpoint:
- truth-containing candidate rank.

Do not change inference and acquisition simultaneously.

---

## 12. Mechanism tests

### M0 — zero nuisance

Set all \(g_s=0\).

Required:
\[
U_{\rm TO}=V_{\rm PMFS}
\]
up to numerical tolerance.

### M1 — common-mode transport change

If all source candidates respond identically to transport, then \(\Delta g_{sr}=0\).

Required:
- no penalty relative to Native.

This proves the method does not simply punish "wind-sensitive" cells.

### M2 — source/transport collinearity

Construct a case where source differences lie exactly in the nuisance span.

Required:
- TO information collapses to zero.

### M3 — complementary measurements

Construct two cells where each scalar measurement is individually transport-confounded but the two-cell source-difference vector is not parallel to the nuisance vector.

Required:
- each one-cell orthogonalized separation is zero;
- the two-cell accumulated separation is positive.

This is the central active-deconfounding signature.

### M4 — destructive sensitivity shuffle

Preserve gradient norms but shuffle/rotate source-specific transport responses.

Any real-data advantage tied to physical source/transport geometry should be destroyed.

---

## 13. Kill criteria

Kill this line as the main innovation if:
- finite-difference transport sensitivities are not reproducible with common random numbers;
- repaired Native PMFS has negligible source/transport confounding in all independent cases;
- TO-selected observations do not improve truth-source rank;
- improvement only exists after tuning epsilon, history length, pair truncation, or other coefficients on truth;
- destructive null preserves the gain;
- the criterion simply reproduces a geometric-distance heuristic.

---

## 14. Current scientific narrative

A concise paper-level narrative, if the data support it:

> PMFS and related model-based GSL planners treat disagreement among simulated source hypotheses as information. We show that part of this disagreement can be generated by transport-model perturbations and is therefore not identifiable source information. Inspired by semiparametric experimental design, we decompose candidate disagreement into transport-confounded and transport-orthogonal components, and actively collect spatial measurements whose joint source signature cannot be reproduced by the transport nuisance. The native PMFS variance criterion appears as the zero-nuisance special case.

This is currently stronger than framing the work as "robust PMFS" or "DRO-PMFS."
