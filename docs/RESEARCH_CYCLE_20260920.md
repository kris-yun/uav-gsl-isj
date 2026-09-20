# Research-cycle checkpoint — 2026-09-20

## Constraint carried forward

Goal: find a paper-level **main scientific idea** for UAV gas-source localization, not an engineering patch. The main idea must come from a recent (2025/2026) remote-domain top-tier scientific/ML line, have a clear theoretical theme, survive physics scrutiny, and show source-discrimination value on available data. SBI is excluded. Pure neural operator / generic foundation model / Mamba / energy-landscape / causal relabeling without a stronger mechanism are not sufficient.

## Already rejected / demoted

- SINN / structural-information neural inverse operator: failed frozen H03 two-source discrimination (3/4 vs Euclidean 4/4; full source-map mean error 6.29 m vs 4.19 m), so no closed-loop continuation.
- Compound-channel / AVC / symmetrizability: useful diagnostic language but too low-level to carry the paper.
- Generic inverse generative modeling / physical world model / physics-informed SSL: retained only as background inspiration, not yet accepted as the paper's organizing principle.

## Current high-value branch

### A. Multiscale non-stationarity / TimeBridge transfer

Source: Liu et al., **TimeBridge: Non-Stationarity Matters for Long-term Time Series Forecasting**, ICML 2025.

Transfer hypothesis:
- short windows should suppress nuisance non-stationarity to expose local plume-response dependencies;
- long windows should preserve non-stationarity when it carries source-specific cross-variable structure;
- for GSL, the key question is not forecasting accuracy but whether the resulting multiscale representation preserves **source identity** across windows, trajectories, and wind regimes.

Required falsification gates:
1. source classification must remain above control after removing absolute wind-speed cues;
2. performance must be stable across multiple window lengths rather than driven by one convenient timescale;
3. source identity must persist across disjoint temporal blocks;
4. representation must improve source discrimination beyond simple concentration/wind summary statistics.

Status: ACTIVE TEST, not yet accepted as main idea.

### B. Physics-guided operator invariance

Hypothesis:
a source is identifiable by a transport-response operator whose invariant structure persists across nuisance changes (wind realization, sampling window, route segment), rather than by raw concentration magnitude.

Candidate observables:
- local ARX / impulse-response coefficients between wind-aligned transport inputs and gas response;
- pole/zero or decay-time summaries;
- normalized gain and phase-lag quantities designed to remove release-rate scale;
- cross-window subspace / coefficient consistency;
- Fisher information or sensitivity of those operator descriptors to candidate source location.

Required falsification gates:
1. same-source operator descriptors must be more stable across disjoint windows than different-source descriptors;
2. invariance must survive wind-speed normalization / residualization;
3. descriptors must discriminate source better than raw feature controls;
4. the effect must hold across multiple public / historical datasets, not only House01/02/03.

Status: ACTIVE CANDIDATE. This is currently more promising as a paper-level physical theme than a direct architecture transfer if the invariance tests pass.

### C. ARX + Fisher as a control and possible mechanism

ARX itself is not accepted as the main innovation. It is used as a low-capacity system-identification probe to test whether a reproducible source-specific transport operator exists.

Fisher information is used as a diagnostic:
- if the source-specific operator is real, candidate-source perturbations should induce structured, repeatable sensitivity in the identified dynamics;
- if Fisher structure collapses after wind-speed controls or across time blocks, reject the operator-invariance hypothesis.

Status: NEXT EXECUTION STEP.

## Immediate continuation point after interrupted session

1. Obtain measured / public multivariate control data suitable for source-ID tests.
2. Fit low-order ARX probes over multiple window sizes.
3. Evaluate same-source vs different-source coefficient/subspace distances.
4. Repeat after explicit wind-speed leakage controls.
5. Compute Fisher/sensitivity representation and cross-window identity consistency.
6. Compare against TimeBridge-inspired multiscale features and simple raw-statistic baselines.
7. If both TimeBridge and ARX/Fisher fail the frozen discrimination gates, reject this branch and resume 2025/2026 remote-domain search rather than forcing a method.
