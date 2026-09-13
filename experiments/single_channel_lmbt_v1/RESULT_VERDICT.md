# H03 seed11 result and decision

## Frozen verdict

- Primary premise: `LMBT_ORACLE_WIND_PREMISE_NO_GO`
- Secondary attribution: `LMBT_SENSOR_MEMORY_ATTRIBUTION_PASS`
- Decision: stop LMBT as the main-innovation route. Do not tune diffusion, the event window, or the lag parameters to rescue this trace.

The formal run used one fixed H03 seed11 A0 history, 7,258 candidate source cells, the exact GADEN runtime wind-grid reader, and no true-gas field in any scoring arm. The source coordinate was opened only after every score had been computed.

## Decisive evidence

All ranks below are normalized true-source ranks; lower is better. The registered default is `kappa=0.03`.

| Arm | Median normalized true-source rank | True-source rank | MAP error |
|---|---:|---:|---:|
| LMBT, sensor memory off, chronological full wind | 0.1414 | 1,027 / 7,258 | 2.03 m |
| LMBT, sensor memory on, chronological full wind | 0.1087 | 790 / 7,258 | 1.60 m |
| LMBT, sensor memory on, reversed wind order | 0.0867 | 630 / 7,258 | 1.55 m |
| Local-wind straight ray, sensor memory on | 0.1780 | 1,293 / 7,258 | 2.38 m |

The chronological full-wind arm beats the local-wind straight-ray arm, so spatially varying transport contains useful information. It does not beat the reversed-wind control, and it misses the registered top-decile threshold. Therefore this run does not establish that chronological backward transport identifies the source.

Sensor-memory correction improves the true-source rank from 1,027 to 790 and the MAP error from 2.03 m to 1.60 m. This is a real component-level result. It cannot be promoted to the main innovation because exact first-order sensor deconvolution already existed in the earlier PF-DEI line, and prior audits found that it changed only a small fraction of block decisions.

For context, native PMFS ended 8.58 m from the source on this history. This is not a formal head-to-head result: LMBT used evaluator-only full spatial wind and reused a fixed trajectory, whereas deployable PMFS did not have that information.

## What failed

The failure is not primarily an attribution weight or posterior-combination problem. The source-response law is underidentified from this single passive trace:

1. PMFS assigns a delayed, hysteretic sensor value to the current UAV pose.
2. Correcting that time assignment helps, but the measured whiffs remain stochastic filament samples rather than deterministic source responses.
3. Full spatial wind improves the footprint over a local straight ray, but the temporal ordering is not source-specific: reversing the wind sequence performs slightly better.
4. Posterior repair, covariance projection, or another causal regularizer can only reorder evidence produced by that misspecified response family.

The surviving scientific claim is narrow: **sensor memory is a measurable secondary failure mechanism; passive one-channel trajectory data do not yet identify the chronological source-to-receptor mechanism.**

## Reproducibility boundary

- Formal output: `results/H03_SEED11_LMBT_ORACLE_WIND_GATE.json`
- Preregistration: `H03_SEED11_PREREG.json`
- Executable: `lmbt_oracle_wind_gate.py`
- Runtime corrections: `PREFLIGHT_CORRECTION.md`
- All input hashes, the executable hash, the preregistration hash, wind-binding errors, and arm scores are stored in the formal JSON.
