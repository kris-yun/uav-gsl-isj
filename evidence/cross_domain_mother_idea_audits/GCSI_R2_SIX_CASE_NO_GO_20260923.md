# GCSI V1 — authoritative-R2 six-case falsification

Date: 2026-09-23  
Status: **NECESSARY PATHOLOGY CONFIRMED / 300-S LOCALIZATION GATE NO-GO**

## Why this run exists

The branch `research/godambe-composite-source-inference-v1` had previously frozen GCSI V1 as the current #1 main-innovation candidate, but its required House01/02/03 × seed0/1 300-s R2 replay had not been completed because the authoritative archive was not available to that analysis.

The exact archive is now available:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

No GCSI equation, block size, gate threshold, or House truth was changed.

## Frozen GCSI contract

- physical block size: 0.9 m;
- source-discrimination power: 1.0;
- native-best candidate selected source-blind;
- paired physical-block mean score differences;
- robust score `z = mean(block difference) / SE(block difference)`;
- candidate relative log weight `-0.5 z^2`;
- simple global block-count/cell-count temperature is mandatory control;
- endpoint: PMFS `ExpectedValue(sourceProbability,0.05)` at the final source update <=300 s.

Cheap Stage-2 GO required:
- pooled endpoint gain >=2%;
- >=4/6 non-worse;
- worst degradation <=25%;
- zero false-confident-collapse;
- GCSI must beat simple scalar temperature.

## Integrity

Native posterior reconstruction from the frozen candidate-support alignment was exact to floating-point precision:

| Case | reconstruction L1 | max abs |
|---|---:|---:|
| H01 s0 | 1.81e-15 | 3.89e-16 |
| H01 s1 | 2.31e-15 | 7.77e-16 |
| H02 s0 | 5.13e-15 | 1.30e-15 |
| H02 s1 | 8.77e-16 | 4.30e-16 |
| H03 s0 | 7.46e-14 | 1.19e-14 |
| H03 s1 | 2.04e-15 | 2.91e-16 |

The repository's previously audited standalone C++ std::sort endpoint clone was compiled and checked against the actual PMFS `RESULT IS` endpoint before counterfactual evaluation. Absolute endpoint differences were 0.00074–0.00298 m, all below the frozen 0.011 m native-parity tolerance.

This is an independent standalone-clone falsification rather than a new linked-native binary build; because native parity passes tightly in all six cases, it is sufficient to reject promotion. A future linked-native rerun could be retained only as archival certification, not as a reason to tune GCSI.

## 300-s results

| Case | Native m | scalar-temperature m | GCSI m | GCSI vs Native |
|---|---:|---:|---:|---:|
| House01 seed0 | 5.52735 | 5.47770 | 5.52593 | +0.00142 m |
| House01 seed1 | 4.00164 | 3.65527 | 3.77122 | -0.23042 m |
| House02 seed0 | 4.10702 | 4.10435 | 4.68178 | **+0.57476 m** |
| House02 seed1 | 3.70074 | 3.47739 | 3.66769 | -0.03305 m |
| House03 seed0 | 7.78206 | 8.03339 | 7.86896 | +0.08691 m |
| House03 seed1 | 8.21155 | 8.08912 | 7.91940 | -0.29216 m |

Pooled:
- Native: **5.55506025 m**
- scalar temperature: **5.47287150 m**
- GCSI: **5.57249763 m**
- GCSI improvement vs Native: **-0.3139%**
- GCSI vs scalar-temperature: **-1.8204%**
- improved/non-worse: 4/6
- worst pair degradation: 13.99%
- false-confident-collapse cases under GCSI audit: 0

## Interpretation

The previously observed dependence pathology is real: PMFS map cells are not independent evidence units, and raw evidence magnitude is grid-resolution dependent.

However, correcting that dependence geometry does **not** repair source localization. The frozen Godambe/sandwich calibration is worse than Native in pooled endpoint error and worse than the simple global temperature control.

Therefore the core project failure is not primarily posterior over-concentration caused by spatial pseudo-replication. It is upstream: the candidate evidence ordering / forward source compatibility itself is frequently wrong.

## Decision

**GCSI V1 = NO-GO AS MAIN INNOVATION.**

Keep only as:
- a posterior-calibration / reliability ablation;
- a false-confidence diagnostic;
- a possible auxiliary module after a genuinely source-identifying evidence mechanism is found.

Do not tune block size, z mapping, clipping, or House-specific temperature on these six cases.
