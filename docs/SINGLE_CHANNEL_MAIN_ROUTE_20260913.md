# Single-channel main-innovation route after the H03 failures

## Decision

Do not continue tuning the historical M1R 2-of-3 route.  Preserve it as a
baseline and causal-identifiability audit.  The only next mechanism gate is
**Time-Arrow Ordinal Response Likelihood (TAORL)**.

TAORL remains inside the current single-VOC-channel hardware contract.  It does
not require stopping the leak, a source library, another chemical channel,
multiple UAVs, a pump/valve, vertical motion, or a new neural network.

## Evidence that forced the switch

| Route | Evidence | Decision |
|---|---|---|
| M1R causal ratio | seed-12 endpoint improved H01/H02 and degraded H03; AUC improved 3/3 | retain code and ablation; not a cross-dataset causal claim |
| Source-evidence audit | true-source native response was zero before clipping for 59/59 H01, 88/88 H02 and 66/70 H03 positive blocks | posterior reweighting cannot create missing source evidence |
| CCDE held-out | `CCDE_WIND_MOMENT_NOT_PHYSICALLY_SPECIFIC` | retire wind-moment deprojection |
| MC-SCSP H03 seed11 | mathematically correct subspace geometry, but localization worsened | retire covariance/subspace repair |
| LMBT H03 seed11 | sensor-memory attribution passed; chronological full wind lost to reversed-wind control | retain timing diagnosis; retire backward transport as main route |
| FKT-AQI-L contract | diffusion sampling, 1 Hz upload, VOC concentration output, no controllable intake | single passive VOC plus time-aligned UAV pose is the deployment boundary |

## Why TAORL is the smallest new test

The latest direct result, ICRA 2026 concentration ranking, removes dependence on
absolute calibration but assumes a steady-enough plume.  The H03 evidence says
timing and intermittency remain load-bearing.  TAORL composes three restricted
principles before Bayesian accumulation:

1. rank instead of magnitude, to remove positive monotone calibration changes;
2. 30 s local windows, fixed as twice the device's stated maximum T90;
3. a first-order sensor timescale profiled over a device-derived set, with the
   entire filter reversed as a time-arrow negative control.

This is not yet a main innovation claim.  It becomes a candidate only if the
one-shot H03 gate improves the true-source rank and error and the correct time
arrow strictly beats the reversed control.  Any failure stops this route.

## Cross-dataset logic

The proposed transferable property is explicit: the likelihood depends on
within-window order and a hardware-bounded dynamics set, not ppm scale, House
identity or a learned House embedding.  Cross-dataset evidence still requires a
later untouched House/seed test.  H03 is only the premise gate and cannot prove
that claim.
