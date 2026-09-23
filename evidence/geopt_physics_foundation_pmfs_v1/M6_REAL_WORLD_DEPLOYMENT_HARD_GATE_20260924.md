# M6 Real-World Deployment Hard Gate

Date: 2026-09-24
Branch: `research/m6-geopt-house02-dev-v1`

Status: **FROZEN BEFORE ANY POSITIVE G1 RESULT**

## Purpose

M6 is intended for UAV gas-source localization, not only GADEN surrogate
prediction. A simulation-positive result is therefore insufficient.

The deployment path is frozen now so later positive simulation results cannot
silently weaken real-world requirements.

## D0 — cross-physics transfer screen

Development only.

- GeoPT pretrained vs identical random-frozen backbone.
- GADEN / controlled field data may use ground-truth wind.
- Purpose: test whether the pretrained representation contains transferable
  information.
- No real-world claim.

## D1 — mechanism and source-identity screen

Required only if D0 is positive.

- wind shuffle;
- geometry/SDF corruption;
- source-adapter shuffle;
- dense geometry-only candidate bank.

Primary endpoint:
truth-containing source-candidate rank / rank margin.

Field MSE alone cannot advance M6.

## D2 — cacheable PMFS representation

Before ROS integration, compare:

1. early source injection used for the clean transfer test;
2. cached environment encoder + source intervention before final global
   Physics-Attention blocks.

The final PMFS implementation must compute the source-independent
geometry/wind representation once per source update and batch candidate-source
queries.

A method that requires a complete 8-layer backbone pass for every candidate is
not accepted as the final onboard implementation unless target-hardware timing
proves it fits the real source-update budget.

## G2 — independent multi-source simulation

Only after D0/D1 survive.

- unseen source positions;
- unseen plume realization;
- more than two source candidates;
- identical inference contract for Native PMFS and M6;
- no truth-conditioned model selection.

## G3 — online-wind shadow gate

This is mandatory before a real-flight claim.

Two evaluations must be separated:

### G3-A oracle-wind diagnosis
May use simulator ground-truth wind only to measure an upper bound.

### G3-B deployable-wind test
M6 receives only the wind representation that would actually be available on
the robot:
- onboard/local anemometer observations;
- the same online wind-map estimator available to PMFS;
- optionally an explicitly modeled wind uncertainty channel if preregistered.

No GADEN ground-truth wind field may enter the deployable arm.

M6 does not advance to flight if its source-rank advantage disappears when
ground-truth wind is replaced by the online estimated wind map.

## G4 — target-hardware timing

Measure on the actual onboard compute target.

For every source update report:
- environment-encoding time;
- candidate-count;
- candidate sweep time;
- memory peak;
- total added source-update latency.

Hard timing rule:
the complete M6 candidate-forward update must finish before the next
source-update opportunity in the frozen flight/PMFS cadence. Timing is measured
from the reference flight configuration; no arbitrary offline threshold is
substituted.

The model must run without cloud/network inference.

## G5 — real UAV test

Minimum scientific comparison:
- Native PMFS;
- M6 forward engine with otherwise unchanged PMFS inference/planner first;
- repeated known source placements;
- more than one wind regime / day when practical;
- randomized or counterbalanced method order;
- same gas sensor, wind sensor, map and stopping rule.

Primary outcomes:
- localization error / truth-containing candidate rank when available;
- time to localization;
- success/failure under the same flight budget;
- compute latency and dropped-control/update events.

Simulation-trained normalization may not use real-flight source truth.

## Safety / fallback

The learned forward model must not be a flight-critical controller.

If M6 inference is unavailable or exceeds its update deadline:
- preserve the flight controller;
- fall back to Native PMFS forward/inference;
- log the event.

## Main-claim boundary

A positive GADEN result supports:
`cross-physics foundation transfer for simulated candidate-forward modeling`.

Only after G3-B + G4 + G5 may the method be described as a deployable
real-world UAV-GSL contribution.

This gate is frozen before reading the current G1-D0 result.
