# Mainline Decision After E4B

Date: 2026-09-25

Status: **STOP FIXED/FACTORIZED ENVIRONMENT-INVARIANCE SEARCH; HOLD CONTEXT-ADAPTIVE MAINLINE FOR THEORY/BASELINE AUDIT ONLY**

## Frozen failures

- E4A single reusable deformation subspace: STOP.
- E4B factorized speed/family deformation: STOP.

Do not reopen these routes by:
- changing rank;
- changing normalization;
- changing thresholds;
- adding seeds;
- relabeling them as a neural model.

## Four-wind H02 postmortem

Across all four H02 canonical winds, 300-D log1p observations have approximate balanced variance fractions:
- source main effect 67.8%;
- wind main effect 8.7%;
- source x wind interaction 20.5%;
- seed residual 3.0%.

Thus source identity is strong but transport-operator interaction is much larger than plume-seed noise.

A fixed cross-wind discriminant model remains unstable.

However an ordinary rank-2 context factor baseline, trained on three winds and given only two known target-wind context sources x two realizations, improves completely non-context query-source prediction and calibrated source NLL in all four leave-one-wind-out postmortem directions.

Therefore:

> target-environment context is empirically useful within a fixed House, but this fact is already captured by an ordinary low-rank adaptation baseline and is not a main innovation.

## Cross-House problem

H01/H02/H03 have different source coordinates and different geometry-selected probe coordinates.

A fixed 300-D H02 latent basis has no valid semantic correspondence across Houses.

Therefore H01 DEV must NOT be unsealed merely to test an H02 vector-space factor model.

## Mainline scientific boundary

Any future candidate must simultaneously satisfy:

1. coordinate/geometry-aware representation across different Houses and irregular probe sets;
2. small target-environment context rather than dense source banks;
3. normalized PMFS-style source posterior as the inverse-task output;
4. direct comparison to ordinary low-rank factor adaptation, Neural Processes/GP calibration, and modern coordinate-aware operator learning;
5. a GSL-specific mechanism beyond generic context-conditioned function/operator learning;
6. a pre-data prediction that can be tested on the still-sealed H01 DEV;
7. eventual untouched House03 confirmation.

## Current data protection

- H01 DEV remains sealed.
- both House03 environments remain sealed.
- no new plume is authorized.

## Next action

Zero-simulation theory/prior-art/baseline audit only.

Candidate literature families to attack, not automatically adopt:
- in-context operator learning;
- resolution-independent / arbitrary-sensor neural operators;
- Neural Processes and GP/Bayesian calibration;
- latent neural operators;
- irregular-domain graph/set operators.

Search question:

> Is there a source-localization-specific, task-relevant adaptation principle that is structurally different from these generic baselines and is supported by the observed environment interaction?

If no such distinction can be specified before H01 DEV is opened, STOP IPTO/context adaptation as the main innovation rather than spending the holdout.