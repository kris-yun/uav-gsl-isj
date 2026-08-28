# PF-DEI exact sensor deconvolution results

Date: 2026-08-28  
Source branch HEAD: `e7d05ce9c3b43124d03914c24cbfead1cb427043`  
Preserved forward closure: `a504e0e`  
Preserved sensor-memory audit: `6fbf08c`

## Contract result

`PF_DEI_INVERSE_SENSOR_REFERENCE_SELFTEST PASS`  
`PF_DEI_EXACT_SENSOR_DECONVOLUTION_COUNTERFACTUAL PASS`

All 30 OFF runs passed the frozen inverse preconditions: regular approximately 0.2 s cadence, 0.4 s integer delay, symmetric `tau=1.2 s`, gain 1, zero baseline/noise/drift, and no active upper saturation. Round-trip measured-trace residuals were at floating-point scale (maximum reported below `3e-16 ppm`); the fixed six-decimal serialization bound is `6.0138824631e-6 ppm`.

## Overall block counterfactual

| classification | count | fraction |
|---|---:|---:|
| SAME_HIT | 2177 | 53.77% |
| SAME_NOTHING | 1713 | 42.31% |
| NATIVE_HIT_IDEAL_NOTHING | 88 | 2.17% |
| NATIVE_NOTHING_IDEAL_HIT | 71 | 1.75% |
| Total | 4049 | 100% |

Thus 159/4049 blocks (3.93%) change decision under the ideal-sensor counterfactual. The net change is +17 HIT blocks for native relative to ideal, not a one-direction “memory creates all hits” effect.

## By House

| House | blocks | native HIT→ideal NOTHING | native NOTHING→ideal HIT | total flips |
|---|---:|---:|---:|---:|
| H01 | 1357 | 29 | 29 | 58 |
| H02 | 1346 | 18 | 11 | 29 |
| H03 | 1346 | 41 | 31 | 72 |

## First block after inter-stop transition

Across 484 first blocks after a transition:

- 18 `NATIVE_HIT_IDEAL_NOTHING`;
- 14 `NATIVE_NOTHING_IDEAL_HIT`;
- 255 `SAME_HIT`;
- 197 `SAME_NOTHING`.

The transition-only flip rate is 32/484 = 6.61%. House-specific transition counts are H01 4/6, H02 6/6, H03 8/2 for the two flip directions (H01/H02/H03 respectively).

## Scientific interpretation

The exact inverse proves that, under the frozen deterministic sensor, historical measured data retain an almost lossless delayed representation of the physical input. Sensor memory relocates and mixes information across time; it does not intrinsically destroy it. A context-local or block-independent source likelihood can therefore misattribute previous exposure to the current stop.

The result does **not** prove that all 102 lower-bound qualifying transitions are false physical hits, nor that sensor memory alone explains the prior 50/50 source-localization generalization. The lower-bound audit and this stricter counterfactual answer different questions: 102 transitions had enough inherited state to force a zero-input block above threshold, while 159 blocks in the full archive actually flip against the ideal counterfactual. Source-truth and localization error were not read.

The scientifically required next test is matched source inference on the same reconstructed physical traces: A1 ideal observation versus A2 native persistent sensor, with identical candidates, transport draws, trajectory, and run-level state handling. Only if A1 becomes adequate while correctly modelled A2/old local representations do not should sensor-state misattribution be called dominant.

## Artifacts

- `artifacts/pf_dei_deconvolution/block_counterfactual.csv`
- `artifacts/pf_dei_deconvolution/block_counterfactual_summary.json`
- `artifacts/pf_dei_deconvolution/seed_counterfactual_summary.csv`
- `artifacts/pf_dei_deconvolution/recovered_physical_trace_House*_seed*.csv`

All artifacts are truth-blind and explicitly preserve the correlated time-series nature of the samples.
