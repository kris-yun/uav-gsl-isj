# M1 derivation v4 — Nuisance-Orthogonal Source Information

Date: 2026-09-23  
Status: **strong source-blind diagnostic; candidate parameter-free movement score**

## 1. Linearized shared-nuisance geometry

At one candidate observation cell, let

- \(h\in\mathbb R^S\): nominal hit predictions across source candidates;
- \(G\in\mathbb R^{S\times d}\): sensitivity of each candidate prediction to the same transport nuisance \(a\);
- \(w\): current normalized source weights;
- \(C=\operatorname{diag}(w)-ww^T\): weighted centering matrix.

Native PMFS variance is

\[
V_0=h^TCh.
\]

Shared-adversary variance is

\[
V(a)=(h+Ga)^TC(h+Ga).
\]

## 2. Unbounded nuisance projection

Ignoring amplitude for a moment, solve

\[
V_\perp
=
\min_a
(h+Ga)^TC(h+Ga).
\]

The minimum is

\[
\boxed{
V_\perp
=
h^TCh
-
h^TCG
(G^TCG)^\dagger
G^TCh
}
\]

or, with \(b=G^TCh\), \(A=G^TCG\),

\[
V_\perp=V_0-b^TA^\dagger b.
\]

This is the weighted residual source variance after removing the component explainable by the transport-nuisance tangent space.

It is the zero-hyperparameter limit of the SATI geometry.

## 3. Transport confounding ratio

For \(V_0>0\), define

\[
\boxed{
\kappa_{\rm tr}
=
\frac{V_0-V_\perp}{V_0}
}
\]

with numerical clipping to \([0,1]\).

Interpretation:

- \(\kappa_{\rm tr}\approx0\): nominal source discrimination is transverse/orthogonal to transport nuisance;
- \(\kappa_{\rm tr}\approx1\): nominal source discrimination can be explained almost entirely by transport change.

This gives a direct diagnostic for the earlier empirical paradox:

> a location can have high and simulator-seed-stable \`varianceOfHitProb\` while being poor for real source identification if that variance lies mainly in the transport-nuisance subspace.

## 4. Why this is not merely an uncertainty penalty

If every candidate has the same transport sensitivity, all rows of \(G\) are equal.

Then

\[
CG=0
\]

and therefore

\[
V_\perp=V_0.
\]

So a large absolute wind sensitivity does **not** get penalized when it shifts all source hypotheses together.

Only **source-vs-transport confounding** is removed.

Conversely, if the centered candidate-prediction vector lies inside the centered nuisance span, then

\[
V_\perp=0.
\]

That cell has no first-order source information that cannot be mimicked by transport error.

## 5. Relation to nuisance-aware active learning

This geometry is consistent with the target/nuisance distinction emphasized in:

- Sloman et al., *Bayesian Active Learning in the Presence of Nuisance Parameters*, UAI 2024. They show nuisance uncertainty can create "negative interference" in learning the target and that nuisance identification can become an auxiliary objective.
- Bartuska, Espath & Tempone, *Laplace-based strategies for Bayesian optimal experimental design with nuisance uncertainty*, Statistics and Computing 35, 2025. They explicitly optimize information about target parameters while marginalizing nuisance uncertainty.
- Shafiei et al., *Distributionally robust free energy principle for decision-making*, Nature Communications, 2025. They place ambiguity on environment transition models and optimize decisions against model/environment mismatch.

These are parent concepts / theory context, not novelty claims.

## 6. Candidate PMFS interpretation

Target:
- source location / source candidate identity.

Nuisance:
- transport drift / diffusion / wind-model perturbations.

Design variable:
- next UAV sensing location.

Observation:
- gas hit/frequency measurement.

PMFS currently values nominal between-source variance. NOSI/SATI asks how much of that source variance survives after accounting for transport nuisance.

## 7. First source-blind test when Native artifacts arrive

For every source update and every candidate observation cell compute:

- \(V_0\): native PMFS source variance;
- \(V_\perp\): nuisance-orthogonal source variance;
- \(\kappa_{\rm tr}\): transport confounding ratio.

Before looking at source truth, report:

1. rank correlation \(V_0\) vs \(V_\perp\);
2. top-10/top-20 overlap;
3. fraction of top-native cells with \(\kappa_{\rm tr}>0.8\);
4. spatial map of \(\kappa_{\rm tr}\);
5. cross-plume-realization stability of \(\kappa_{\rm tr}\).

Then reveal truth and perform the same fixed-budget truth-source-rank intervention test.

## 8. Decision

This parameter-free nuisance projection should be tested **before** tuning a finite SATI radius.

If \(V_\perp\) itself gives no source-rank signal, adding a hand-calibrated radius is unlikely to rescue the scientific mechanism and the line should be reconsidered.
