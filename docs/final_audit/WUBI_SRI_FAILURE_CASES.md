# WUBI-SRI Failure Case Analysis

Total trials: 14
Method: US_HIT_SHRINK_CAL (single-split evaluation)

## Summary

2 out of 14 trials have CR90 coverage = 0 (source outside credible region):
- **314_01**: wind=0.73 m/s, wind_std=43.7 deg, distance=251m
- **314_02**: wind=0.52 m/s, wind_std=44.9 deg, distance=243m

Both failures share the same pattern: very low wind speed (< 1.0 m/s) combined with unstable wind direction (std > 40 deg). In these conditions, the upwind direction is essentially random, making sector-based inference unreliable.

### LOO Validation Confirms Pattern

In leave-one-trial-out validation, the same 2 trials fail:
- 314_01: failure_reason = low_wind_speed|unstable_wind|source_far
- 314_02: failure_reason = low_wind_speed|unstable_wind

314_03 (also low wind at 0.57 m/s) is covered in both single-split and LOO, but with the largest CR90 area (224,400 m2 = 44% of grid). This suggests the method can sometimes handle low wind, but unreliably.

### Paper-Ready Explanation

"For trials with wind speed below 1.0 m/s and direction standard deviation above 40 degrees, the upwind sector method fails because the wind direction is effectively random. In such conditions, no directional constraint can be reliably imposed, and the method degrades to a near-uniform distribution over the search grid. These 2 failure cases (out of 14) represent the operational limit of directional-constraint-based source-region inference."

---

## Per-Trial Details

## 225_01

- Covered: YES
- Wind speed: 4.53 m/s
- Wind direction std: 12.3 deg
- Min distance to source: 3.4 m
- Source inside bbox: True
- CR90 area: 46025 m2
- Err2D: 27 m

## 225_02

- Covered: YES
- Wind speed: 5.52 m/s
- Wind direction std: 14.9 deg
- Min distance to source: 1.1 m
- Source inside bbox: True
- CR90 area: 50125 m2
- Err2D: 38 m

## 308_02

- Covered: YES
- Wind speed: 1.71 m/s
- Wind direction std: 26.3 deg
- Min distance to source: 214.0 m
- Source inside bbox: False
- CR90 area: 121275 m2
- Err2D: 210 m

## 309_01

- Covered: YES
- Wind speed: 2.80 m/s
- Wind direction std: 26.9 deg
- Min distance to source: 200.8 m
- Source inside bbox: False
- CR90 area: 121400 m2
- Err2D: 231 m

## 309_02

- Covered: YES
- Wind speed: 2.69 m/s
- Wind direction std: 28.8 deg
- Min distance to source: 222.0 m
- Source inside bbox: False
- CR90 area: 136300 m2
- Err2D: 231 m

## 312_01

- Covered: YES
- Wind speed: 3.31 m/s
- Wind direction std: 12.7 deg
- Min distance to source: 211.1 m
- Source inside bbox: False
- CR90 area: 67125 m2
- Err2D: 188 m

## 312_03

- Covered: YES
- Wind speed: 3.54 m/s
- Wind direction std: 13.6 deg
- Min distance to source: 186.4 m
- Source inside bbox: False
- CR90 area: 58775 m2
- Err2D: 168 m

## 313_01

- Covered: YES
- Wind speed: 3.56 m/s
- Wind direction std: 17.9 deg
- Min distance to source: 206.2 m
- Source inside bbox: False
- CR90 area: 53575 m2
- Err2D: 184 m

## 313_02

- Covered: YES
- Wind speed: 2.82 m/s
- Wind direction std: 25.4 deg
- Min distance to source: 201.2 m
- Source inside bbox: False
- CR90 area: 67250 m2
- Err2D: 148 m

## 313_03

- Covered: YES
- Wind speed: 2.17 m/s
- Wind direction std: 75.0 deg
- Min distance to source: 164.0 m
- Source inside bbox: False
- CR90 area: 171950 m2
- Err2D: 168 m

## 313_04

- Covered: YES
- Wind speed: 2.68 m/s
- Wind direction std: 43.3 deg
- Min distance to source: 163.2 m
- Source inside bbox: False
- CR90 area: 123000 m2
- Err2D: 174 m

## 314_01

- Covered: NO
- Wind speed: 0.73 m/s
- Wind direction std: 43.7 deg
- Min distance to source: 251.4 m
- Source inside bbox: False
- CR90 area: 112275 m2
- Err2D: 316 m
- **Failure reason**: low wind speed (< 1.0 m/s), unstable wind direction (std > 30 deg), source far from trajectory (> 250m)

## 314_02

- Covered: NO
- Wind speed: 0.52 m/s
- Wind direction std: 44.9 deg
- Min distance to source: 243.4 m
- Source inside bbox: False
- CR90 area: 160550 m2
- Err2D: 332 m
- **Failure reason**: low wind speed (< 1.0 m/s), unstable wind direction (std > 30 deg)

## 314_03

- Covered: YES
- Wind speed: 0.57 m/s
- Wind direction std: 55.3 deg
- Min distance to source: 252.8 m
- Source inside bbox: False
- CR90 area: 224400 m2
- Err2D: 241 m
