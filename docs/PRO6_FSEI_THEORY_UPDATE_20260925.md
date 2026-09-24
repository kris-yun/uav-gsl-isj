# PRO6 THEORY UPDATE — FSEI Exact Decomposition

Date: 2026-09-25

The primary thread has now formalized the mainline one level further.

Working concept:

**Finite-Sample Emergent Identifiability (FSEI)**

Do not continue using "macro EI > micro EI" as the core proof.

## Exact fidelity result

For micro source \(S\), observation \(Y\), and deterministic partition
\(M=g(S)\), under the same fixed micro prior, the oracle macro posterior lifted
honestly back to microcells incurs expected excess log loss

\[
\mathcal L_{\rm fid}(g)
=
I(S;Y\mid M).
\]

This is the irreducible information lost by not distinguishing source cells
inside a macrostate.

## Exact finite-sample decomposition

Let \(\hat q_{\rm id,n}\) be the finite-sample identity estimator and
\(\hat q_{g,n}\) the finite-sample macro-pooled estimator lifted back to the
same microcell support.

Define estimation regrets under the same true \(p(S,Y)\):

\[
\mathcal E_{\rm id,n}
=
E\log\frac{p(S|Y)}{\hat q_{\rm id,n}(S|Y)}
\]

and

\[
\mathcal E_{g,n}
=
E\log\frac{q_g^*(S|Y)}{\hat q_{g,n}(S|Y)}.
\]

Then the expected same-task microcell log-score gain is exactly

\[
\boxed{
\Delta_n(g)
=
\mathcal E_{\rm id,n}
-
\mathcal E_{g,n}
-
I(S;Y|M)
}.
\]

Therefore a coarse source scale helps only when finite-sample estimation-risk
reduction exceeds irreducible within-macro information loss.

This is the theory you should operationalize in the D1R->D1C work.

## Prior-art boundary tightened

The primary thread has also verified:

- AAAI 2025 already has *Emergence-Inspired Multi-Granularity Causal
  Learning*, DOI 10.1609/aaai.v39i18.34113.
- UAI 2023 already has data-driven state aggregation with finite-sample error
  bounds.

Therefore "emergence-inspired multi-granularity learning" and "finite-sample
state aggregation" are not sufficient novelty claims.

The defensible GSL novelty must involve the integrated bundle:

- repeated turbulent-plume realizations;
- source-scale identifiability;
- original microcell source task/prior;
- exact \(I(S;Y|M)\) fidelity accounting;
- uncertainty-preserving microcell posterior;
- untouched-target proper score;
- strong ordinary pooling/shrinkage baselines;
- PMFS-compatible probability map.

## What to change in your current assignment

When writing:

- D1R_TO_D1C_OPERATIONAL_THEORY.md
- PARTITION_SEARCH_AND_BASELINES.md
- D1C_PROPER_SCORE_AND_POWER.md
- CAUSAL_EMERGENCE_CLAIM_BOUNDARY.md

explicitly use the FSEI decomposition above.

For every candidate partition algorithm, explain which term it is trying to
reduce:

- estimation regret;
- fidelity loss;
- or both.

For every ordinary pooling baseline, state whether the FSEI candidate provides
anything beyond its bias/variance trade-off.

Do not overclaim causal emergence.
