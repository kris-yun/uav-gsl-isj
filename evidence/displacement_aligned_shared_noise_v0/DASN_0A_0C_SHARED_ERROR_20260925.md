# DASN 0A-0C Independent Screen — 2026-09-25

Status: **SHARED_LOCALIZATION_ERROR_SIGNAL_REPRODUCED; DISPLACEMENT MECHANISM NOT YET ESTABLISHED**

Data: D1R 168 sources x16 realizations x10 times x30 probes.

Readout: ordinary ridge coordinate regression on log(1+ppm), with train-half-only alpha selection.

Probe split:
- view A: probes 0,2,...,28 (15 probes);
- view B: probes 1,3,...,29 (15 probes);
- all 10 frozen times retained.

## 0A — each disjoint view has localization sensitivity

Train reps 1-8, test reps 9-16:

- odd-view mean error = 0.52168 m;
- odd-view median error = 0.45420 m;
- odd-view q90 = 0.95031 m;
- even-view mean error = 0.68619 m;
- even-view median error = 0.63238 m;
- even-view q90 = 1.11598 m;
- center-only null mean error = 1.93811 m.

Both disjoint views contain meaningful 2D source-location information.

## 0B — same-realization shared localization error

For each source and fresh realization, let e_A,e_B be the two view localization errors.
Center each view's errors within source and compute the trace of the paired cross-view covariance.

Primary descriptive statistic:

T = mean_s tr(C_AB(s)).

Observed:
- T = 0.0267256 m^2;
- source-wise T median = 0.0083276 m^2;
- source-wise T q25/q75 = -0.006898 / 0.054408 m^2;
- centered x-error correlation = 0.16368;
- centered y-error correlation = 0.17279.

Within-source B-view realization pairing was destroyed 300 times.

Permutation null:
- mean = 0.0000791 m^2;
- q2.5 = -0.0085963 m^2;
- q97.5 = 0.0086634 m^2;
- exceedance count = 0/300.

Thus same plume realizations induce reproducible common localization shifts across disjoint probe views.

## 0C — reverse 8/8 robustness

Train reps 9-16, test reps 1-8:

- odd mean/median error = 0.51899 / 0.44341 m;
- even mean/median error = 0.68344 / 0.62275 m;
- T = 0.0214671 m^2;
- centered x-error correlation = 0.16448;
- centered y-error correlation = 0.07489.

300 within-source pairing-destruction permutations:
- null mean = -0.0000389 m^2;
- q2.5 = -0.0079046 m^2;
- q97.5 = 0.0071943 m^2;
- exceedance count = 0/300.

The shared-error signal persists under reversal of the realization halves.

## Current scientific boundary

Established so far:

> same-realization plume variability produces a reproducible shared localization-error component across two disjoint observation subsets.

Not established:
- common-gain rejection;
- generic low-rank factor rejection;
- decoder-family invariance;
- boundary independence;
- alignment with local source-displacement sensitivity J;
- an information-limiting correlation mechanism.

Next frozen mini-step: common-gain control only.