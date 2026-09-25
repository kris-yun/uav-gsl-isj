# SC-SRO D1 Decision — 2026-09-25

Decision: **D1_HOLD_LINEAR_CORRELATED_UNCERTAINTY_ONLY**

No new GADEN runs, dense cubes, stronger neural architecture, or closed-loop experiment are authorized for SC-SRO as the mainline.

## What survived

D1R establishes a real source-conditioned correlated stochastic signal.

Compared with a shared low-rank covariance model, allowing the low-rank turbulence-mode amplitudes to vary with source context improves completely source-heldout proper log score in all four outer scenarios:
- +0.0209 bit/target, 95% realization-bootstrap [0.0150, 0.0270];
- +0.0635 bit/target, [0.0586, 0.0683];
- +0.0852 bit/target, [0.0679, 0.1029];
- +0.0564 bit/target, [0.0498, 0.0633].

Scalar source variance alone does not explain the gain.
A shared full covariance / Mahalanobis model does not explain the gain.

Thus correlated low-rank stochastic plume structure is reusable as an auxiliary likelihood/UQ component.

## Frozen D1 candidate

The preregistered first nonlinear D1 model used:
- low-rank source mean basis;
- 5 shared residual covariance modes;
- a small source-context MLP predicting mean coefficients, mode amplitudes and residual variance;
- exact low-rank Gaussian likelihood;
- source-only inner calibration;
- no heldout-source plume data.

## Nonlinear D1 result

Fresh source-heldout mean true-source log2 scores:
- direction0 parity0: -5.614;
- direction0 parity1: -6.351;
- direction1 parity0: -5.481;
- direction1 parity1: -5.437.

These are substantially worse than the linear source-conditioned low-rank KRR lower bound:
- -4.407;
- -4.390;
- -4.306;
- -4.333.

The nonlinear context operator also loses ranking quality.

## Decision logic

The frozen D1 protocol stated that a stronger jointly learned operator should not be attempted unless the compact first D1 implementation passes.

It did not pass.

Therefore no architecture escalation is allowed.

## Scientific interpretation

The data support a useful auxiliary result:

> Source-dependent amplitudes of shared correlated plume-noise modes carry transferable source information.

They do not support the stronger mainline claim that a stochastic neural/operator architecture is needed or improves source localization.

Recent prior art also narrows novelty:
- neural operators have entered GSL (IROS 2026);
- deep probabilistic GSL already models heteroscedastic field uncertainty (arXiv:2608.16221), although with diagonal Gaussian fields and no spatial correlation.

SC-SRO should therefore be retained as a possible auxiliary correlated-UQ module, not the paper's main scientific thesis.