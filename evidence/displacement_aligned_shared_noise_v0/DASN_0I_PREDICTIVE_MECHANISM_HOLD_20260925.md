# DASN 0I — Predictive Mechanism Test and Decision

Date: 2026-09-25

Decision: **DASN_HOLD_SHARED_DISPLACEMENT_GEOMETRY_NOT_INFORMATION_LIMIT**

No new likelihood, final target, or GADEN simulation is authorized for DASN.

## Question

Does a source's displacement-aligned shared plume-noise strength, estimated only from one realization half, predict how difficult that source will be to localize on the opposite fresh half?

This is the key predictive consequence required before interpreting the geometry as information-limiting noise.

## Training-half source-specific aligned shared index

For each source and each 8-realization half:
- estimate odd/even local source-response Jacobians from that half only;
- project same-source plume residuals into equivalent local source displacement using the frozen ridge-regularized Jacobian inverse;
- compute the source-specific odd/even paired shared displacement statistic T_J,s.

## Reproducibility of the source-specific geometry

Across the 168 sources, first8 versus last8 T_J,s:
- Spearman rho = 0.4812;
- Pearson r = 0.1909.

Thus source ordering of the aligned shared component is moderately reproducible, although magnitude agreement is weak.

## Fresh localization-difficulty prediction

Fresh difficulty is source-wise mean squared localization error from an ordinary full-30-probe ridge coordinate decoder trained on the opposite half.

First8 T_J,s -> last8 fresh localization MSE:
- Spearman rho = -0.1213;
- Pearson r = -0.0953.

Last8 T_J,s -> first8 fresh localization MSE:
- Spearman rho = -0.0619;
- Pearson r = -0.1262.

After controlling for training-half total residual variance, global gain variance, and the frozen true-boundary label:
- partial Pearson = -0.1506 for first8 -> last8;
- partial Pearson = -0.1653 for last8 -> first8.

## Related marginal aligned-variance check

A separate training-half displacement-equivalent variance index also failed to predict larger fresh localization error; associations were weak and negative.

## Interpretation

DASN 0A-0H established a real geometric phenomenon:
- same plume realization causes shared localization shifts across disjoint probe views;
- pairing destruction removes the signal;
- common gain does not explain it;
- an equal-dimensional generic 2D factor does not explain it;
- the effect survives a second decoder family;
- it is not boundary dominated;
- source-matched local Jacobians capture substantially more coherent displacement-like error than source-shuffled Jacobians.

However, 0I fails the required mechanistic prediction:

> sources with larger independently estimated displacement-aligned shared noise are not harder to localize on fresh plume realizations.

Therefore the observed alignment cannot currently be promoted to an information-limiting localization mechanism.

High-rank generic factors also remain capable of absorbing much of the covariance, reinforcing the non-identifiability caution.

## Decision

**HOLD, not ADVANCE.**

Retain as a potentially useful auxiliary plume-geometry observation.

Do not claim:
- information-limiting correlations as the main GSL mechanism;
- a physical displacement-noise latent;
- DASN as the main innovation;
- justification for a new covariance likelihood.

## Mainline consequence

The next mechanism search should ask which pre-observation quantity actually predicts fresh source-localization difficulty under the D1R bank.

A natural next first-principles screen is the local signal-versus-noise / Fisher-information geometry:

- local source sensitivity strength and conditioning;
- source-conditioned stochastic variance projected through that sensitivity;
- whether a frozen information metric predicts fresh localization error better than raw variance, gain, or geometry alone.

This should be tested as a mechanism screen before attaching any new mother-theory label.