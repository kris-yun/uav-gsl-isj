# RR-MVSI Unified Sanity Audit — 2026-09-25

Decision:

**D1_HOLD_LINEAR_MULTIVIEW_SIGNAL_ONLY**

No new simulation is authorized.

## Why the earlier ADVANCE was withdrawn

The earlier exploratory source-heldout result was sensitive to implementation details in latent scaling and prototype/calibration handling.

A unified lightweight audit was therefore run before any expensive nested CV:

- same 168-candidate support;
- same D1R source-heldout checkerboard split;
- fixed 20-dimensional latent space for PCA/LDA/paired-view CCA;
- identical source-coordinate RBF-KRR prototype mapping;
- latent dimensions standardized from the outer training sources only;
- posterior temperature selected on training sources only;
- no heldout-source target used for model selection.

Two representative source-heldout directions were used as a pre-registered sanity stop.

## Representative proper-score results

Scenario A:
- raw log-ppm + KRR: mean true-source log2 = -3.968;
- PCA20 + KRR: -4.037;
- LDA20 + KRR: -6.268;
- paired-view CCA20 + KRR: -6.190.

Scenario B:
- raw log-ppm + KRR: -4.844;
- PCA20 + KRR: -4.023;
- LDA20 + KRR: -6.258;
- paired-view CCA20 + KRR: -6.349.

Rank diagnostics still favor LDA/CCA:
- top1 roughly 23-27%;
- top3 roughly 55-58%;
- median rank 3;

whereas raw/PCA have weaker rank but substantially better calibrated proper score.

## Interpretation

The D1R data continue to support a real repeated-view nuisance geometry:
- source-dependent heteroscedasticity is reproducible;
- cross-realization residual second-order dependence is near the finite-sample independence null;
- paired-view shared directions improve source ordering.

However, that structure does not currently transfer into a better calibrated posterior over completely unseen source classes.

Under the frozen RR-MVSI D1 contract, rank-only gains are insufficient.

Therefore the nonlinear multi-view route is not promoted to the mainline.

## Reusable contribution

Retain paired-view / covariance nuisance suppression as a possible auxiliary observation feature.

Do not claim:
- multi-view identifiability as the main innovation;
- content/style disentanglement as established;
- fresh-source probabilistic superiority.

## Mainline implication

The next main innovation should target the remaining bottleneck directly:

> learning the **source-conditioned stochastic observation distribution** at unseen source locations, rather than only its mean profile or an invariant ranking representation.

The D1R bank is now especially valuable for testing transferable distributional models without any new GADEN runs.