# M1 derivation v3 — Shared Adversarial Transport Identifiability (SATI)

Date: 2026-09-23  
Status: **preferred first falsification form**

## 1. Why v3

The v2 interval objective

\[
\min_{q_s\in[\underline h_s,\overline h_s]}\operatorname{Var}_\pi(q_s)
\]

is useful as a conservative bound, but it allows nature to choose a different effective prediction for each source candidate independently.

That can be too pessimistic: the physical world has one transport field shared by every source hypothesis.

The stronger formulation couples all candidates through the **same adversarial transport perturbation**.

## 2. Shared transport nuisance

Let \(a\) parameterize a physically admissible perturbation of the nominal PMFS wind/transport field.

For the first falsification, use only a global 2-D drift bias:

\[
w_a(x)=w_0(x)+a,
\qquad
a=[\delta u,\delta v]^T.
\]

The admissible set is

\[
\|a\|_2\le r_w.
\]

For PMFS Gaussian filament velocity noise \(\sigma\), this corresponds to a local KL radius

\[
\eta=\frac{r_w^2}{2\sigma^2}.
\]

Do not tune \(r_w\) on source truth.

Later versions may replace global bias with a source-blind low-rank spatial wind-error basis, but do not start there.

## 3. Linear-response hit model

For source candidate \(s\) and potential observation cell \(x\),

\[
h_s(x;a)
\approx
h_s(x;0)+g_s(x)^Ta
\]

where

\[
g_s(x)
=
\nabla_a h_s(x;a)|_{a=0}.
\]

### First implementation

Estimate \(g_s\) by common-random-number central finite differences:

\[
g_{s,u}(x)
\approx
\frac{h_s(x;+\epsilon e_u)-h_s(x;-\epsilon e_u)}{2\epsilon},
\]

\[
g_{s,v}(x)
\approx
\frac{h_s(x;+\epsilon e_v)-h_s(x;-\epsilon e_v)}{2\epsilon}.
\]

Requirements:

- same simulator seeds for plus/minus perturbations;
- \(\epsilon\) fixed before truth evaluation;
- verify linearity with a second smaller/larger epsilon source-blind.

A later efficiency upgrade can use likelihood-ratio / score-function sensitivity from nominal Gaussian filament trajectories; it is not required for the first gate.

## 4. Shared Adversarial Transport Identifiability

Let source weights be the current normalized PMFS candidate probabilities \(w_s\).

Native PMFS movement informativeness is

\[
V_0(x)=\operatorname{Var}_{s\sim w}[h_s(x)].
\]

Define

\[
\boxed{
V_{\rm SATI}(x)
=
\min_{\|a\|_2\le r_w}
\operatorname{Var}_{s\sim w}
[h_s(x)+g_s(x)^Ta]
}
\]

Interpretation:

> Choose positions where no single physically admissible shared wind bias can make the currently plausible source hypotheses look alike.

This is not:
- another entropy;
- another Rényi coefficient;
- a bank of hand-picked plume models;
- an independent uncertainty interval per source.

It is an explicit source-identifiability game against a shared transport nuisance.

## 5. Quadratic form

Let

- \(h\in\mathbb R^S\): nominal candidate hit predictions at one cell;
- \(G\in\mathbb R^{S\times d}\): transport sensitivities;
- \(w\in\Delta^{S-1}\);
- \(C=\operatorname{diag}(w)-ww^T\).

Then

\[
\operatorname{Var}_w(h+Ga)
=
(h+Ga)^TC(h+Ga).
\]

Expand:

\[
V(a)
=
a^TAa+2b^Ta+c
\]

with

\[
A=G^TCG\succeq0,
\qquad
b=G^TCh,
\qquad
c=h^TCh.
\]

Therefore SATI solves the convex trust-region problem

\[
\min_{\|a\|_2\le r_w}
a^TAa+2b^Ta+c.
\]

If the unconstrained solution

\[
a_0=-A^\dagger b
\]

lies inside the ball, it is optimal.

Otherwise,

