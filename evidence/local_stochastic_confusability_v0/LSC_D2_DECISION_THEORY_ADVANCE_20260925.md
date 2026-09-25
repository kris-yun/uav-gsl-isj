# LSC D2 — Decision-Theoretic Distinguishability Advance

Date: 2026-09-25

Decision: **LSC_D2_ADVANCE_MECHANISM_ONLY_LOCAL_STOCHASTIC_DISTINGUISHABILITY**

No new inference algorithm, GADEN run, final target, or closed-loop PMFS experiment is authorized by this decision.

## Mother scientific question

For neighboring candidate source cells, how distinguishable are the stochastic plume-observation distributions under the finite observation protocol?

The mechanism is local statistical distinguishability, not source variance alone, not deterministic field error alone, and not a manually chosen macro scale.

## Pairwise decision-theory proxy

For every one of the 305 unique four-neighbor source pairs:

1. use one 8-realization half only;
2. standardize 300-D log(1+ppm) observations using training-half statistics;
3. define the pairwise mean-difference direction from the training half;
4. project each source's eight samples onto that fixed 1D direction;
5. fit two univariate Gaussian plug-in distributions;
6. compute the Bhattacharyya distance D_B;
7. form the equal-prior plug-in confusion proxy 0.5*exp(-D_B).

Because distribution parameters are estimated from only eight realizations, this quantity is used as a **decision-theory proxy**, not a rigorous finite-sample Bayes-error certificate.

## Fresh binary falsification

Use the opposite 8-realization half as completely fresh samples from the two source cells.

Direction A, first8 -> last8:
- mean fresh pairwise error = 0.2223;
- D_B vs fresh error Spearman = -0.7651;
- confusion proxy vs fresh error Spearman = +0.7651;
- confusion proxy vs fresh error Pearson = +0.7484.

Direction B, last8 -> first8:
- mean fresh pairwise error = 0.2162;
- D_B vs fresh error Spearman = -0.8254;
- confusion proxy vs fresh error Spearman = +0.8254;
- confusion proxy vs fresh error Pearson = +0.8001.

First8/last8 D_B ordering stability across the same 305 neighbor pairs:
- Spearman = 0.7926.

## Link to full 168-cell proper score

For each source, aggregate its four-neighbor pairwise confusion proxies into a local confusion mass.

Mean local confusion mass first8/last8 stability:
- Spearman = 0.8384.

Training-half local confusion mass vs opposite-half 168-cell prototype-posterior NLL:

Direction A:
- Spearman = +0.5958;
- Pearson = +0.6180.

Direction B:
- Spearman = +0.6378;
- Pearson = +0.5229.

Thus a source's local pairwise indistinguishability predicts not only binary source swaps but also fresh multiclass posterior quality.

## Supporting nonparametric evidence

Neighbor-pair energy distance, estimated directly from the eight training samples without a Gaussian model:
- first8/last8 stability Spearman = 0.8209;
- predicts opposite-half fresh binary error with Spearman = -0.6744 / -0.7039.

This prevents the mechanism from depending only on the one-dimensional Gaussian plug-in construction.

## Spatial interpretation

The most confusable competitor is overwhelmingly local:
- about 76% within 0.6 m;
- about 89-91% within 0.9 m;
- about 94% within 1.2 m.

This provides a mechanism-level explanation for the repeated observation that exact source-cell ranking is unstable while a local source basin often remains informative.

## Current claim

Supported:

> Under the frozen House02/W2 observation protocol, neighboring candidate source cells have reproducible finite-sample stochastic distinguishability, and that distinguishability predicts fresh pairwise source confusion and fresh multiclass posterior quality.

Not yet supported:
- cross-wind/cross-House generality;
- a new GSL algorithm;
- a new likelihood;
- an exact information-theoretic lower bound;
- a publishable novelty claim.

## Theory lineage

The appropriate mother-theory family is statistical decision theory / finite-sample model distinguishability, including Bhattacharyya-Chernoff-Hellinger/Le Cam style notions.

A particularly relevant 2026 complex-systems anchor is Aguilar, Muñoz & Azaele, Physical Review X 16, 031015 (2026), 'Limits of Inference in Complex Systems: When Stochastic Models Become Indistinguishable', which studies how finite sampling resolution and dataset size determine stochastic-model distinguishability.

## Next gate

Prior-art audit only:

Search GSL/olfaction for prior use of source-conditioned pairwise distribution distinguishability, Bhattacharyya/Chernoff/Hellinger source-confusion graphs, or an equivalent local stochastic-confusability object.

Only if the mechanism is not already standard in GSL should the primary thread design one second-order inference innovation that preserves the PMFS probability-map output.