# M5 Theory Note — Boundary Constraints Create Non-Gaussian Lagrangian Transitions

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## 1. Core mechanism

Even if the unconstrained filament perturbation is Gaussian, obstacle handling can make the **realized transition law non-Gaussian**.

This matters because:

- Native PMFS uses Gaussian velocity perturbation plus stop-before-wall behavior.
- GADEN uses Gaussian perturbation followed by recursive obstacle deflection / tangential projection.

Thus the difference between the two models is not only a different mean trajectory.

It can change the **shape/support of the transition distribution**.

## 2. Local flat-wall derivation

Let the free region be one side of a locally flat wall.

Let:
- \(n\): wall normal;
- \(P_T=I-nn^T\): tangent projector;
- \(d>0\): current normal distance to the wall;
- proposed displacement:
  \[
  D\sim\mathcal N(\mu,\Sigma).
  \]

Ignoring finite-cell discretization for the local argument, split proposals into:

### No collision

\[
n^TD>-d.
\]

The displacement remains approximately:

\[
D'=D.
\]

### Collision

\[
n^TD\le-d.
\]

A GADEN-like deflection removes the blocked normal remainder and preserves tangential motion.

Locally:

\[
D'
\approx
-dn
+
P_TD
\]

for the wall-contact/slide part.

Therefore:

\[
P(D')
=
P(\text{no collision})P(D'\mid no\ collision)
+
P(\text{collision})P(D'\mid collision).
\]

The collision branch lives on or near a lower-dimensional tangential constraint set.

It is not a full-dimensional Gaussian.

## 3. Consequences

### C1 — singular/mixed support

The realized distribution contains:
- an unconstrained free-space branch;
- a wall-constrained/tangential branch.

A single Gaussian cannot represent a finite probability mass concentrated on the boundary manifold.

### C2 — skew/heavy tails

Clipping/projection of the normal component creates strong asymmetric statistics near a wall.

### C3 — corners create multiple modes

Near a corner or doorway, distinct proposal directions can produce:
- free-space motion;
- slide along wall A;
- slide along wall B;
- corner/contact behavior.

This naturally produces multimodal constrained trajectory futures.

### C4 — open space remains simple

Far from obstacles, the constraint is inactive and the same transition can remain close to Gaussian.

Therefore M5 should not apply a large generative model uniformly.

## 4. Minimal synthetic F0

A local 2-D flat-wall unit test was evaluated with:

- wall at \(x=0\), free region \(x>0\);
- current wall distance \(d=0.02\) m;
- mean proposed displacement:
  \[
  \mu=(-0.03,\;0.02)\ {\rm m};
  \]
- isotropic displacement std:
  \[
  \sigma=0.02\ {\rm m};
  \]
- 500,000 proposals.

Local wall projection sets the normal endpoint to the wall on collision while preserving tangential displacement.

Observed:

- collision/deflection fraction: **0.6907**;
- normal-coordinate skewness: **2.585**;
- normal-coordinate excess kurtosis: **7.275**.

A moment-matched continuous Gaussian assigns zero exact mass to the wall manifold and cannot represent the projected branch.

This is a **mechanism unit test only**.

It is not House/GADEN evidence.

## 5. Revised M5 architecture hypothesis

Use a hybrid transport law.

### Open-space regime

Keep an analytic/simple stochastic law:

\[
X_{t+\Delta}
=
X_t+W(X_t)\Delta+\epsilon,
\qquad
\epsilon\sim\mathcal N(0,\Sigma).
\]

### Constraint-active regime

Use a physics-conditioned generative residual / constrained trajectory model only when:
- wall distance is small relative to displacement uncertainty;
- obstacle/corner interaction is likely;
- local transport residual is demonstrably non-Gaussian in L1.

Conceptually:

\[
P(X_{t+\Delta}\mid z)
=
(1-\rho(z))P_{\rm free}
+
\rho(z)P_{\rm constrained,\theta}.
\]

where \(\rho(z)\) is a source-blind collision/constraint probability.

Do not implement this mixture before L1 confirms the signature in real saved GADEN trajectories.

## 6. Why this is stronger than generic diffusion

The scientific object is not “a diffusion model for trajectories.”

It is:

> **a generative model for the constraint-induced non-Gaussian part of a physically anchored Lagrangian transition law.**

Wind remains the reference drift.

Known free-space physics remains analytic.

The learned/generative component is restricted to unresolved constrained transport.

## 7. L1 predicted signature

If M5's mechanism is real, the independent GADEN realization should show:

### Far from walls
- B1/B2 Gaussian residuals fit well;
- low skew/kurtosis;
- little generative gain.

### Near walls/corners
- larger Gaussian calibration error;
- non-Gaussian residuals;
- multiple directional modes / projected normal component;
- strong relation to wall distance/direction.

### Destructive wall-context shuffle
- conditional structure disappears.

If this spatial signature is absent, the boundary-induced generative argument is not supported.

## 8. Decision impact

This note strengthens **why** a generative model might be needed but does not satisfy L1.

Status remains:

\`M5 KEEP — L1 REAL-DATA CONFIRMATION REQUIRED\`.
