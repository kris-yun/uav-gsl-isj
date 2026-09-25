# RR-MVSI D1 Decision — Supersedes Earlier D0 Advance

Date: 2026-09-25

Decision: **D1_STOP_RRMVSI_NOT_DISTINCT_FROM_ORDINARY_REPRESENTATION**

This decision supersedes the earlier exploratory D0 source-heldout ADVANCE document.

## Why the earlier advance is superseded

A reproducibility audit standardized:
- full 168-candidate support;
- train-source-only hyperparameter selection;
- latent scaling;
- source-context interpolation;
- proper log score;
- ordinary supervised baselines.

Under this stricter implementation, the previously reported approximately +1 bit paired-view advantage over ordinary baselines is not reproducible.

Paired-view CCA still carries signal, but no longer has a stable decisive advantage over supervised LDA / ordinary representation learning.

## Corrected source-heldout linear result

Using nested source-only selection with four checkerboard/realization directions:

Paired-view CCA mean true-source log2 scores were approximately:
- -4.549
- -4.810
- -4.528
- -4.747.

PCA baselines were approximately:
- -4.715
- -4.948
- -4.655
- -4.926.

Thus paired-view CCA consistently beats PCA by a modest margin.

Supervised LDA baselines were approximately:
- -5.436
- -4.788
- -4.449
- -4.877.

CCA and LDA therefore have mixed wins; paired-view structure is not distinctly superior to an ordinary supervised discriminative subspace.

## Nonlinear ordinary representation attack

A simple source-context metric-learning model was trained using only outer-train sources and one 8-realization half.

Observation encoder:
- 300-D log(1+ppm) -> nonlinear latent code.

Context encoder:
- source (x,y) -> latent source code.

Training:
- ordinary cross-entropy / contrastive compatibility between each plume observation and its source-context code;
- no paired-view loss in the baseline.

Evaluation:
- completely heldout checkerboard source classes;
- opposite 8-realization half;
- all 168 candidate source cells.

Across two deterministic seeds, mean true-source log2 scores were approximately:
- -3.752
- -4.018
- -3.895
- -4.107.

Adding an explicit same-source paired-view cosine-invariance term gave:
- -3.758
- -3.895
- -3.762
- -4.045.

Average ordinary baseline: about -3.943 bits.
Average paired-view candidate: about -3.865 bits.

Average incremental benefit: only about +0.078 bit/target, with one of four source-heldout scenarios worsening.

Top-rank gains are similarly mixed.

## Mechanism result that remains valid

D1R still supports:
- strong source-dependent heteroscedastic nuisance;
- low extra cross-realization residual covariance after conditioning on source;
- fresh-realization source information in shared covariance/content directions.

These are useful auxiliary observations.

They do NOT establish a main innovation distinct from ordinary supervised metric/representation learning.

## Frozen STOP rationale

The D1 freeze explicitly required STOP if ordinary supervised/contrastive representation learning explains the gain.

That condition is now met.

Therefore:

**D1_STOP_RRMVSI_NOT_DISTINCT_FROM_ORDINARY_REPRESENTATION**

No new GADEN runs, no neural scaling experiment, and no closed-loop PMFS experiment are authorized for RR-MVSI as the mainline.

Reusable auxiliary insight:
pooled/shared nuisance covariance or repeated-view regularization may later serve as an auxiliary robustness module if a stronger main scientific route is found.