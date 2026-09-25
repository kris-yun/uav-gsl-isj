# LSC D1 — Pairwise Fresh-Realization Falsification

Date: 2026-09-25

Status: **PAIRWISE_CONFUSABILITY_MECHANISM_REPRODUCED**

## Question

Does distributional separation estimated from one realization half predict the actual fresh-realization confusion probability between neighboring source cells?

## Pair set

Use every unique four-neighbor source pair in the complete 24x7 D1R panel:
- 305 unique spatial neighbor pairs.

No pair is selected by outcome.

## Training-half quantities

Using only one 8-realization half and train-only global standardization in 300-D log(1+ppm) space, compute for each pair:

1. mean-signature squared separation d^2;
2. stochastic SNR margin d^2/(v_s+v_n), using source-wise scalar stochastic spread;
3. nonparametric energy distance between the two eight-sample source distributions.

## Fresh pairwise error

On the opposite 8-realization half, classify the 16 fresh samples from the two source cells with the ordinary train-half nearest-centroid rule.

The endpoint is the fresh binary source-confusion error, not a fitted information measure.

## Direction A

Train reps 1-8; fresh reps 9-16.

- mean fresh pair error = 0.2250;
- median = 0.2500;
- 27.5% of pairs have zero fresh error;
- 50.5% have fresh error >= 0.25.

Training metric vs fresh binary error, Spearman:
- mean separation d^2: -0.5178;
- stochastic SNR margin: -0.6450;
- energy distance: -0.6744.

## Direction B

Train reps 9-16; fresh reps 1-8.

- mean fresh pair error = 0.2166;
- median = 0.1875;
- 29.5% have zero error;
- 45.9% have error >= 0.25.

Spearman:
- mean separation d^2: -0.5994;
- stochastic SNR margin: -0.6873;
- energy distance: -0.7039.

## Metric reproducibility

First8 versus last8 pairwise metric ordering across all 305 neighbor pairs:
- mean separation d^2: Spearman 0.7681;
- stochastic SNR margin: 0.7515;
- energy distance: 0.8209.

## Interpretation

Neighbor-source stochastic overlap is not merely correlated with one multiclass decoder's posterior score.

It predicts actual source-pair interchange on completely fresh plume realizations.

The nonparametric energy-distance result is strongest and does not depend on a Gaussian covariance model.

Thus the current mechanism fact is:

> neighboring candidate sources induce stochastic observation distributions with reproducible, spatially local degrees of overlap, and that overlap predicts fresh pairwise source confusion.

## Scientific boundary

This does not yet prove that energy distance itself is the correct inference quantity or a novel algorithm.

Next theory step must connect the observed pairwise distinguishability to a principled decision-theoretic quantity (Bayes error / total variation / Hellinger / Chernoff-type distinguishability) and derive an a priori prediction for multiclass source posterior behavior.

No new GADEN run or localization model is authorized at this stage.