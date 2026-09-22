# Reactive Flux Matching transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO — METHOD-DOMAIN DEGENERACY**

## Mother idea

2026 rare-event physics / Transition Path Theory:
*Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events*, arXiv:2606.06295.

The paper learns directed reactive current and a potential/reaction coordinate from transition-path ensembles. Under detailed balance, the potential reduces to a logit transform of the forward committor.

## GSL transfer tested

Using sensor-defined basins:
- A: measured gas <= 1e-6 ppm
- B: measured gas >= 0.1 ppm

For every complete A->B or B->A transition path, each source candidate's simulated hit-probability trajectory q_s(t) was scored by directed reactive progress:

  direction * [q(end)-q(start)] / total_variation(q)

so a correct source should increase q on A->B paths and decrease q on B->A paths.

Geometry-only and plume-minus-geometry variants were also checked.

## Failure

Old House03 seed0 contains only one usable A->B reactive transition. Under the frozen directionality score all candidate hypotheses collapse to the same score, so the source posterior is undefined.

This is a legitimate case, not missing data.

Following the HCMC independent-failure lesson, no epsilon, fallback, fusion with committor score, or alternative flux statistic was introduced after observing the degeneracy.

## Decision

`REACTIVE_FLUX_MATCHING_GSL_TRANSFER_NO_GO_20260922`

The parent committor-consistency route remains a separate HOLD candidate; the reactive-flux-only refinement is rejected.
