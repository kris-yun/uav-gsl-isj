# SC-SRO D1 Existing-Data Freeze — 2026-09-25

Status: FROZEN OFFLINE D1, NO NEW SIMULATION

## Claim

A source-conditioned correlated stochastic response operator can improve source-heldout microcell likelihood beyond mean-only, diagonal-uncertainty and source-independent covariance models.

## Data

Only D1R 168x16x10x30 pooled data.

## Outer evaluation

Four scenarios:
- checkerboard source parity 0 held out, reps1-8 train / reps9-16 test;
- checkerboard source parity 1 held out, reps1-8 train / reps9-16 test;
- parity 0 held out, reverse realization direction;
- parity 1 held out, reverse realization direction.

Representation/model fitting never uses plume data from heldout source classes.

Posterior support is always all 168 candidates.

## Mandatory baselines

1. mean-only raw/PCA + RBF-KRR;
2. source-conditioned scalar variance;
3. shared full covariance / Mahalanobis;
4. shared low-rank covariance;
5. diagonal heteroscedastic Gaussian source field, DGSE-like uncertainty control;
6. source-conditioned low-rank covariance KRR lower bound.

## Candidate D1 model

Use a compact correlated stochastic operator with:
- source-context branch encoder;
- observation-query trunk/basis;
- mean response mu_theta(c,q);
- PSD covariance K_theta(c) = Phi_theta diag(lambda_theta(c)) Phi_theta^T + tau_theta(c) I;
- exact Gaussian/Student-t low-rank log likelihood with Woodbury evaluation;
- train-only calibration;
- no target-dependent choice of covariance rank or temperature.

An acceptable first D1 implementation may keep Phi fixed from training residuals and learn only nonlinear source-context maps for mean and modal amplitudes. A stronger second implementation may learn the basis jointly, but only if the first passes.

## Primary endpoint

Mean full-168-support true-source log2 score on completely heldout source classes.

## ADVANCE

`D1_ADVANCE_SCSRO_MAINLINE_CANDIDATE` requires:
1. candidate beats shared-low-rank covariance baseline in all four outer scenarios;
2. candidate beats source-conditioned low-rank KRR lower bound in at least three of four scenarios and is not worse by more than 0.02 bit in the fourth;
3. paired realization-bootstrap lower bound for candidate-vs-shared-low-rank is >0 in all four;
4. gains are proper-score gains, not rank-only;
5. GSL prior-art audit confirms no existing source-conditioned correlated stochastic-operator formulation.

## HOLD

`D1_HOLD_LINEAR_CORRELATED_UNCERTAINTY_ONLY` if the linear source-conditioned low-rank model remains best.

## STOP

`D1_STOP_SCSRO_NOT_DISTINCT_FROM_STANDARD_UQ` if diagonal/global covariance or ordinary mean modeling explains the gain, or the nonlinear operator cannot transfer to heldout source classes.

No rescue by generating new simulation data at D1.