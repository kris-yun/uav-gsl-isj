# RR-MVSI D0 Paired Proper-Score Advantage — 2026-09-25

Evaluation covers all 168 sources x16 realizations exactly once as outer fresh targets.

Each target is evaluated in a source-heldout configuration:
- its source class is absent from representation/source-prototype training;
- its realization half is absent from fitting;
- posterior support contains all 168 candidate cells.

Paired-view CCA dimension, RBF-KRR mapping parameters and temperature are selected using training sources only.

The strongest ordinary method chosen by training-source CV is PCA + RBF-KRR in all four outer scenarios.

## Aggregate result

Mean true-source log2 probability:
- paired-view shared-content CCA: **-3.3933 bits**;
- ordinary PCA+KRR champion: **-4.4923 bits**.

Paired improvement:

**+1.0990 bits per target**.

Equivalent geometric-mean true-source probability ratio:

2^1.099 ≈ **2.14x**.

Target-level paired improvement:
- median = **+1.3201 bits**;
- positive on **81.32%** of 2688 fresh targets.

Source-wise mean improvement:
- positive for **81.55%** of the 168 sources;
- median source gain = **+1.2973 bits**;
- source-gain 10/90 percentiles ≈ **-0.490 / +2.422 bits**.

Fixed-panel realization bootstrap:
- all 168 sources retained;
- 16 realization-level paired differences resampled within each source;
- 5000 bootstrap replicates;
- 95% interval for mean gain: **[+1.0612, +1.1361] bits**.

This bootstrap quantifies realization uncertainty conditional on the frozen 168-source panel; it is not a population-over-source confidence interval.

## Interpretation

The transferable paired-view signal is large on the same full-168 microcell proper-score task.

It is not explained by ordinary PCA low-rank representation plus the same source-coordinate RBF-KRR mapping and model-selection structure.

This result supports advancing RR-MVSI to the frozen existing-D1R D1 theory/algorithm test.

It does not establish nonlinear novelty, cross-House transfer, or real-flight validity.