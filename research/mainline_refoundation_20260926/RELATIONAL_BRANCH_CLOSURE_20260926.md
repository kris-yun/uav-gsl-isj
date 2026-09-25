# Mainline Refoundation after RIA-A1 and RPO-G0

Date: 2026-09-26

## Frozen decisions

- JTD mainline: STOP.
- NPG mapping: STOP.
- SPX: diagnostic only; neither frozen source-only nor probe-only dominance rule explains the crossed result.
- RIA-A0: retain `RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED`.
- RIA-A1: `RIA_A1_MIXED_SIGNAL_AND_VARIABILITY`; do not relax the pre-registered dominance thresholds.
- RPO-G0: `RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES`.

## Interpretation

RIA-A1 is signal-skewed in behavioral association but formally mixed in contribution magnitude.

Therefore the relational-observability branch is retained as an auxiliary scientific finding:
- probe layout changes observation-level source identifiability;
- between-source signature separation is strongly associated with bounded heldout discrimination;
- within-source variability is not sufficient to explain the effect;
- the tested hand-crafted source–probe–flow descriptor cannot prospectively predict it across space.

This branch is no longer eligible to become the paper's main innovation without a genuinely new mechanism and fresh evidence.

## Governance

Do not run RIA-A2/RPO-G1.
Do not rescue RPO using nonlinear regressors, revised standardization, new path features, or relaxed thresholds.
Do not reopen JTD/NPG.
Do not generate new plume for this branch.
H01 DEV and House03 remain sealed.

## Fresh mainline search problem

Return to the project-level failure:

> fixed environment-specific statistics/operators repeatedly work locally and fail under environment/observation shift.

A new mainline must therefore learn or infer the current physical observation operator from sparse context, rather than assume a fixed temporal/covariance/transport representation.

Primary search family:
`partial-observation physical world models / in-context operator learning`.

This is a NEW search family, not a continuation of RIA/JTD.