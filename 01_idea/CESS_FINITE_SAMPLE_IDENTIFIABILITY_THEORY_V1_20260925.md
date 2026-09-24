# CESS Finite-Sample Emergent Identifiability Theory v1

Date: 2026-09-25

Status:
**THEORY FREEZE FOR D1R->D1C DESIGN; NOT A SCIENTIFIC RESULT**

Working mainline name:

**Causal-Emergence-Inspired Finite-Sample Multiscale Source Identifiability**

Short concept name:

**Finite-Sample Emergent Identifiability (FSEI)**

This document formalizes the mainline after the auxiliary-Pro red-team and
before any locked D1C target generation.

---

## 1. Variables

Let

\[
S\in\{1,\dots,N\}
\]

be the micro source cell under a fixed source prior \(\pi_s\).

Let

\[
Y
\]

be the plume observation under a fixed observation protocol.

Let a deterministic source coarse-graining be

\[
M=g(S)\in\{1,\dots,K\}.
\]

The macro prior is induced by the same micro prior:

\[
\Pi_m=\sum_{s:g(s)=m}\pi_s.
\]

No independent uniform-macro prior is introduced for the final localization
task.

This is essential: D1C remains the same N-way source-localization problem.

---

## 2. Honest macro-to-micro posterior lifting

Suppose a macro model provides

\[
Q_g(m\mid y).
\]

The only admissible default lift that does not invent within-macro source
evidence is

\[
q_g(s\mid y)
=
Q_g(g(s)\mid y)
\frac{\pi_s}{\Pi_{g(s)}}.
\]

Therefore

\[
\sum_{s:g(s)=m}q_g(s\mid y)=Q_g(m\mid y)
\]

and total source probability is conserved.

Under a uniform micro prior, probability is uniform within an unresolved
macrostate.

No centroid spike, MAP-cell reassignment, or hidden within-group decoder is
allowed unless separately trained and evaluated as an explicit model.

---

## 3. Oracle coarse-graining fidelity theorem

Let the true micro posterior be

\[
p(s\mid y).
\]

For a fixed partition \(g\), define the oracle macro posterior

\[
p(m\mid y)=\sum_{s:g(s)=m}p(s\mid y)
\]

and its honest micro lift

\[
q_g^*(s\mid y)
=
p(g(s)\mid y)\frac{\pi_s}{\Pi_{g(s)}}.
\]

Then the expected excess logarithmic loss of the oracle coarse model relative
to the true micro posterior is exactly

\[
\mathcal L_{\rm fid}(g)
=
\mathbb E
\left[
\log\frac{p(S\mid Y)}{q_g^*(S\mid Y)}
\right]
=
I(S;Y\mid M).
\]

### Proof sketch

Because \(M=g(S)\),

\[
H(S\mid Y)=H(M\mid Y)+H(S\mid M,Y).
\]

The expected negative log score of the honest oracle macro lift is

\[
H(M\mid Y)+H(S\mid M).
\]

Subtracting \(H(S\mid Y)\) gives

\[
H(S\mid M)-H(S\mid M,Y)
=
I(S;Y\mid M).
\]

Therefore deterministic coarse-graining does not create true micro-source
information.

It loses exactly the information that the observation contains about
within-macro source identity.

This explicitly respects data-processing inequalities.

---

## 4. Finite-sample emergence criterion

The project does not claim that the macro representation has more oracle
information than the micro representation.

The hypothesis is finite-sample.

Let

\[
\hat q_{\rm id,n}(s\mid y)
\]

be an identity/micro estimator learned from \(n\) stochastic reference
realizations per source.

Let

\[
\hat q_{g,n}(s\mid y)
\]

be a macro-pooled estimator, lifted honestly to the same micro support.

Define the finite-sample estimation regrets

\[
\varepsilon_{\rm id}(n)
=
\mathbb E
D_{\rm KL}
\left(
p(S\mid Y)
\Vert
\hat q_{\rm id,n}(S\mid Y)
\right)
\]

and

\[
\varepsilon_g(n)
=
\mathbb E
D_{\rm KL}
\left(
q_g^*(S\mid Y)
\Vert
\hat q_{g,n}(S\mid Y)
\right)
\]

with the second regret measured relative to the oracle model available within
the partition-restricted family.

Then the expected microcell log-score advantage of coarse-graining has the
bias-variance/information form

\[
\Delta_n(g)
=
\mathbb E
[
\log \hat q_{g,n}(S\mid Y)
-
\log \hat q_{\rm id,n}(S\mid Y)
]
\]

and, schematically,

\[
\Delta_n(g)
\approx
\underbrace{
\varepsilon_{\rm id}(n)-\varepsilon_g(n)
}_{\text{finite-sample estimation-risk reduction}}
-
\underbrace{
I(S;Y\mid M)
}_{\text{irreducible coarse-graining fidelity loss}}.
\]

Hence a macrostate is useful only when

\[
\varepsilon_{\rm id}(n)-\varepsilon_g(n)
>
I(S;Y\mid M).
\]

