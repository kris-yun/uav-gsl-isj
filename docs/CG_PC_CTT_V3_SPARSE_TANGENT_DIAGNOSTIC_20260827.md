# CG-PC-CTT V3 sparse local-tangent diagnostic — H03 real bank

Data boundary: frozen House03 V2 product `phi[10,206,8,626]`; 206 unique physical source coordinates. No V2 threshold was changed and no source truth was used in the statistic.

## Full-support 2-D tangent result

Using Delaunay physical neighbours and the V2 pair-difference feature whitener, a member-specific local response derivative was fitted for each source position. The cross-member 2x2 tangent information matrix is

`F_i = sum_{m!=n} B_{i,m} B_{i,n}^T / [M(M-1)]`,

where `B` is the whitened local derivative with respect to physical `(x,y)` source displacement.

On all ten H03 contexts at full 626-cell support:

- fraction of physical source locations with `lambda_min(F_i)>0`: 1.0 in every context;
- median `gamma_xy = sqrt(lambda_min/lambda_max)`: approximately 0.469–0.473;
- context-wise 5th percentile `gamma_xy`: approximately 0.143–0.149.

Thus the full H03 forward field provides replicated local sensitivity in both physical source-coordinate directions.

## Sparse-support stress

Using fixed random feature subsets only as a diagnostic, the mean fraction of source locations with positive second tangent eigenvalue and the mean context median `gamma_xy` were approximately:

| sampled support Q | fraction lambda_min>0 | mean median gamma_xy |
|---:|---:|---:|
| 1 | 0.000 | 0.000 |
| 2 | 0.0227 | 0.000 |
| 4 | 0.2822 | 0.000 |
| 8 | 0.5215 | 0.0429 |
| 16 | 0.8057 | 0.2594 |
| 32 | 0.9526 | 0.3964 |
| 64 | 0.9848 | 0.3983 |
| 128 | 0.9977 | 0.4309 |
| 256 | 0.9998 | 0.4582 |
| 626 | 1.000 | 0.4713 |

Interpretation: sparse observation support causes a genuine geometric rank loss in the two-dimensional physical source inverse problem. With one feature, a 2-D source cannot have rank-2 local information. A small number of features can still be redundant or directional, so raw point count is not an identifiability guarantee.

This diagnostic motivates the V3 rule that current source resolution must be based on observation-conditioned local geometry rather than global `rank_k=3`.
