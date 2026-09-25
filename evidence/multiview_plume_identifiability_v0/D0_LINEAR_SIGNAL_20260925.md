# Multiview Plume Identifiability D0 Signal — 2026-09-25

Status:

**D0_POSITIVE_SIGNAL_MULTIVIEW_NUISANCE_STRUCTURE**

This is not yet a GO for a neural mainline and does not authorize new GADEN runs.

## Scientific reframing

For a fixed source S, independent stochastic plume realizations

Y^(1), ..., Y^(R)

can be treated as repeated noisy views of a shared latent content variable
(source identity/location) under realization-specific turbulent nuisance.

This suggests a far-domain representation-learning formulation:

source identity = shared content

turbulent plume realization = view-specific style / nuisance.

The goal is not to average realizations online.

The goal is to learn, offline, which directions of observation variation are
shared source information and which are realization nuisance, then apply the
learned invariant representation to a single fresh realization.

## Pre-data theory families

Relevant far-domain theory candidates include:

- Kori, Toni & Glocker, ICML 2025,
  *Identifiable Object Representations under Spatial Ambiguities*;
- Shrestha & Fu, ICLR 2025,
  *Content-Style Learning from Unaligned Domains: Identifiability under Unknown Latent Dimensions*;
- Wu et al., ICLR 2025,
  *Unsupervised Disentanglement of Content and Style via Variance-Invariance Constraints*;
- multi-view causal representation identifiability results from ICLR 2024 as
  supporting theory.

Direct GSL/olfaction searches did not reveal an obvious use of this
content-vs-plume-realization identifiability formulation. This remains to be
audited more deeply before promotion.

## D1R linear diagnostic 1: same-source fresh realizations

Train on 8 realizations/source and test on the other 8.

Binary encounter features, ordinary shrinkage LDA:

After train-only temperature calibration:

- test top-1: about 29.5-31.6%;
- top-3: about 59%;
- top-10: about 89%;
- median rank: 3;
- mean true-source log score: about -3.22 to -3.30 bits.

Independent Bernoulli likelihood:

- top-1: about 24.9-26.6%;
- top-3: about 51-53%;
- top-10: about 78-80%;
- median rank: 3;
- mean true-source log score is much worse because the independent model is
  badly overconfident under correlated observations.

## D1R linear diagnostic 2: raw log-ppm views

Using log(1+ppm) features with the same shrinkage-LDA and train-only
temperature calibration:

Split A:
- top-1 = 43.15%;
- top-3 = 70.24%;
- top-10 = 90.48%;
- median rank = 2;
- mean true-source log score = -2.807 bits.

Split B:
- top-1 = 41.52%;
- top-3 = 67.63%;
- top-10 = 90.85%;
- median rank = 2;
- mean true-source log score = -2.947 bits.

This is a large fresh-realization signal from a deliberately ordinary linear
shared-covariance model.

It shows that source-discriminative information exists in directions that are
obscured when the 300 coordinates are modeled independently.

## D1R linear diagnostic 3: covariance transfers to unseen source classes

A stricter source-held-out test was run.

For each checkerboard split:

- 84 source classes are completely removed;
- source means for the 84 unseen classes are predicted only by 4-neighbor
  interpolation from training-source means;
- the nuisance covariance is estimated only from residuals of training sources;
- evaluation uses the opposite 8-realization half of the unseen sources.

Euclidean scoring with interpolated means:

- top-1 about 7.9-10.9%;
- top-3 about 32.4-36.0%;
- median rank 5-6;
- MAP-error q90 about 1.08-1.23 m.

Full Ledoit-Wolf shared-covariance whitening learned only from the other source
classes:

- top-1 about 15.6-21.6%;
- top-3 about 55.8-59.4%;
- top-10 about 82.1-82.4%;
- median rank 3;
- MAP-error q90 about 0.67-0.89 m.

Therefore the realization-nuisance covariance is not merely source-specific:
it transfers across completely unseen source classes.

This is the most important D0 positive signal.

## Important limitation

Under source-held-out probability calibration, full covariance whitening improves
ranking strongly but does not yet improve mean proper log score over a simple
Euclidean interpolated-mean model.

Therefore the current evidence supports:

- transferable nuisance geometry;
- improved source ordering;
- a multi-view/invariant-representation research direction.

It does not yet establish a calibrated probabilistic source-posterior method.

## What must happen next

Before any new simulation:

1. audit GSL prior art for contrastive, invariant, disentangled or multi-view
   source representation;
2. derive the correct shared-content / realization-nuisance identifiability
   assumptions for plume data;
3. design a reference-only nonlinear or generalized-eigen representation that
   is explicitly compared against:
   - shrinkage LDA;
   - pooled covariance whitening;
   - independent likelihood;
   - ordinary supervised classification;
4. retain PMFS-style calibrated source probability output;
5. test with existing D1R first.

STOP if the nonlinear method cannot beat the linear shared-covariance baseline
on untouched reference folds and source-held-out tests.
