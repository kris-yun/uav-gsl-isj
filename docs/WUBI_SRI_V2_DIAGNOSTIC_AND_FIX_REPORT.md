# WUBI-SRI V2 Diagnostic and Fix Report

## 1. Executive Summary

### V1 Failure Root Causes

1. **Wind convention error (CRITICAL)**: The wind vector in MATRIX data points in the "blowing to" direction, but v1 assumed "coming from" direction. This caused 57% of trials to have LIKELIHOOD_DIRECTION_FAILURE (source rank percentile = 1.0).

2. **Gaussian plume amplitude likelihood mismatch**: The v1 WUL/WUL_MML methods used Gaussian plume amplitude models that are inappropriate for far-field UAV data. Even with corrected wind, these methods achieve CR90 coverage = 0.00.

3. **Grid domain was NOT the issue**: Source is inside the grid for 100% of trials with both local_200m and expanded_600m policies.

### V2 Fixes Applied

1. Wind convention audit identified **B_reversed (-u, -v)** as correct, achieving 73% upwind hit ratio.
2. New **upwind_sector_hit_only** baseline achieves CR90 coverage = 0.79 with reversed wind.
3. New **upwind_sector_hit_nonhit** achieves CR90 coverage = 0.71.
4. New **WUS_HN** method achieves CR90 coverage = 0.21, source rank percentile = 0.30.

### Current Verdict: **FAIL**

WUS_HN (the proposed new method) does not outperform the simpler upwind_sector_hit_only baseline. The best CR90 coverage (0.79) is close to but below the 0.80 threshold.

## 2. Dataset Audit Fix

- MATRIX: **USABLE** (14/15 trials, 225_03 blocked due to NaN wind)
- BTEX/PANGAEA: Directory not found
- FFT-07: Directory not found
- Original audit contradiction fixed: wubi_sri_dataset_audit.md now correctly shows MATRIX usable

## 3. Wind/Coordinate Convention Audit

| Convention | Mean Upwind Hit | Mean Angular Error |
|------------|----------------|-------------------|
| **B_reversed** | **0.728** | **34.2deg** |
| D_reversed_y_flipped | 0.447 | 58.0deg |
| A_as_given | 0.089 | 130.8deg |
| C_y_flipped | 0.084 | 119.3deg |

**Finding**: Wind vector needs to be negated (B_reversed). The data stores wind as "blowing to" direction.

Best convention per trial: B_reversed wins 11/14 trials.

## 4. Grid Domain Audit

| Policy | Source In Grid | Mean Oracle Error |
|--------|---------------|-------------------|
| local_200m | 100% | 2.1m |
| expanded_600m | 100% | 1.2m |
| wind_sector_adaptive | 93% | 0.0m |

**Finding**: Source is in grid for all policies. Grid domain is NOT the failure cause.

## 5. Posterior Failure Diagnosis

### V1 (as_given wind):
- LIKELIHOOD_DIRECTION_FAILURE: 16/28 (57%)
- Source rank percentile = 1.0 for most far-field trials
- Posterior concentrated in wrong direction

### V2 (reversed wind):
- WUL_MML: rank_pct = 0.041, CR90_cov = 0.00
- WUS_HN: rank_pct = 0.301, CR90_cov = 0.21
- upwind_sector_hit_only: rank_pct = 0.182, CR90_cov = 0.79

**Finding**: Wind reversal fixes direction failure. But Gaussian plume amplitude likelihood still fails.

## 6. New Baselines

| Method | Err2D | CR90 Cov | Rank Pct |
|--------|-------|----------|----------|
| max_enhancement | 215.3m | N/A | N/A |
| hit_centroid | 217.8m | N/A | N/A |
| point_wind_gaussian | 218.0m | N/A | N/A |
| **upwind_sector_hit_only** | **186.1m** | **0.79** | **0.182** |
| upwind_sector_hit_nonhit | 220.6m | 0.71 | 0.219 |

