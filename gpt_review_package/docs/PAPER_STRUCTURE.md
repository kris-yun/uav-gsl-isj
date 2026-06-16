# Paper Draft Structure for ISJ

## Title (Draft)
"Spatial Deconvolution Refinement for UAV Gas Source Localization in Low-Wind Indoor Environments"

## Abstract
- Problem: PMFS fails in low-wind sparse-gas scenarios
- Solution: SDR - medical imaging deconvolution applied to GSL probability maps
- Results: 11.7% improvement on House01, 2.2% on House02
- Contribution: cross-domain innovation + comprehensive validation

## 1. Introduction
- UAV GSL importance (hazardous gas detection, environmental monitoring)
- PMFS algorithm and its limitations in low-wind scenarios
- Research gap: no robust post-processing for probability map refinement
- Our contribution: SDR from medical imaging

## 2. Related Work
- PMFS and variants
- Bayesian GSL methods (GrGSL, surge_cast)
- Deconvolution in medical imaging (Richardson-Lucy)
- Gap: deconvolution not applied to GSL probability maps

## 3. Method
### 3.1 PMFS Baseline
### 3.2 SDR: Spatial Deconvolution Refinement
- Hit map construction from gas detections
- Directional PSF aligned with wind
- Richardson-Lucy deconvolution
- Peak extraction and source estimate refinement

## 4. Experiments
### 4.1 Setup
- VGR dataset (House01, House02, House03)
- Baselines: PMFS, GrGSL, surge_cast (official MAPIRlab implementations)
- Metrics: final_error_m, success_at_2m
### 4.2 Ablation Study
- SDR vs baseline across 3 houses
- Multi-source positions on House01
- Statistical significance (paired t-test, bootstrap CI)
### 4.3 Comparison with Official Baselines
### 4.4 Failure Analysis (House03)
- Exploration failure, not estimation failure
- Discussion of limitations

## 5. Discussion
- When SDR helps vs hurts
- Limitations: requires gas hits, directional PSF assumption
- Future work: adaptive PSF, exploration enhancement

## 6. Conclusion