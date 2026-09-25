# LSC D3 — Inference-Consequence Audit

Date: 2026-09-25

Decision: **LSC_MECHANISM_ADVANCED_BUT_DIRECT_POSTERIOR_CORRECTION_HOLD**

## Question

Does the validated local stochastic-confusability graph imply a distinct PMFS posterior update beyond ordinary graph smoothing / local shrinkage?

## Baseline posterior

Train on one 8-realization half using standardized 300-D log(1+ppm) source prototypes.
Use a train-only 6/2 split to select one posterior temperature.
Evaluate on the opposite 8 realizations/source over all 168 cells.

Fresh mean true-source log2 score:
- direction A: -3.9582 bit;
- direction B: -4.0543 bit.

## Ordinary graph smoothing

One-step probability diffusion over the four-neighbor source graph:

q = (1-alpha)p + alpha pA,

with alpha selected only on the training-half calibration split.

Selected alpha = 0.05 in both directions.

Fresh mean true-source log2:
- direction A: -3.9309 bit;
- direction B: -3.9701 bit.

Thus ordinary graph smoothing gives a small proper-score improvement.

## Ordinary local prototype pooling

Shrink each source prototype toward the mean of its four-neighbor prototypes:

mu'_s = (1-beta)mu_s + beta mean_{n in N(s)} mu_n.

beta and temperature selected on training-only calibration data.

Selected beta = 0.30 in both directions.

Fresh mean true-source log2:
- direction A: -3.9431 bit;
- direction B: -4.0041 bit.

This also gives a small improvement over the unpooled prototype model.

## Local pairwise-ratio refinement

For the base posterior MAP source and its four-neighbor cells, fit train-half one-dimensional Gaussian pairwise likelihood-ratio models and redistribute only the existing local posterior mass.

Train-only local temperature selected before fresh evaluation.

Fresh mean true-source log2:
- direction A: -4.8515 bit;
- direction B: -4.1328 bit.

The LSC-specific local ratio refinement is worse than the base posterior.

## Global Hodge integration negative control

An exploratory construction estimated local edge-wise pairwise likelihood ratios on all 305 neighboring-source edges and projected them by graph-Hodge least squares into a global source potential.

Fresh proper scores collapsed to approximately:
- -20.9 bit;
- -26.4 bit.

Reason:
local i-vs-j density-ratio models are only reliable near the support of hypotheses i/j; evaluating every local edge on arbitrary far-source observations creates severe off-support extrapolation.

Moreover, if all edge ratios came from one coherent global generative likelihood, Hodge integration would merely reconstruct that same likelihood potential and add no information.

## Scientific conclusion

The LSC mechanism is real, but its most immediate posterior consequence is already captured by ordinary local smoothing/shrinkage.

Therefore the project must NOT claim novelty for:
- confusion-graph posterior diffusion;
- local graph smoothing;
- local prototype pooling;
- Hodge integration of naive pairwise evidence.

The validated mechanism can still motivate a different scientific question:

> can the observation representation itself be learned so that stochastic distinguishability between spatially neighboring source hypotheses increases on fresh plume realizations?

That question must first pass an ordinary linear local-discriminant lower-bound test before any new far-domain theory or neural model is proposed.