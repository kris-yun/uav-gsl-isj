# M7 Refinement — Keep Known Physics Exact, Learn Only a Residual Operator Dictionary

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`

## 1. Problem discovered during interface audit

The ICML 2026 advection–diffusion benchmark uses relatively low-dimensional/global dynamics parameters.

Indoor GSL is harder:

\[
W=W(x,t)
\]

is a spatially varying vector field constrained by walls/openings.

If M7 learns the complete wind-advection map from scratch, the method risks collapsing into a generic source/wind-conditioned neural operator.

That would weaken both physical meaning and novelty.

## 2. Decision

**Do not learn basic advection in the first M7 implementation.**

Keep known mechanisms explicit:

\[
\mathcal J_S
\]

analytic source injection;

\[
\mathcal A_W
\]

explicit wind-field advection;

\[
\mathcal D_0
\]

a simple physical baseline diffusion/spreading operator;

\[
\mathcal B_O
\]

explicit obstacle/boundary projection.

Define the known split:

\[
\mathcal F_0
=
\mathcal B_O
\circ
\mathcal D_0
\circ
\mathcal A_W
\circ
\mathcal J_S.
\]

Learn only the unresolved transport operator.

## 3. Residual mechanism library

Let the high-fidelity transition be

\[
c_{t+\Delta}^{HF}
=
\mathcal F_0(c_t)
+
R(c_t,W,O,\ldots).
\]

Instead of one monolithic residual network, learn/recover a small dictionary:

\[
\mathcal R
=
\{
R_1,\ldots,R_K
\}.
\]

Possible residual mechanisms may correspond empirically to:
- wall recirculation;
- shear / turning;
- enhanced spreading;
- wake/intermittency regimes.

These physical labels are **not assumed** a priori.

They must be inferred/validated from residual structure.

## 4. Test-time composition

For a new House/wind/source regime, freeze the residual library and select/compose operators using source-blind context:

\[
\hat c_{t+\Delta}
=
R_{k_m}
\circ\cdots\circ
R_{k_1}
\circ
\mathcal F_0(c_t).
\]

or a predeclared short splitting family where residual blocks are inserted between exact physical blocks.

No gradient update at test time.

The source hypothesis changes only \(\mathcal J_S\).

The environment/wind context controls selection of residual operators.

## 5. Why this still reflects the ICML 2026 mother idea

The key transferred concept is not “learn every PDE term.”

It is:

> maintain a reusable dictionary of mechanism operators and perform test-time computation over their compositions to represent unseen dynamics.

The gas-specific second derivation is stronger physically because:
- known advection is not relearned;
- walls are not learned from scratch;
- only unresolved transport is placed in the learned dictionary.

## 6. O0 residual-dictionary viability test

After computing the analytical split residual

\[
R_t
=
c_{t+\Delta}^{HF}
-
\mathcal F_0(c_t),
\]

test whether residuals form a reusable low-complexity family.

### Source-independence test

Under the same House/wind but different sources:

- compare residual covariance/subspaces;
- train a source-blind low-rank residual basis on source A;
- evaluate reconstruction on source B.

A reusable transport residual should transfer across source interventions.

### Wind/regime structure

Across wind regimes:
- measure whether residual subspaces change systematically;
- test whether a small union/dictionary of subspaces explains both regimes better than one global residual model.

### Complexity tests

Report:
- PCA cumulative energy;
- effective rank;
- cluster stability across plume seeds;
- held-out residual reconstruction.

## 7. Required positive signature

M7 becomes substantially more plausible if:

1. known physical split removes a large fraction of raw transition error;
2. remaining residual is structured;
3. residual structure transfers across source position;
4. residual changes in a repeatable way with wind/obstacle regime;
5. a small dictionary explains held-out regimes better than one global low-rank basis.

This is exactly the signature needed to justify reusable learned mechanism operators.

## 8. Kill condition

If residual:
- is effectively high-rank noise;
- is source-specific;
- has no stable cross-seed structure;
- or one global residual model works as well as any dictionary,

then M7's test-time mechanism-library claim has no empirical basis.

Do not train a large operator model to rescue it.

## 9. Current status

\`M7 = KEEP, BUT FIRST IMPLEMENTATION MUST BE PHYSICS-EXACT + RESIDUAL-DICTIONARY\`.

This refinement improves physical interpretability and prevents M7 from degenerating into generic PINO.
