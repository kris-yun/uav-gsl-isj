# C0-C Matched-Capacity Learned Historical Pre-Screen

Date: 2026-09-23  
Branch: \`research/causal-compositional-plume-world-model-v1\`

## Decision

\`C0-C = NEUTRAL / HOLD\`

The historical 2×2 asset does **not** currently show a decisive advantage for a physically compositional source–wind representation over an equally sized monolithic representation.

This is a downgrade from “top lead” status until a stronger intervention/dense-field test says otherwise.

## 1. Dataset

Same verified controlled asset:

- 3 Houses;
- 2 source interventions;
- 2 transport conditions;
- identical route/timing within a House;
- source-invariant wind sequence within each fast/slow condition.

At 240 s each history is averaged onto the PMFS 0.3-m grid.

Target:

\[
y=\log(1+c).
\]

Cross-validation:

- hold out one source×wind combination;
- train on the other three;
- repeat all 4 folds × 3 Houses = 12 held-out cases.

## 2. Capacity-matched representations

Both models use:
- 6 base variables;
- complete degree-2 polynomial expansion;
- exactly 28 regression features;
- the same ridge solver and regularization;
- the same training samples.

### Monolithic representation

Base variables:

\[
[x,y,s_x,s_y,u,v].
\]

No explicit physical source–wind coordinate transformation.

### Physics-compositional representation

For query location \(x\), source \(s\), local wind \(w\):

\[
d_{\parallel}
=
(x-s)\cdot \hat w,
\]

\[
d_{\perp}
=
(x-s)\times \hat w,
\]

\[
r=\|x-s\|,
\qquad
v=\|w\|.
\]

Base variables:

\[
[x,y,d_{\parallel},d_{\perp},r,v].
\]

This explicitly composes source position and wind into wind-relative transport coordinates.

## 3. Ridge sensitivity panel

Predeclared values:

\[
\lambda\in
\{10^{-4},10^{-3},10^{-2},10^{-1}\}.
\]

No value is selected using source truth.

## 4. Source-identification result

For every lambda:

- monolithic: **12/12 correct source identities**;
- compositional: **12/12 correct source identities**.

At \(\lambda=10^{-3}\):

- monolithic mean source-margin ≈ **0.088261**;
- compositional mean source-margin ≈ **0.089052**.

The difference is small and not a convincing main-method signal.

### House pattern

Mean margin at \(\lambda=10^{-3}\):

| House | monolithic | compositional |
|---|---:|---:|
| H01 | 0.001998 | 0.003315 |
| H02 | 0.126758 | 0.090187 |
| H03 | 0.136026 | 0.173655 |

Thus:
- H01 favors compositional mildly;
- H03 favors compositional;
- H02 favors monolithic substantially.

No uniform advantage exists.

The same qualitative pattern persists across the ridge sensitivity panel.

## 5. Interpretation

This test is more permissive than the zero-training additive test because both representations learn a nonlinear quadratic mapping.

It establishes:

> a physically wind-relative coordinate system is sufficient for source identification on the historical held-out source×wind combinations.

But it does **not** establish:

> causal/operator compositional representation is superior to an ordinary matched-capacity model.

Therefore M4 currently lacks the differentiating empirical signal required for a paper-level main thesis.

## 6. What this does and does not kill

### Rejected as evidence

- “compositional coordinates obviously generalize better”;
- “the historical 2×2 data already validates causal modularity”;
- any claim that M4 is ready for full implementation.

### Still open

A true operator model:

\[
C=\mathcal T_{W,O}(Q_S)
\]

may still outperform a monolithic learned field model when:
- dense plume fields are used;
- more than two sources/winds are available;
- unseen source positions must be interpolated/extrapolated;
- cross-House geometry generalization is tested.

Those are materially stronger tests than this 2-source fixed-route regression.

## 7. Resource decision

Do not make M4 the sole main-innovation bet now.

Priority should shift toward candidates that have a distinct empirical/interface advantage before large data generation.

M4 remains:

\`HOLD — STRONG SCIENTIFIC NARRATIVE, NO CURRENT COMPARATIVE PERFORMANCE SIGNAL\`.

A new 2×2/4×2 dense-field intervention dataset may revisit it, but only after higher-priority candidates are screened.
