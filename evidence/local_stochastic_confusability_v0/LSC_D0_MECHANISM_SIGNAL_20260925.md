# LSC v0 — Local Stochastic Confusability Mechanism Screen

Date: 2026-09-25

Status: **REFERENCE-ONLY POSITIVE MECHANISM SIGNAL; NO NEW MODEL AUTHORIZED**

## Scientific observation

The strongest current D1R predictor of fresh probabilistic source-localization difficulty is not raw plume variance, not local Fisher sensitivity alone, and not the DASN aligned-noise index.

It is the **local stochastic separation between neighboring source-conditioned observation distributions**.

## Training-half local margin

For each source s, using only one 8-realization half:
- standardize log(1+ppm) observations from the training half only;
- estimate source mean observation mu_s;
- estimate a scalar within-source stochastic spread v_s;
- for each spatial four-neighbor n compute

  margin(s,n) = ||mu_s-mu_n||^2 / (v_s+v_n),

with the feature-space squared norm averaged over the 300 frozen observation coordinates.

The source-level local stochastic margin is the median over available spatial neighbors.

## Reproducibility

First8 versus last8 local stochastic margin:
- Spearman rho = 0.7710;
- log-scale Pearson r = 0.7693.

Thus the source-wise confusability ordering is highly reproducible across independent plume-realization halves.

## Prediction of fresh proper score

Use an ordinary 168-class prototype posterior trained on one 8-realization half, with temperature selected by train-half leave-one-realization-out log loss.

Fresh source-wise negative log score on the opposite half is predicted by the training-half local stochastic margin:

- first8 -> last8: Spearman rho = -0.5852;
- last8 -> first8: Spearman rho = -0.6160.

## Signal-versus-noise decomposition

Median neighboring mean-signature separation alone:
- rho = -0.5456 / -0.5308.

Neighbor stochastic spread alone:
- rho = +0.0961 / +0.1362.

Separation/spread stochastic margin:
- rho = -0.5852 / -0.6160.

Source-level CV R^2 from a single scalar:
- mean separation: 0.178 / 0.054;
- stochastic spread: 0.024 / 0.082;
- stochastic margin: 0.339 / 0.227.

Thus the ratio/overlap structure is more predictive than either component alone.

## Nonparametric distribution-overlap check

Using the eight training realizations directly, compute pairwise energy distance between neighboring source distributions in standardized 300-D log-ppm space.

Median local energy distance:
- first8/last8 stability Spearman = 0.8154;
- predicts fresh NLL with Spearman = -0.5671 / -0.5792.

This shows the mechanism does not depend on a Gaussian/Fisher approximation or on the hand-built separation/spread ratio.

## Spatial locality of confusers

Using all-pair stochastic margin, select the most confusable competing source for every source.

First8:
- 43.5% of nearest confusers within 0.3 m;
- 76.8% within 0.6 m;
- 91.1% within 0.9 m;
- 94.0% within 1.2 m.

Last8:
- 51.2% within 0.3 m;
- 75.6% within 0.6 m;
- 89.3% within 0.9 m;
- 93.5% within 1.2 m.

Median nearest-confuser distance is about 0.3-0.42 m.

Exact nearest-confuser identity matches across first8/last8 for 35.7% of sources; top-3 confuser sets have mean overlap 0.464.

Interpretation:

> exact competing cell identity fluctuates, but stochastic source confusion is overwhelmingly local in space.

This provides a direct mechanism-level explanation for earlier observations that exact microcell ranking can be unstable while a local source basin remains informative.

## Controls already known

Local stochastic margin remains negatively associated with fresh NLL after controlling for total residual variance, gain variance, true boundary label and source x/y position:
- partial correlation approximately -0.384 / -0.216.

Incremental source-level CV R^2 beyond those ordinary controls:
- +0.074 in one direction;
- +0.006 in the reverse direction.

The asymmetry means this is not yet a final mechanism PASS.

## Current boundary

Supported:
- reproducible local distributional confusability;
- direct relation to fresh proper score;
- stronger prediction than mean separation or stochastic spread alone;
- robustness to a nonparametric energy-distance formulation;
- confusers are predominantly spatially local.

Not established:
- a unique theoretical information quantity;
- cross-wind/cross-House invariance;
- a new inference algorithm;
- superiority to ordinary likelihood methods;
- a publishable main innovation.

Next step must identify a theory quantity with an a priori prediction for posterior confusion and test that prediction on D1R before designing any new algorithm.