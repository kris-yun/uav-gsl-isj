# Theory and claim boundary

## Observation model

At source update `t`, PMFS supplies one measured hit-probability field `y`, a
confidence vector `c`, a prior `pi`, and online response maps `g_s` for the
current candidate sources. The algorithm consumes one chemical concentration
channel; position and wind are state variables used by PMFS, not extra gas
channels.

Let `W = diag(sqrt(c / sigma^2))` and let

`D = [g_s - sum_r pi_r g_r]_s`

be the source-contrast matrix. Perturbing wind direction, speed, velocity noise,
plume realization and the declared sensor response produces centred nuisance
atoms `A` at the same candidate support.

## Metric-consistent decomposition

The scientifically relevant geometry is the observation-noise metric. MC-SCSP
therefore forms `D_w = W D` and `A_w = W A`, computes rank-revealing orthonormal
bases, and decomposes

`A_w = P_span(D_w) A_w + (I - P_span(D_w)) A_w`.

Only the second term enters the structured covariance. It is transformed back
to measurement coordinates before evaluating the likelihood, avoiding a second
application of `W`. This preserves the source-contrast subspace while allowing
variance along nuisance directions that cannot be explained as a source change.

The overlap is

`rho = ||Q_D^T Q_A||_F^2 / min(rank(D_w), rank(A_w))`.

The frozen A4 posterior is

`p_A4 = (1-rho) p(y | s, B_perp) + rho pi`.

## What is new here

The borrowed scientific principle is nuisance/foreground deprojection under an
explicit noise metric. The second-step contribution is its candidate-response,
online PMFS form with source-subspace protection and metric-consistent
rank-revealing geometry. Candidate maps are generated online from the current
PMFS state; there is no historical leak catalogue or environment-specific
lookup library.

## What cannot be claimed yet

- This is not causal source identification. The previous causal line established
  action response but failed source-location identifiability.
- A pass on H03 seed11 is development evidence only.
- Matching or beating native PMFS is insufficient: the corrected geometry must
  also beat the legacy projection and plain matched-source filter on the frozen
  mechanism metrics.
- A real ethanol/VOC flight can test transfer, but cannot convert a failed
  simulation mechanism into a main innovation.

