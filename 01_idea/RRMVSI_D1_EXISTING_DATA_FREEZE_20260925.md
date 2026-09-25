# RR-MVSI D1 Freeze — Existing-D1R Falsification

Date: 2026-09-25

Status: **FROZEN D1 DESIGN; EXISTING DATA ONLY**

Working name: Repeated-Realization Multi-View Source Identifiability (RR-MVSI).

## Claim under test

A repeated-realization representation can identify source-shared plume content while suppressing realization-specific turbulent nuisance, and the learned content geometry transfers to source classes excluded from representation training.

## Data firewall

Use only the completed D1R 168x16 reference bank.

No new GADEN run, no final target and no PMFS closed loop.

## Required evaluation A — fresh realization

Symmetric 8/8 source-complete split.

All model/hyperparameter choices must be made within the training 8 realizations/source.

Primary endpoint: 168-cell true-source log score on the opposite 8.

## Required evaluation B — unseen source classes

Checkerboard 84/84 source holdout crossed with the two 8/8 realization directions.

Representation training cannot use any realization from the heldout source classes.

Source-content prototypes for all 168 candidates must be generated from a source-context mapping, not from heldout-source plume averages.

Primary endpoint: full-168-support true-source log score.

## Mandatory baselines

1. paired-view generalized CCA + RBF-KRR (current strongest linear lower bound);
2. PCA + KRR;
3. pooled covariance whitening + KRR;
4. shrinkage LDA + KRR;
5. ordinary source-coordinate regression;
6. independent zero-hurdle / encounter likelihood;
7. supervised contrastive or ordinary discriminative representation with equal source labels/data budget.

## Candidate second-order requirements

The candidate must not be merely a deeper classifier.

It must explicitly represent:
- source-shared content;
- realization-specific nuisance/private information;
- a source-context encoder that can generate candidate content without repeated releases from that candidate;
- calibrated compatibility producing a normalized 168-cell PMFS posterior.

## D1 ADVANCE

`D1_ADVANCE_RRMVSI_MAINLINE_CANDIDATE` requires all:

1. candidate beats paired-view CCA on mean fresh-realization proper log score in both 8/8 directions;
2. candidate beats paired-view CCA on mean source-heldout proper log score in all four checkerboard x realization directions;
3. candidate does not trade proper score for rank-only gains;
4. representation/source-context mapping is trained without heldout-source plume data;
5. direct GSL prior-art audit does not reveal the same repeated-realization shared-content formulation;
6. theory audit supports a defensible multi-view/content-nuisance interpretation rather than ordinary supervised contrastive learning.

## HOLD

`D1_HOLD_LINEAR_MULTIVIEW_SIGNAL_ONLY` if paired-view CCA remains the strongest method or nonlinear gains are inconsistent.

Linear multi-view nuisance geometry may remain an auxiliary innovation.

## STOP

`D1_STOP_RRMVSI_NOT_DISTINCT_FROM_ORDINARY_REPRESENTATION` if ordinary supervised/contrastive/coordinate methods explain the gain, or if the content/nuisance identifiability assumptions fail.

No scientific rescue by adding new simulation data at D1.