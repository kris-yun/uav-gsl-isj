# RR-MVSI Corrected D1 Decision — 2026-09-25

Decision: **D1_STOP_RRMVSI_NOT_DISTINCT_FROM_ORDINARY_REPRESENTATION**

This document supersedes the earlier exploratory D0 advance note.

## Why correction was necessary

An earlier exploratory source-heldout implementation reported roughly +1 bit/target for paired-view CCA over PCA/KRR.

After rebuilding all methods under one implementation with identical:
- log(1+ppm) inputs;
- full 168-candidate posterior support;
- source-heldout checkerboard splits;
- train-source-only KRR prototype mapping;
- train-source-only temperature calibration;
- consistent latent metric handling;

that large advantage does not reproduce.

## Corrected paired-view CCA versus ordinary baselines

Fresh source-heldout proper log2 scores:

direction0 parity0:
- raw/KRR: -4.4814
- PCA/KRR: -4.4819
- paired CCA/KRR: -4.4990

direction0 parity1:
- raw/KRR: -4.4858
- PCA/KRR: -4.4863
- paired CCA/KRR: -4.4017

direction1 parity0:
- raw/KRR: -4.4986
- PCA/KRR: -4.4992
- paired CCA/KRR: -4.2588

direction1 parity1:
- raw/KRR: -4.5011
- PCA/KRR: -4.5016
- paired CCA/KRR: -4.9107

Paired CCA therefore wins in only two of four source-heldout scenarios and loses in the other two.

## Nonlinear repeated-view test

A small two-tower model was then tested using only:
- same-source paired-view agreement;
- source-context alignment;
- anti-collapse variance/covariance regularization;
- no 168-class source softmax.

All hyperparameters and temperature were selected without heldout-source plume data.

Fresh source-heldout proper log2:
- -4.7708
- -4.6303
- -4.5511
- -4.7778.

These fail to beat the strongest raw/PCA+KRR baseline in all four scenarios.

Rank metrics improve in some cases, but proper score does not.

## Scientific interpretation

Repeated plume views do contain source-shared second-order structure, and D1R supports source-dependent heteroscedasticity with weak cross-realization residual covariance.

However, under the frozen D1 rule, a mainline repeated-view identifiability method must improve calibrated source likelihood, not only ranks.

It does not.

Therefore RR-MVSI is stopped as the main innovation.

The heteroscedasticity/residual-independence mechanism audit remains reusable background evidence.