\[
a^\star(\lambda)
=
-(A+\lambda I)^{-1}b,
\]

where \(\lambda>0\) is the unique value satisfying

\[
\|a^\star(\lambda)\|_2=r_w.
\]

Thus the adversary costs only a tiny matrix solve plus a scalar root search per observation cell.

For the first probe \(d=2\).

## 6. Important signatures

### S1 — matched model

If \(r_w=0\),

\[
V_{\rm SATI}=V_0.
\]

### S2 — transport-fragile nominal information

If a small shared wind bias can align candidate predictions,

\[
V_{\rm SATI}\ll V_0.
\]

These are exactly the cells that native PMFS may incorrectly consider informative.

### S3 — transport-invariant source information

If all candidates respond similarly to wind bias, i.e. their sensitivity vectors are nearly equal, then common transport perturbations shift predictions together and cannot erase their relative separation.

Such a cell can retain high SATI even when absolute hit probabilities move substantially.

This is an important distinction from generic uncertainty penalties: SATI penalizes **confounding of source identity by transport**, not uncertainty magnitude by itself.

## 7. Why SATI is stronger than "robust sensor placement"

A fixed methane detector DRO problem can hedge detection time across wind scenarios without reasoning about source-hypothesis confounding.

SATI instead asks a different inverse-problem question:

> Can a plausible change in transport make *different source locations observationally equivalent* at the next mobile measurement?

That source-vs-transport confounding is the scientific target.

## 8. First falsification — SATI-B0

Run only after the Native PMFS recovery artifacts are available.

Start with one hit-bearing case, preferably House02 seed0, then one independent realization before expanding.

For every frozen PMFS source update:

1. preserve exact current candidate sources and source weights;
2. generate nominal candidate hit maps;
3. generate four common-random-number maps:
   - \(+\epsilon u\);
   - \(-\epsilon u\);
   - \(+\epsilon v\);
   - \(-\epsilon v\);
4. estimate \(g_s(x)\);
5. compute:
   - native variance \(V_0(x)\);
   - SATI for a predeclared source-blind radius panel;
6. select the same number of candidate observation cells under each criterion;
7. replay real/frozen observations from those cells;
8. update source probability with the **same Native PMFS source-update rule**.

Hard endpoint:

- truth-containing candidate rank.

Do not change the inference rule in B0. This isolates the value of robust measurement selection.

## 9. Radius rule for B0

Do not pick the best radius after truth is revealed.

Preferred order:

1. estimate a wind-error scale from source-blind measured-vs-model wind residuals if available;
2. convert to KL via \(r_w^2/(2\sigma^2)\);
3. additionally report a small predeclared sensitivity panel around that estimate;
4. label the whole panel diagnostic unless a source-blind calibration rule is fixed.

## 10. Destructive controls

### N1 — candidate-label shuffle

Shuffle candidate labels in the sensitivity tensor while preserving nominal hit maps.

SATI advantage should collapse if source-transport coupling is causal to the gain.

### N2 — sensitivity rotation/permutation

Preserve gradient norms but destroy the shared directional relation between candidates.

If SATI still performs equally, it is likely just an uncertainty penalty.

### N3 — zero-radius

Must exactly recover native variance ranking up to ties/numerics.

## 11. Kill conditions

Kill SATI as main innovation if any holds:

- source rank does not improve over native variance on independent realizations;
- positive results require choosing radius with source truth;
- only very large, physically implausible wind perturbations change the selection;
- sensitivity finite differences are dominated by Monte Carlo noise despite common random numbers;
- gain survives candidate/sensitivity destructive nulls;
- repaired Native PMFS eliminates the effect entirely in every mismatch test.

## 12. If B0 is positive

Only then extend \(a\) from a global 2-D bias to a low-dimensional spatial transport field

\[
\delta w(x)=B(x)a
\]

with a source-blind uncertainty ellipsoid.

The final method should keep the same shared-adversary principle and SATI objective; the richer basis is an implementation refinement, not a new claimed idea.
