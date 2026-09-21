# Horizon-Calibrated Transport Uncertainty V1 — offline screen

Date: 2026-09-22
Status: **POSITIVE AUXILIARY SIGNAL / NO-GO AS MAIN INNOVATION**

## Remote idea

ICLR 2026: *Learning to Be Uncertain: Pre-training World Models with Horizon-Calibrated Uncertainty*.

Transfer hypothesis:
candidate-source transport predictions should not be treated as equally trustworthy across transport horizons. Long / poorly aligned transport paths should contribute less evidence because model error can grow with horizon.

## Frozen controlled VGR screen

Asset:
H01/H02/H03 × SA/SB × fast/slow, 240 s, identical within-House trajectories.

Candidate-specific advective burden:

`tau = d / (0.02 + |u| * max(0.1, cos_alignment))`

No parameter was fitted to source truth.

### Tercile result

Using centered-cosine source identity within candidate-specific burden terciles:

- full field: 12/12, mean margin 0.77598
- near burden: 12/12, mean margin 0.790998
- middle burden: 12/12, mean margin 0.67049
- far burden: 10/12, mean margin 0.62255
- far failures: H02_SA_fast and H02_SA_slow

This supports the narrow premise that high-burden evidence is more fragile.

### Rank-reliability result

With burden percentile r:

- near reliability: `w = 1-r`
- destructive far control: `w = r`

At 240 s:

- uniform: 12/12; mean margin 0.775976; min margin 0.009192
- near-weighted: 12/12; mean margin 0.776312; min margin 0.016532
- far-weighted: 12/12; mean margin 0.750476; min margin 0.001075

500 source-blind random rank-weight controls:

- random global-min-margin median: 0.008439
- 95th percentile: 0.016463
- only 4.6% of random controls meet/exceed near-weighted min margin

Thus the near-burden rule improves the worst-case margin beyond most random weightings, although it does not materially improve the average margin.

### Cross-time result

At 176 s and 200 s near weighting slightly improves the worst-case margin while far weighting is clearly worse.
At 220 s near weighting is slightly worse than uniform but still better than far.
At 240 s the hard-case improvement reappears.

The effect is therefore real but modest rather than uniformly dominant.

## Critical disentangling control

At 240 s compare the same fixed rank weighting using:

1. advective burden;
2. pure Euclidean candidate distance;
3. wind-speed-only reliability.

Results:

- advective burden: 12/12; mean 0.776312; min 0.016532
- Euclidean distance: 12/12; mean 0.755032; **min 0.019338**
- wind-speed-only: 11/12; min -0.009216; fails H02_SA_slow

Pure Euclidean distance gives a better worst-case margin than the proposed wind-aware transport-horizon measure.

## Internal novelty boundary

The repository already contains physical distance attenuation in OPGSLScientificV31's observation model. That is not mathematically identical to epistemic horizon calibration, but this screen does not demonstrate a benefit specific to horizon-calibrated uncertainty beyond ordinary near-source reliability.

## Decision

**NO-GO as the paper-level mother idea.**

Keep as an auxiliary reliability mechanism / ablation:
high-burden evidence is demonstrably fragile and downweighting it can protect the weakest source ordering.

Do not claim that world-model horizon calibration is the load-bearing new mechanism unless a future independent dataset shows a benefit beyond simple distance reliability.
