# TAORL H03 seed11 result

## Frozen result

- Formal contract verdict: `TAORL_H03_NO_GO`
- Endpoint-improvement component: `TAORL_H03_ENDPOINT_IMPROVEMENT_SIGNAL`
- Time-arrow attribution component: `TAORL_FORWARD_BEATS_REVERSE`
- Main-innovation decision: do not tune or promote TAORL as a cross-dataset
  causal estimator from this trace.

The formal script, literature trace and gate were committed and pushed as
`b73888a1112f9c415f68e49a57b54b8f1291cfc7` before the result existed.

## What improved

| Arm | True-source rank | Normalized rank | MAP error |
|---|---:|---:|---:|
| Raw profiled value | 4,705 / 7,258 | 64.82% | 9.39 m |
| ICRA 2026 global EDF | 7,060 / 7,258 | 97.27% | 6.75 m |
| TAORL forward windowed | **3,089 / 7,258** | **42.55%** | **4.99 m** |
| TAORL reverse-time control | 6,133 / 7,258 | 84.50% | 8.74 m |
| Historical native PMFS endpoint | n/a | n/a | 8.584 m |

TAORL reduced endpoint error by 41.9% relative to the historical PMFS result
and moved the solution 4.41 m closer than the raw-value candidate scorer.  The
forward filter also beat the reverse-time control by 3,044 rank positions.
These are meaningful development signals.

## Why the registered gate still failed

Four of five checks passed.  The failed check was the precommitted requirement
that the true source enter the top decile.  Its actual normalized rank was
42.55%.  A closer MAP point alone does not show that the likelihood identifies
the source: 3,088 other cells still received lower loss than the true cell.

The result therefore supports a narrow statement: hardware-bounded sensor time
and local ordinal comparison improve the previously failing H03 endpoint and
carry a correct-time-arrow signal.  They do not yet provide globally specific
source evidence.

## Post-result diagnosis

The diagnosis did not select or test a new parameter.  The analytic provider at
the true source was nonzero for every measured hit, so this failure differs from
the earlier native-PMFS zero-support failure.  Its within-window Spearman
agreement was inconsistent (median 0.377, including two negative windows),
whereas the TAORL MAP candidate had median agreement 0.676.  The remaining
missing property is **transport-regime-specific response shape**, not sensor
calibration, sensor memory or source support.

No threshold, window, tau value or candidate score was changed after observing
the result.  `H03_SEED11_TAORL_DIAGNOSIS.json` is explicitly post hoc and has no
gate authority.

## Claim boundary

This H03 trace may be reported as a development ablation showing endpoint and
time-arrow improvements.  It cannot establish cross-House effectiveness,
causal source identification, real-flight readiness or a main contribution.
