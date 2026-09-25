# IPTO Final Mainline Decision — 2026-09-25

Decision: **STOP_IPTO_AS_MAIN_INNOVATION**

No new GADEN/CFD acquisition is authorized for IPTO.

## Why

After the Pro theory review and the source-contrast refinement, the broad IPTO mechanism can be absorbed by established frameworks:

- Bayesian/GP/Neural-Process context calibration;
- in-context operator learning;
- task-aware / goal-oriented operator learning;
- goal-oriented inference for advection-diffusion;
- posterior-aware surrogate modeling.

The final narrowed idea — learning only source-contrast-relevant operator directions — is a GSL-specific task choice, but not a sufficiently distinct mother-theory innovation by itself.

Historical M4 and D1R/LSC evidence remain useful:
- M4 shows field error and source-identifiability objectives can diverge;
- LSC shows local stochastic source distinguishability predicts fresh confusion/proper score.

These become design/evaluation constraints for future routes, not justification for IPTO as the main innovation.

## Reusable principles

Retain:
- local source likelihood-ratio / distinguishability as the inverse-problem task geometry;
- field-MSE is insufficient as a GSL world-model objective;
- sparse real-site calibration is a deployment requirement;
- context must change relative source evidence, not only common-mode plume statistics.

## Next candidate class

Audit statistical-experiment sufficiency / Blackwell-Le Cam representation theory:

> learn or identify an observation representation that preserves source-decision information (likelihood-ratio structure) while discarding plume/environment nuisance.

This candidate must be killed if it reduces to ordinary LDA, supervised contrastive learning, knowledge distillation, or standard sufficient-representation transfer.