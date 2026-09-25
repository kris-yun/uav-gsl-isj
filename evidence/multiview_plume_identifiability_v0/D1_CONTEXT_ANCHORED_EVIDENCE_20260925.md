# Context-Anchored RR-MVSI D1 Evidence — 2026-09-25

Status: **DATA GATES SATISFIED; THEORY/PRIOR-ART GATE STILL OPEN**

## Candidate second-order idea

Paired-view CCA learns observation directions reproducible across independent plume realizations of the same source.

However, real deployment also requires that shared content be generatable from candidate source context.

The context-anchored linear D1 candidate therefore augments the repeated-view covariance objective with a source-context predictable covariance term.

Schematic generalized eigen objective:

maximize source-shared cross-view covariance + beta * context-predictable covariance
relative to total single-view covariance.

Current D1 context is deliberately minimal:
- source (x,y) coordinates;
- RBF context features.

Future cross-environment source context must include geometry/wind rather than rely on within-House coordinates alone.

## Train-only hyperparameter stability

Candidate context grids:
- RBF bandwidth h in {0.6, 1.2} m;
- context weight beta in {0.5, 1.0}.

Across all four source-heldout outer scenarios, training-source CV selected:

**h = 0.6 m, beta = 1.0**.

Across both source-complete 8/8 fresh-realization directions, training-realization CV also selected:

**h = 0.6 m, beta = 1.0**.

Thus the same configuration emerged in all six independent train-only selection problems.

## Source-heldout primary result

Full 168-candidate support.

Context-anchored mean true-source log2 versus paired-view CCA:
- dir0/parity0: -3.349 vs -3.447;
- dir0/parity1: -3.243 vs -3.366;
- dir1/parity0: -3.362 vs -3.366;
- dir1/parity1: -3.327 vs -3.394.

All four outer directions are non-inferior and improve mean proper score; one direction has only a small gain.

Across all 2688 source-heldout fresh targets:
- mean context-over-paired gain: **+0.0731 bits/target**;
- median target gain: **+0.0731 bits**;
- positive target fraction: **58.78%**;
- positive source-mean fraction: **55.95%**;
- fixed-panel within-source realization bootstrap 95% interval: **[+0.0512,+0.0956] bits**.

## Source-complete fresh-realization result

Paired-view CCA train-only selection:
- both directions select d=20;
- calibrated temperature 0.5.

Context-anchored train-only selection:
- both directions select h=0.6, beta=1.0, d=20;
- calibrated temperature 1.0.

Fresh test proper scores:
- direction A: paired -2.2935 -> context -2.1526 bits;
- direction B: paired -2.4637 -> context -2.3307 bits.

Mean paired improvement across the full 168x16 symmetric evaluation:
- **+0.1369 bits/target**;
- fixed-panel within-source realization bootstrap 95% interval: **[+0.0558,+0.2262] bits**.

Top-1 is roughly unchanged/slightly lower, so this improvement should be interpreted as better probability allocation rather than an argmax-only gain.

## Relation to ordinary baselines

Source-heldout paired-view CCA already beats training-selected PCA+KRR by about +1.10 bits/target.

The context anchor adds a smaller but consistent additional proper-score gain over that paired-view lower bound.

Therefore the second-order contribution is not simply PCA, LDA, covariance whitening, or coordinate regression.

## Current interpretation

The data now support two nested mechanisms:

1. repeated plume views identify a transferable source-shared subspace while suppressing realization nuisance;
2. constraining that shared subspace toward source-context-predictable structure improves calibrated source probability assignment.

## Remaining D1 blockers

Do not promote to final mainline until:
- direct GSL/olfaction prior art excludes the same repeated-realization factorization;
- multi-view/content-style theory assumptions are audited;
- strongest ordinary supervised-contrastive baseline is tested with the same data budget;
- the future source-context representation is formulated using map/wind, not x-y alone.

No new simulations are authorized yet.