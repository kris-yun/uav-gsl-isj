# Iteration 5: SDM Implementation Summary

**Date**: 2026-06-07
**Status**: COMPLETE

---

## What Is SDM

**Sparse Deconvolution Mapping** — borrowed from image deblurring (L1 sparse deconvolution).

**Core idea**: Wind causes the gas plume to be "smeared" downwind, like motion blur in images. The Bayesian posterior inherits this blur — the source appears shifted and spread in the downwind direction. SDM deconvolves this blur using L1-regularized sparse recovery (ISTA algorithm), sharpening the posterior to recover the true source location.

**Cross-domain mapping**:
- Motion blur kernel → wind-induced smearing (asymmetric, elongated downwind)
- Blurred image → blurred posterior
- Sparse original → sparse source (one or few point sources)
- L1 regularization → source sparsity prior
- ISTA/FISTA → iterative deconvolution solver

**Why this works**: Standard Bayesian posteriors in wind conditions are stretched downwind of the true source. L1 deconvolution enforces sparsity (few source candidates) while fitting the observed posterior, effectively reversing the wind blur.

---

## Implementation Files

### `workspace/uav_diagsense/src/sdm/sdm_estimator.py`

**`SDMEstimator`** — wraps standard Bayesian posterior with L1 deconvolution.

- **Standard update**: `update(x, wind, hit)` — same Bayesian likelihood model as other estimators (along-wind/cross-wind decomposition)
- **Blur kernel**: `_build_blur_kernel(wind)` — asymmetric Gaussian elongated downwind (`blur_sigma_along >> blur_sigma_cross`), with small upwind tail
- **Deconvolution**: `deconvolve(wind)` — ISTA (Iterative Shrinkage/Thresholding Algorithm):
  - Solves: `min_s ||K*s - b||^2 + lambda * ||s||_1`
  - Gradient step: `s -= alpha * K^T(K*s - b)`
  - Soft thresholding: `s = sign(s) * max(|s| - lambda*alpha, 0)`
  - Non-negativity + normalization each iteration
- **Key parameters**: `blur_sigma_cross=1.0`, `blur_sigma_along=3.0`, `sparsity_weight=0.05`, `n_iter=20`
- Methods: `posterior_raw()` (blurred), `posterior()` (deconvolved), `map_estimate()`, `entropy()`, `entropy_norm()`

### `workspace/uav_diagsense/src/sdm/sdm_planner.py`

**`SDMPlanner`** — uses deconvolved posterior for action selection.

- KLD-based waypoint scoring over deconvolved posterior
- Deconvolution runs every `deconv_interval` steps (default 5) to amortize cost
- Candidates: radial, MAP, upwind (on gas detection)
- Entropy-adaptive mode selection

---

## Tests

### `workspace/uav_diagsense/tests/test_sdm.py`

| Test | What it checks | Status |
|------|---------------|--------|
| `test_raw_posterior_updates` | Standard Bayesian update works (hits increase peak) | PASS |
| `test_deconvolution_sharpens` | Deconvolved entropy < raw entropy | PASS |
| `test_deconvolution_shifts_toward_source` | Deconv MAP not much worse than raw MAP | PASS |
| `test_sparsity_property` | Deconv posterior has higher peak (sparser) | PASS |

### Key design decisions

1. **Asymmetric blur kernel**: Wind causes downwind smearing, not isotropic blur. The kernel uses `blur_sigma_along` (downwind, default 3.0) >> `blur_sigma_cross` (crosswind, default 1.0), matching the physical plume shape.

2. **L1 (not L2) regularization**: L1 promotes sparse solutions — the source is a point, not a distributed region. L2 would smooth rather than sharpen.

3. **ISTA algorithm**: Simple, provably convergent, and efficient for our grid sizes (N~100-400). Each iteration is O(N^2) for the kernel multiply, but N is small enough that this is fast.

4. **Periodic deconvolution**: The full deconvolve step (kernel build + ISTA) is more expensive than a standard posterior update. Running it every 5 steps amortizes the cost while keeping the posterior reasonably up-to-date.

---

## Status

- Code: implemented and tested (4/4 tests pass)
- Integration: SDMPlanner follows same interface as other planners
- Ready for experiment
