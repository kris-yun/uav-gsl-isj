# Realization-Invariant Source Signature — D0 Data-Only Probe

Date: 2026-09-24

Branch: `research/realization-invariant-source-signature-v0`

Status: **D0_HOLD_MECHANISM_SIGNAL — NOT A MAIN INNOVATION YET**

## Frozen input

Reuses the independently audited Gate-1A House02/W2 package:

- 630 arbitrary source hypotheses;
- targets S2_W2_A / S2_W2_B;
- prediction seeds 2026092401 / 2026092402;
- 10 frozen times x 30 frozen probes;
- same W2, occupancy, GADEN binary and source bank.

No new simulation and no learned model were used in this probe.

## Baseline

Frozen exact-forward mean(C,D) truth ranks:

- A: 1
- B: 7

This is the realization-sensitivity failure that motivated the probe.

## Predefined nuisance-removal controls

Truth rank A / B:

| Representation | A | B |
|---|---:|---:|
| raw 300-D exact-forward | 1 | 7 |
| temporal mean over 10 snapshots | 1 | 5 |
| global L1 normalization | 1 | 8–9 |
| global L2 normalization | 1 | 10 |
| total-mass time series only | 1 | 20–22 |
| spatiotemporal binary support only | 5 | 8 |
| first arrival time per probe only | 5 | 5 |
| per-time L1 mass fraction -> time average | 2 | 3 |

For the last row, each independent prediction realization is first mapped to its feature and then the two feature vectors are averaged. No learned weights or post-result tuning are used.

## Cross-realization invariance

For targets A and B from the same source:

- raw 300-D cosine: ~0.9774;
- raw relative L2 difference: ~0.2118;
- per-time-L1/time-average signature cosine: ~0.9952;
- signature relative L2 difference: ~0.1013.

Thus this representation approximately halves the A/B relative discrepancy while preserving/improving source rank.

## Stability / mechanism check

Leave-one-time-slice-out for the per-time-L1/time-average signature:

- omitting iterations 150..550: B remains rank 3;
- omitting the earliest iteration 100: B degrades from rank 3 to rank 22.

The improvement is therefore not a uniformly distributed generic normalization effect.

At iteration 100:

- target A has a small nonzero probe mass;
- target B has zero probe mass;
- truth prediction C has a small nonzero probe mass;
- truth prediction D has zero probe mass.

This means the signature is exploiting a combination of:

1. early causal arrival / non-arrival structure;
2. later spatial mass-fraction morphology.

Neither component alone reproduces the full 2/3 ranking result.

## Current scientific interpretation

The useful signal is more specific than “normalize concentration”:

> Source identity appears to be encoded in a realization-robust combination of causal plume-arrival support and the time-aggregated spatial distribution of plume mass, while absolute realization-dependent concentration amplitude acts largely as a nuisance.

This is a **mechanism signal only**.

Do not yet:

- train a neural model;
- tune weights between arrival and shape;
- change probes or times;
- claim a main innovation;
- run closed loop.

## Next gate

Before any model construction, search for one far-domain mother theory that explicitly separates fast stochastic realization fluctuations from slow / invariant mechanistic identity, and whose mathematical object can naturally combine arrival/reachability with normalized morphology.

Candidate theory must then be tested on this same 630-source bank without result-driven tuning.
