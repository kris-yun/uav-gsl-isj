# PRO6 RR-MVSI UPDATE — Strong Source-Heldout Proper-Score Signal

Date: 2026-09-25

Primary thread has completed a stricter D0 before any new simulation.

## New outer evaluation

Each target source class is completely absent from representation/prototype training.
Posterior support remains all 168 candidate source cells.
Representation/prototype/KRR/temperature choices use training sources only.

Paired-view generalized CCA uses same-source independently seeded plume views but no source-class discrimination objective.

Dimension is selected from {5,10,20,40} by training-source CV.

Selected dimensions across the four source-parity x realization directions:
- 20, 20, 40, 20.

Fresh source-heldout mean true-source log2:
- -3.4469
- -3.3659
- -3.3660
- -3.3943

Training-source CV selects PCA+RBF-KRR as the ordinary champion in all four scenarios.
Its corresponding fresh log2 scores are approximately:
- -4.482
- -4.486
- -4.499
- -4.502

Aggregate paired gain over all 168x16 fresh targets:
- mean +1.0990 bits/target;
- median +1.3201 bits;
- positive for 81.32% of targets;
- source-wise mean positive for 81.55% of sources;
- fixed-panel within-source realization bootstrap 95% interval: [+1.0612,+1.1361] bits.

Ordinary full-covariance whitening, supervised LDA+KRR and direct linear coordinate regression are also weaker on proper score.

## Mechanism audit

D1R log-ppm source-conditioned residual energy is strongly heteroscedastic:
- first8/last8 source variance-order Spearman ~0.584;
- source residual-energy 10-90% range ~1.23 to 10.01;
- max ~21.26.

However, after independently centering the two 8-realization halves, cross-half residual covariance is near finite-sample random-source null:
- observed relative Frobenius mean ~0.071;
- random-source null median ~0.068.

This supports, at second-moment level only, the model:
Y_sr = mu_s + epsilon_sr
with source-dependent Sigma_s but weak cross-realization residual covariance.

Therefore cross-view covariance can isolate Cov_s(mu_s) without requiring homoscedastic nuisance.

## Primary-thread theorem candidate

For two conditionally independent plume views:

Cov(Y1,Y2) = Cov_s(mu_s) = B
Cov(Y) = B + E_s[Sigma_s].

The generalized eigenvalue lambda(v)=v'Bv / v'(B+W)v measures reproducible source-shared variance fraction.

CCA itself is NOT the novelty claim.

Candidate novelty bundle:
- repeated stochastic plume realizations as source-shared multi-views;
- heteroscedastic nuisance allowed;
- nonlinear shared-content/private-nuisance representation;
- source/map/wind context encoder generating content codes for unseen candidate sources;
- one-view online inference;
- calibrated PMFS posterior.

## Important adjacent prior art discovered

Generic gas/olfactory representation disentanglement is no longer empty territory:
- 2026 Sensors and Actuators B: device-aware feature disentanglement for cross-device gas recognition;
- 2026 visuo-olfactory work: contrastive odor representation and localization.

So generic 'disentanglement' or 'contrastive olfaction' cannot be the novelty.

## What I need in your pending audit

Please directly decide:
1. whether the heteroscedastic repeated-view moment bridge is theoretically defensible;
2. which ICML/ICLR identifiability assumptions map and which fail;
3. whether this is genuinely distinct from deep CCA / supervised contrastive learning;
4. what nonlinear second-order objective can beat the paired-CCA lower bound without becoming a classifier;
5. what exact existing-D1R D1 gate should be used;
6. whether source-context encoding from map/wind can make the method viable without a full real-environment source bank.

No new simulations.
No PMFS closed loop yet.