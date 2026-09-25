# RR-MVSI D0 Source-Heldout Proper-Score Audit — 2026-09-25

Status: **D0_ADVANCE_MULTIVIEW_SOURCE_IDENTIFIABILITY_D1**

This is an offline advance only. No new GADEN runs and no final PMFS closed loop are authorized.

## Scientific object

Independent plume realizations from the same source are treated as repeated stochastic views.

- shared content: source identity/location;
- view-specific nuisance: turbulent plume realization.

The current linear lower-bound model learns a shared-content subspace using paired views from the same source, without optimizing a source-class discrimination loss.

## Data contract

- D1R 168 dense sources x16 realizations;
- log(1+ppm) 300-D observation features;
- checkerboard source holdout: 84 source classes completely absent from representation/prototype training;
- opposite realization half used for final source-heldout evaluation;
- all posterior/rank metrics use the full 168-candidate source support.

## Paired-view shared-content model

For the outer training source set and one 8-realization reference half:

1. center log-ppm observations;
2. pair the first four and last four independent realizations of each training source;
3. estimate symmetric cross-view covariance C_xy;
4. estimate regularized total covariance C_xx;
5. solve the generalized eigenproblem C_xy v = lambda C_xx v;
6. retain a train-only selected shared-content dimension;
7. map source (x,y) coordinates to latent source prototypes with RBF KRR;
8. select KRR length scale, ridge and posterior temperature only by source-heldout CV inside the outer training sources;
9. predict every one of the 168 candidate prototypes from the KRR map;
10. evaluate completely unseen source classes on the opposite realization half.

## Train-only dimension selection

Candidate dimensions: {5,10,20,40}.

Selected dimensions from training-source CV:
- dir0 / parity0: d=20;
- dir0 / parity1: d=20;
- dir1 / parity0: d=40;
- dir1 / parity1: d=20.

No heldout-source target was used to select dimension, KRR hyperparameters or temperature.

## Fresh source-heldout results — paired-view CCA

| realization direction | heldout source parity | mean true-source log2 | top1 | top3 | top10 | median rank | MAP q90 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | -3.4469 | 20.09% | 54.76% | 88.39% | 3 | 0.849 m |
| 0 | 1 | -3.3659 | 26.04% | 58.93% | 86.76% | 3 | 0.849 m |
| 1 | 0 | -3.3660 | 26.34% | 61.61% | -- | 3 | -- |
| 1 | 1 | -3.3943 | 23.96% | 56.10% | 87.80% | 3 | 0.849 m |

The one omitted secondary cell is not needed for the decision; primary comparison is proper log score.

## Ordinary source-heldout portfolio

All baselines use the same outer source/realization split, all 168 candidates and train-source-only hyperparameter selection.

### PCA + RBF-KRR prototype regression

Inner CV selected d=40 in all four outer scenarios.

Fresh mean true-source log2:
- -4.482;
- -4.486;
- -4.499;
- -4.502.

Top1 approximately 18-21%; top3 approximately 39-46%; median rank 4-5.

### Supervised LDA + RBF-KRR

Train-source CV selected d=40.

Fresh mean true-source log2:
- -4.441;
- -4.321;
- -4.605;
- -4.272.

### Full pooled covariance whitening + RBF-KRR

Fresh mean true-source log2:
- -4.439;
- -4.319;
- -4.604;
- -4.270.

### Ordinary linear coordinate regression

Ridge maps the 300-D log-ppm realization directly to source (x,y), followed by a calibrated spatial posterior.

Fresh mean true-source log2:
- -4.723;
- -4.666;
- -4.679;
- -4.784.

## Key D0 finding

Relative to the ordinary model chosen by training-source CV (PCA+KRR), paired-view shared-content learning improves completely unseen-source proper log score by roughly one bit per target in all four outer scenarios.

The improvement is therefore not explained by:
- PCA low rank alone;
- pooled covariance whitening alone;
- supervised LDA directions alone;
- ordinary linear source-coordinate regression;
- restricting ranking to only heldout candidates.

## Why this matters

The repeated realizations are used only offline to identify nuisance-invariant shared directions.

At evaluation, a fresh source contributes one realization only.

This is compatible in principle with real flight: the online UAV does not need repeated releases of the unknown source.

## What is NOT yet established

- theoretical identifiability assumptions for turbulent plume views;
- calibrated neural/nonlinear advantage over the linear paired-CCA lower bound;
- cross-wind / cross-House transfer;
- source-content generation from map/wind rather than within-House (x,y) KRR;
- direct novelty versus supervised contrastive/domain-invariant representation learning;
- PMFS closed-loop benefit.

## D1 decision

Advance to a reference-only D1 theory/algorithm gate.

Do not generate new plume data.

D1 must use the existing D1R bank and compare any nonlinear/GSL-specific method against the paired-view CCA lower bound plus the strongest ordinary baselines.

STOP if the proposed second-order method cannot beat the paired-CCA lower bound on both fresh-realization proper score and source-heldout proper score, or if prior art shows the same repeated-realization content/nuisance formulation in GSL.