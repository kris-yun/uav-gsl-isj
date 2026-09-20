# Candidate M1 — Physics-Guided Operator Invariance for GSL

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / NOT PRIMARY

## Remote-field source

Primary:
- ICLR 2026 — Li et al., *Towards Generalizable PDE Dynamics Forecasting via Physics-Guided Invariant Learning*.
  The paper defines a two-fold PDE invariance principle: ingredient operators and their composition relationships remain invariant across domains and system evolution.

Supporting:
- ICLR 2026 — Germain et al., *A Spectral-Grassmann Wasserstein metric for operator representations of dynamical systems*.
  Dynamical systems are compared through operator spectra/projectors; the metric is sampling-frequency invariant and supports classification/interpolation.

## GSL transfer hypothesis

Represent turbulent source observations in mechanism/operator space rather than raw signal space:

source injection operator
  -> transport/advection-diffusion operators
  -> sensor-response operator
  -> observations.

Across House/wind changes, raw trajectories vary strongly, while some operator ingredients/composition rules may remain stable.

A source candidate would be scored by compatibility of its inferred local dynamics/operator fingerprint with the observed history, ultimately yielding the same source-location probability map.

## Offline operator proxy

A low-order autoregressive operator proxy was fitted to log-concentration histories.

Within the same time block, AR(2) often separates source identity from wind variation better than raw moment statistics:

- H01, 180–240 s:
  AR2 wind/source ratio 0.048 vs raw moments 0.179, both 2/2 source identity.
- H03, 180–240 s:
  AR2 ratio 0.072 vs moments 0.886; AR2 gives 2/2 while moments give 1/2.
- H02, 120–180 s:
  AR2 ratio 0.0007 vs moments 0.038, both 2/2.

This is positive evidence that local dynamical operators can expose source structure hidden in amplitude statistics.

## Hard cross-time test

Train source operator prototypes on fast-wind 120–180 s and evaluate slow-wind 180–240 s.

- H01: AR2 succeeds on supported windows (100% supported-window identity across tested widths).
- H02: the held interval has no >0.01 ppm physical support; admissible verdict is abstention, not localization.
- H03: AR2 fails the persistence test:
  - 10 s supported windows: 50% identity, negative mean source margin;
  - 20 s: 60% identity but still negative mean source margin;
  - 30/60 s: near chance.

Therefore a local operator fingerprint is not a persistent source identity in H03.

## Decision

The ICLR 2026 operator-invariance principle is scientifically strong, but the simple project premise does not support promoting it to M1.

Reason:
- operator structure is source-informative inside some regimes;
- it is not stable enough across time/transport regimes to serve as source identity without an additional regime model;
- adding regime segmentation would turn the candidate into a larger speculative stack.

STATUS = RESERVE THEORY / NOT PRIMARY.

This candidate may later supply a diagnostic or auxiliary metric, but no neural-operator main contribution is authorized.
