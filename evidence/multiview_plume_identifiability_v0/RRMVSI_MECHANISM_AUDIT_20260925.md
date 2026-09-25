# RR-MVSI Mechanism Audit — Heteroscedasticity and Cross-Realization Residual Independence

Date: 2026-09-25

Data: D1R pooled tensor, log(1+ppm), shape 168 x16 x300.

Status: **SUPPORTS LINEAR MOMENT MODEL; DOES NOT PROVE NONLINEAR IDENTIFIABILITY**

## Source-dependent nuisance amplitude

For each source, subtract the 16-realization source mean in log-ppm feature space and compute mean squared residual norm per realization.

Across the 168 sources:
- minimum: 0.5070
- q10: 1.3161
- median: 4.3100
- q90: 10.8518
- maximum: 21.6691

Using first8 and last8 independently, the source ordering of residual energy has Spearman rho = **0.5844**.

Therefore plume-realization nuisance is strongly source/location dependent and reproducibly heteroscedastic.

Any mainline model that assumes one identical source-independent plume-noise covariance is scientifically suspect.

## Cross-realization residual covariance

For every source, independently center first8 and last8 log-ppm realizations by their own half means.

Pool all 168 x8 residual pairs and form the cross-half residual covariance C12.

Normalize by the geometric mean of the two within-half covariance Frobenius norms:

rho_cross = ||C12||_F / sqrt(||C11||_F ||C22||_F).

Observed rho_cross = **0.06719**.

As a finite-sample null, independently permute the last8 realization indices within every source 500 times while preserving each source's residual distribution.

Null distribution:
- q2.5: 0.0514
- median: 0.0772
- q97.5: 0.1340
- mean: 0.0806.

The observed cross-half residual covariance is not elevated relative to this independence-compatible finite-sample null.

## Scientific interpretation

The two empirical facts needed by the linear repeated-view decomposition coexist:

1. nuisance variance can depend strongly on source;
2. independently seeded realizations do not show an extra shared residual second-order component after conditioning/centering on source.

This supports the moment identity:

Cov(Y1,Y2) = Cov_S(mu_S)

for independent same-source plume views at the level of the registered second-order diagnostic.

It does NOT establish:
- full conditional independence of all plume paths;
- nonlinear content/style identifiability;
- cross-wind or cross-House invariance;
- causal independence.

These stronger claims remain D1/theory questions.