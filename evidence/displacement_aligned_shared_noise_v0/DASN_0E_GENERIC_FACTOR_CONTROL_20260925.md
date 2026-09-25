# DASN 0E — Equal-Dimension Generic Low-Rank Factor Control

Date: 2026-09-25

Status: **2D_GENERIC_FACTOR_INSUFFICIENT; HIGHER-RANK_FACTORS_WARN_OF_NONIDENTIFIABILITY**

## Control design

Use the same D1R, odd/even ridge readouts and two 8/8 directions as DASN 0D.

On the training half, form source-centered full 300-D log(1+ppm) plume residuals and learn an ordinary PCA nuisance basis.

On the diagnostic half, project same-source residuals into the frozen PCA basis.

For each factor rank k, use a deliberately generous pooled linear regression from factor scores to each view's centered 2D localization error, subtract the explained component, and recompute paired shared-error T.

The primary fair control is k=2 because source displacement has two degrees of freedom.

Ranks 1,4,8,16 are sensitivity analyses only.

## Direction A

Pre-control T = 0.02957 m^2.

Residual T after generic factors:
- k=1: 0.02615 m^2; 11.6% removed;
- k=2: 0.02340 m^2; 20.9% removed;
- k=4: 0.02190 m^2; 25.9% removed;
- k=8: 0.01101 m^2; 62.8% removed;
- k=16: 0.00479 m^2; 83.8% removed.

For k=2, 300 pairing-destruction permutations give null 95% interval:
- -0.00822 to 0.00776 m^2;
- exceedance = 0/300.

## Direction B

Pre-control T = 0.023995 m^2.

Residual T:
- k=1: 0.02241 m^2; 6.6% removed;
- k=2: 0.021999 m^2; 8.3% removed;
- k=4: 0.01657 m^2; 30.9% removed;
- k=8: 0.01132 m^2; 52.8% removed;
- k=16: 0.00464 m^2; 80.7% removed.

For k=2, pairing-destruction null 95% interval:
- -0.00729 to 0.00666 m^2;
- exceedance = 0/300.

## Interpretation

The equal-dimensional generic low-rank alternative does not explain the observed shared localization error.

However, higher-rank nuisance factors can absorb most of the signal. At k=16, the residual approaches the permutation-null scale.

This is an important non-identifiability warning:

> a sufficiently flexible generic covariance/factor model can reproduce shared-error structure without any displacement-specific physical latent.

Therefore 0E does NOT prove displacement-aligned noise.

It only shows that the effect is not reducible to one common gain factor or an equally low-dimensional generic 2D nuisance factor.

Next mini-step: **DASN-0F second readout-family replication only**.