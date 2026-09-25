# WCIG R0 implementation freeze

Committed before reading any W0/W1/W2/W3 local wind samples for this audit.
The governing scientific thresholds remain those in
`WCIG_R0_ZERO_PLUME_CHARTER_20260925.md`.

- Decode each of the 11 canonical wind iterations with the repository's
  `export_gaden_wind_3d.export_one` reader, and sample the three points with
  `l1_filament_transition_audit.sample_wind`. That validated GADEN mapping
  uses the containing grid cell (truncate toward zero). No new interpolator
  is introduced. The reader's float32 exported values are retained.
- The edge vector is endpoint 2 minus endpoint 1 in map xy. Local wind at an
  iteration is `(endpoint1 + 2*midpoint + endpoint2)/4`; mean it over all
  11 iterations before computing `A_parallel`, `A_perp`, and `U`.
- For each of the 30 W0/W1/W2 edge-wind cells, the primary target is the
  arithmetic mean of the frozen A/B energy distances. Fit ordinary least
  squares with an intercept and the three chartered log features, with
  `eps=1e-6 m/s`. No ridge, tuning, or feature selection.
- Leave one entire wind out at a time. Calculate Spearman correlation of
  predicted and observed log energy for each held-out wind and pooled over
  all 30 out-of-wind predictions.
- The orientation check compares mean energy over x edges versus y edges
  separately for each held-out wind. Prediction must reproduce the observed
  W0/W1 `y>x` and W2 `x>y` pattern.
- Repeat the full leave-one-wind-out check separately using the frozen A
  energies and B energies. Both must meet the same pooled, per-wind sign, and
  orientation criteria for split consistency.
- The secondary rank-only model uses within-wind ranks of `A_parallel` and
  `A_perp` as its two predictors, with intercept, and within-wind energy
  rank as target. It is reported and cannot rescue the primary criterion.
- Fit the same primary OLS on all 30 discovery cells solely to produce the
  W3 wind-only prediction. The three lowest predicted energies are HARD;
  the three highest are EASY. Similarity to W2 versus W0/W1 is Spearman
  against their already observed split-mean edge energies. No W3 plume
  outcome is opened.

Secondary physical diagnostics are descriptive: population SD of
per-iteration absolute along projection, unweighted circular SD of active
local wind direction, norm of mean endpoint difference in horizontal wind,
and absolute mean vertical wind.