This is the central scientific criterion.

A positive finite-sample gain does not violate the data-processing inequality:
it means that reduced estimation/generalization error exceeds the information
discarded by the coarse representation.

---

## 5. Scientific interpretation for turbulent GSL

In stochastic plume localization:

- neighboring 0.30 m source cells may induce highly overlapping encounter
  distributions;
- estimating a separate observation law for every fine source cell from a
  small realization budget has high variance;
- pooling statistically equivalent / nearly-equivalent neighboring cells can
  reduce estimator variance;
- excessive pooling destroys real within-region source information.

Therefore the scientifically meaningful source scale is a finite-sample
trade-off between:

1. stochastic estimation variance;
2. within-macro source-information loss.

The scale should emerge from the observation channel and realization budget,
not from an arbitrary spatial-error tolerance.

---

## 6. Relationship to causal emergence

The mother-theory inspiration is causal emergence / effective information /
information-theoretic coarse-graining.

Relevant recent theory includes:

- Zhang et al., *Dynamical reversibility and a new theory of causal emergence
  based on SVD*, npj Complexity, 2025,
  DOI 10.1038/s44260-025-00028-0.
- Liu et al., *Singular-value-decomposition-based causal emergence for Gaussian
  iterative systems*, Physical Review E, 2025,
  DOI 10.1103/mfct-sxn5.
- Yang et al., *Finding emergence in data by maximizing effective information*,
  National Science Review, 2025 volume,
  DOI 10.1093/nsr/nwae279.
- Cawiding et al., *A reframed landscape of causal emergence*, Patterns, 2026,
  DOI 10.1016/j.patter.2025.101476.

However, the current GSL problem is an inverse static-parameter problem, not a
source-state Markov transition system.

Therefore the mainline must currently claim:

**causal-emergence-inspired statistical identifiability**

rather than literal dynamical causal emergence.

The stronger label is conditional on later theory and cross-environment
evidence.

---

## 7. Relationship to ordinary pooling

Ordinary pooling can also reduce variance.

Therefore a CESS/FSEI claim is not established merely by outperforming the
identity model.

The final method must be compared fairly against:

- geometry-only pooling;
- encounter-profile clustering;
- hierarchical Bayesian/shrinkage pooling;
- MDL / complexity-regularized grouping;
- size-matched random groupings;
- all-in-one pooling.

All methods must use:

- identical reference data;
- identical candidate source support;
- identical prior;
- identical observation channel;
- identical target realizations;
- comparable model-selection budgets;
- microcell posterior output.

If an ordinary pooling baseline matches the final predictive gain and yields
equally stable/fidelitous partitions, the stronger causal-emergence-inspired
claim should be downgraded.

---

## 8. Reference-only partition-selection principle

D1R reference data may be used to choose a partition family and its
hyperparameters.

The preferred formulation is not "maximize macro accuracy."

Instead, for each candidate partition \(g\), reference-only cross-fitting
estimates:

\[
\widehat{\Delta}_{\rm ref}(g)
=
\frac{1}{|\mathcal D_{\rm val}|}
\sum_{(s,y)}
\log_2
\frac{
\hat q_{g,\rm train}(s\mid y)
}{
\hat q_{\rm id,\rm train}(s\mid y)
}.
\]

This stays on the original micro source task.

Partition selection must additionally inspect:

- split stability;
- co-membership stability;
- physical connectedness;
- fidelity loss;
- calibration;
- group size / diameter;
- raw-amplitude information loss.

The exact finite candidate family and thresholds remain to be frozen after
D1R and the auxiliary-Pro operational memo.

---

## 9. D1C locked confirmation principle

After all model choices are frozen, generate completely new target
realizations.

Primary endpoint:

\[
\Delta_B
=
\frac1N
\sum_{s=1}^{N}
\frac1J
\sum_{r=1}^{J}
\log_2
\frac{
q_{g^*}(s\mid y_{sr})
}{
q_{\rm id}(s\mid y_{sr})
}.
\]

The comparison is valid only if both models share:

- the same \(N=168\) source support;
- the same micro prior;
- the same observation input;
- the same target realization;
- the same reference-budget constraints.

No alternate target endpoint may replace \(\Delta_B\) after target reveal.

Diagnostics such as truth rank, MAP error and probability mass within fixed
radii remain secondary.

---

## 10. What would constitute the main scientific finding?

A future positive result would mean:

> under a fixed finite stochastic-realization budget, a reproducible
> multiscale source representation reduces held-out microcell inference risk
> enough to overcome its unavoidable within-macro information loss, while
> preserving unresolved uncertainty on the original PMFS source map.

This is more precise than saying "the macro has more information."

It makes finite-sample identifiability, not raw coarse classification, the
scientific object.

---

## 11. Current status

- R0: PASS.
- D1R: authorized reference construction.
- FSEI theory: frozen at conceptual/mathematical level in this document.
- Partition algorithm: not yet frozen.
- D1C thresholds: not yet frozen.
- Final targets: not generated.
- PMFS closed loop: not authorized.