upwind_sector_hit_only is the strongest baseline: 186.1m Err2D (vs 215.3m max_enhancement), CR90 coverage 0.79.

## 7. WUS_HN Method

WUS_HN combines direction + rank + distance + non-hit likelihoods.

| Method | Err2D | CR90 Cov | Rank Pct |
|--------|-------|----------|----------|
| WUS_HN | 226.6m | 0.21 | 0.301 |
| WUS_only | 318.6m | 0.21 | 0.151 |

WUS_HN achieves CR90 coverage 0.21, much worse than upwind_sector_hit_only (0.79).

**Issue**: The combined likelihood dilutes the directional signal. The rank and distance components may be pulling the posterior away from the correct region.

## 8. Main Results

### With Reversed Wind Convention (expanded_600m grid)

| Method | Err2D | CR90 Cov | CR90 Area | Rank Pct | Runtime |
|--------|-------|----------|-----------|----------|---------|
| WUL_MML | 132.3m | 0.00 | 412 | 0.041 | 891ms |
| WUL_only | 133.4m | 0.00 | 438 | 0.041 | 246ms |
| upwind_sector_hit_only | 186.1m | 0.79 | 294825 | 0.182 | 44ms |
| max_enhancement | 215.3m | N/A | N/A | N/A | 0ms |
| hit_centroid | 217.8m | N/A | N/A | N/A | 0ms |
| point_wind_gaussian | 218.0m | N/A | N/A | N/A | 0ms |
| upwind_sector_hit_nonhit | 220.6m | 0.71 | 289925 | 0.219 | 152ms |
| WUS_HN | 226.6m | 0.21 | 58750 | 0.301 | 765ms |
| WUS_only | 318.6m | 0.21 | 38225 | 0.151 | 702ms |

### WUL_MML Anomaly

WUL_MML achieves Err2D = 132.3m (best point accuracy) but CR90 coverage = 0.00. This means:
- MAP estimate is close to source
- But posterior is so concentrated that CR90 region doesn't cover source
- Source rank percentile = 0.041 (source is in top 4% of posterior)

This suggests the posterior has the right peak but wrong uncertainty quantification.

## 9. Decision Gate V2

**Verdict: FAIL** (4/7 criteria passed)

| Criterion | Pass | Details |
|-----------|------|---------|
| no_leakage | PASS | PASS |
| dataset_audit | PASS | MATRIX usable |
| cr90_coverage | FAIL | WUS_HN = 0.21 (need >= 0.80) |
| cr90_area_ratio | PASS | 0.092 (need <= 0.25) |
| source_rank | PASS | 0.301 (need < 0.5) |
| vs_upwind_sector | FAIL | WUS_HN 0.21 < US 0.79 |
| runtime | FAIL | p95 = 765ms |

## 10. Remaining Risks and Recommendations

### Why WUS_HN Fails

The combined likelihood approach dilutes the directional signal. The rank and distance components may be counterproductive for far-field data where:
- Enhancement amplitude is unreliable for distance estimation
- Rank correlation with source distance is weak at 200m+ range

### Possible Improvements

1. **Increase direction weight** in WUS_HN (currently 0.4, try 0.8+)
2. **Remove distance component** for far-field data
3. **Use upwind_sector_hit_only as primary method** and calibrate its credible region
4. **Posterior temperature calibration**: The WUL_MML posterior is too concentrated (CR90 = 412m² but misses source). Temperature scaling could spread it.

### Paper Strategy

If v2 still FAILS after optimization:
- Write as "Far-field UAV gas source region inference: failure modes, evaluation protocols, and identifiability analysis"
- Key contributions:
  1. Wind convention audit protocol
  2. Source region evaluation metrics (CR90 coverage, area, rank)
  3. Upwind sector baseline as strong reference
  4. Analysis of why Gaussian plume models fail at far-field
  5. Calibration/test split methodology

### External Data

BTEX/PANGAEA and FFT-07 are not available. MATRIX (15 trials) is the only dataset. This limits generalizability.
