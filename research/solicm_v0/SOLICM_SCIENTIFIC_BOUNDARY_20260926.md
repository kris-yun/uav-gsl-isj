# SOLICM scientific boundary and literature map

## Why this is not a generic domain-adaptation project

The final proposed scientific object is NOT `make W0 features look like W2 features`.

The candidate main idea is:

> recover only the latent temporal causal mechanisms that are both cross-environment stable and sufficient for source discrimination.

Two 2025/2026 theory lines are intentionally separated:

1. TPAMI 2026 LCA supplies the latent invariant causal-mechanism principle and identifiability setting for high-dimensional time series.
2. NeurIPS 2025 Reward-oriented CRL supplies the principle that full causal recovery can be excessive and that the representation should be only as detailed as needed for the downstream task.

G0 tests only item 1.

Only if G0 passes may G1 combine them into a source-oriented mechanism.

## Known novelty collisions

- time-series domain adaptation and invariant causal representation are established ML topics;
- 2026 gas-recognition work already uses multi-source domain adaptation for gas classification;
- olfactory navigation already has extensive temporal-memory/evidence-integration literature;
- therefore novelty cannot be `domain adaptation`, `causal representation`, or `temporal memory` alone.

The novelty candidate, if supported, must be the source-localization-specific coupling:
`task-sufficient latent causal invariance -> candidate source posterior map`.

## Important assumptions/boundaries from LCA

The published LCA framework assumes:
- high-dimensional observations generated from latent variables through a nonlinear mixing map;
- temporal latent structural equations;
- stable latent causal structure across domains while conditional mechanisms may vary;
- sufficient change/sparsity conditions for identifiability.

G0 does not prove these assumptions are true for turbulent gas dispersion.

G0 only asks whether the published inductive bias has source-discrimination transfer value in a clean same-House/same-source/same-probe wind-shift setting.

## Deployment boundary

The G0 six-class classifier is only a mother-theory probe.

It is NOT the final deployable localization architecture because fixed source IDs do not generalize to arbitrary map cells.

Any G1 after PASS must replace class-ID scoring with a candidate-conditioned score `f(s, y, context)` so it can populate the PMFS source probability map over arbitrary candidate locations.

Target-domain adaptation may use unlabeled online observations, but deployment may not require true-source labels or a target-environment dense source stochastic bank.