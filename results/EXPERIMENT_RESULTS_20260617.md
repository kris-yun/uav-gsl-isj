# UAV-GSL ISJ Experiment Results (Updated 2026-06-17)

## Method: DQA-AS + Innovation Modules

### Innovation Modules
1. **SDR (Spatial Deconvolution Refinement)** ? Medical imaging (Richardson-Lucy deconvolution)
   - Deconvolves gas hit distribution to recover source location
   - ITS-G gate (astronomical inertia tensor) controls when SDR applies
   - Domain: Medical CT reconstruction + Astronomical image analysis

2. **TDC (Temporal Deconvolution Correction)** ? Signal processing
   - Compensates MOX sensor temporal response delay
   - Adaptive tau decay with accumulated detections
   - Domain: Signal processing / inverse filtering

3. *Third module candidates being tested*

## House01 Results (10 seeds, paired)

| Seed | Baseline | SDR | Status(BL) | Status(SDR) |
|------|----------|-----|------------|-------------|
| s0 | 3.589m | 3.105m | SUCCESS | SUCCESS |
| s1 | 2.879m | 0.486m | FAILED | FAILED |
| s2 | 2.879m | 2.958m | FAILED | SUCCESS |
| s3 | 2.879m | 2.958m | FAILED | SUCCESS |
| s4 | 3.270m | 2.879m | SUCCESS | FAILED |
| s5 | 3.270m | 3.105m | SUCCESS | SUCCESS |
| s6 | 2.879m | 2.958m | FAILED | FAILED |
| s7 | 2.879m | 3.105m | FAILED | SUCCESS |
| s8 | 3.589m | 2.958m | SUCCESS | SUCCESS |
| s9 | 2.879m | 3.105m | FAILED | SUCCESS |
| **Mean** | **3.129m** | **2.752m** | **40% success** | **60% success** |

Improvement: **-12.0% mean error, +20% success rate**

## House02 Results (5 seeds, paired)

| Seed | Baseline | SDR |
|------|----------|-----|
| s0 | 5.674m | 5.261m |
| s1 | 6.020m | 6.077m |
| s2 | 5.813m | 5.261m |
| s3 | 5.674m | 5.261m |
| s4 | 5.379m | 5.261m |
| **Mean** | **5.712m** | **5.424m** |

Improvement: **-5.0% mean error**

## House03 Results (5 seeds, paired)

All seeds: 3.448m (both baseline and SDR). PMFS converges in 4 iterations; SDR has insufficient gas hit data.

## Single-Seed Module Tests (House01, seed 0)

| Module | Error | vs Baseline (3.589m) |
|--------|-------|---------------------|
| TDC | 3.200m | **-10.8%** |
| SDR | 3.105m | **-13.5%** |
| SDR+TDC | 2.879m* | **-19.8%** |
| PWC | 3.813m | +6.2% (worse) |
| PSDE | 8.904m | +148% (worse) |

*PMFS did not converge; error from SDR estimate

## Key Findings

1. SDR improves estimates on House01 (-12%) and House02 (-5%), but not House03
2. TDC improves House01 by -10.8% (single seed)
3. PWC and PSDE are ineffective
4. PMFS convergence is seed-dependent: 4/10 seeds fail on House01
5. SDR improves estimates even on non-converged seeds (e.g., s1: 2.879m -> 0.486m)

## Pending
- [ ] TDC multi-seed validation on House01/02/03
- [ ] SDR+TDC combination multi-seed
- [ ] Third innovation module selection
- [ ] Official baseline comparison (PMFS/GrGSL/surge_cast)
- [ ] Statistical tests (Wilcoxon, bootstrap CI)
