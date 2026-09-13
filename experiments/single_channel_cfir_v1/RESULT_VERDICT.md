# CFIR H03 seed11 result

## Frozen verdict

`CFIR_H03_ORACLE_PREMISE_NO_GO`

The formal one-shot run reproduced both frozen LMBT comparators exactly, so the
failure is attributable to the registered CFIR subtraction rather than input or
runtime drift.

At the registered default `kappa=0.03`:

| Evidence field | True-source rank | Normalized rank | MAP error |
|---|---:|---:|---:|
| LMBT chronological | 790 / 7,258 | 0.1087 | 1.6004 m |
| LMBT reversed wind | 630 / 7,258 | 0.0867 | 1.5479 m |
| CFIR chronological over reversed | 1,075 / 7,258 | 0.1480 | 1.9810 m |
| CFIR sign-reversed control | 6,184 / 7,258 | 0.8520 | 13.9574 m |

CFIR fails the MAP, true-source rank, top-decile, and frozen-grid median gates.
The result is stable across the fixed diffusion sensitivity grid: CFIR ranks
the truth 1,026, 1,075 and 1,117, and its MAP errors are 1.760, 1.981 and
1.920 m for `kappa=0.01, 0.03, 0.1`.

## Scientific meaning

The correct CFIR sign strongly beats its sign-reversed control.  The trace and
wind therefore contain a detectable global time arrow.  That time arrow is not
source-specific: subtracting reversed support removes more evidence from the
true source than from a false near-trajectory mode.  This is why causal
direction can be detected while localization becomes worse.

This result closes a tempting but invalid inference: observing
irreversibility is not sufficient to identify the intervention target or gas
source.  The remaining blocker is the source-conditioned observation operator,
not the lack of another posterior weight, temporal window, or causal penalty.

## Stop decision

Per preregistration, do not tune CFIR weights, temperatures, event thresholds,
sensor parameters, diffusion values, or windows on H03.  Retire the passive
time-arrow/footprint-contrast line as the main innovation route.

Any next mechanism must create source-discriminating information that the
current passive trace does not contain.  It must be tested upstream of Bayesian
accumulation and must not be another reweighting of the same response field.

## Reproducibility

- Raw result: `results/H03_SEED11_CFIR_ONE_SHOT.json`
- Raw result SHA-256:
  `30ae0b47ff2607e58eb233f6c3df025e595bb5b9c9b95620b4c34e68d3c8ccd2`
- Pre-experiment GitHub commit:
  `3fa23f88231d5b0823b4a7b1b3319689abc7079f`
- All model inputs, dependencies, wind fields, executable and preregistration
  are hashed inside the raw result.

