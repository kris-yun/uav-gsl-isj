# Iteration 2: MEMP Implementation Summary

**Date**: 2026-06-07
**Status**: COMPLETE

---

## What Is MEMP

**Medical Evidence Mass Processing** — borrowed from EEG brain source localization (LORETA, Pascual-Marqui et al. 1994/2002).

**Core idea**: Add a Laplacian smoothness constraint to the Bayesian posterior to prevent isolated peaks and enforce spatial coherence.

**Cross-domain mapping**:
- EEG scalp sensors → gas sensors (sparse, noisy)
- Brain dipole → gas source (localized)
- Volume conductor → wind transport
- Spatial smoothness → plume continuity (gas doesn't teleport)

**Standard Bayes**: `P(s|z) ~ P(z|s) * P(s)`
**MEMP Bayes**: `P(s|z) ~ P(z|s) * P(s) * exp(-lambda * ||L*s||^2)`

Where `L` = graph Laplacian of free-space grid, `lambda` = smoothness weight.

---

## Implementation Files

### `workspace/uav_diagsense/src/memp/memp_posterior.py`
- `MEMPPosteriorEstimator` class
- `_build_laplacian()`: constructs sparse graph Laplacian (D - A) over 4-connected free-space grid
- `update(x, wind, hit)`: Bayesian update in log-space + Laplacian smoothing penalty
- `posterior()`, `entropy()`, `entropy_norm()`, `map_estimate()`
- Laplacian built once at init, applied every update step
- Smoothness weight is a hyperparameter (default 0.1)

### `workspace/uav_diagsense/src/memp/memp_planner.py`
- `MEMPPlanner(DQAASPlanner)`: inherits DQA-AS action selection
- Replaces standard posterior with `MEMPPosteriorEstimator`
- Syncs observations from `obs_history` to MEMP estimator each step
- Scores candidate actions using MEMP-smoothed posterior
- Inherits exploration bonus, revisit penalty, and A* pathfinding from DQA-AS

---

## Tests

### Unit tests (in `memp_posterior.py`)

| Test | What it checks | Status |
|------|---------------|--------|
| `test_laplacian_construction` | L is N×N, symmetric, non-negative diagonal, row sums = 0 | PASS |
| `test_smoothness_constraint` | Isolated peak at (2,2) receives positive penalty | PASS |
| `test_posterior_convergence` | 20 hit observations near (2,2) → posterior peak within 2m | PASS |

### Integration tests (`tests/test_memp_signal.py`)

| Test | What it checks | Status |
|------|---------------|--------|
| `test_memp_responds_to_gas_signal` | Hit vs miss produce different posteriors; hit posterior has lower entropy | PASS |
| `test_memp_planner_receives_gas_from_obs_history` | `gas > 0.01` correctly maps to `hit=True` | PASS |

### Bug fix applied
- **Original**: `last.get("hit", False)` — `"hit"` key never exists in obs_history
- **Fixed**: `float(last.get("gas", 0.0)) > 0.01`

---

## Laplacian Properties (verified)

- **Symmetry**: `L = L^T` (graph Laplacian of undirected grid)
- **Positive semi-definite**: all eigenvalues ≥ 0
- **Row sums = 0**: constant vector is in null space
- **Sparse**: O(N) non-zeros for 4-connected grid (stored as `scipy.sparse.csr_matrix`)

The Laplacian penalizes the gradient magnitude of the posterior: `||L*p||^2 = sum over edges (p_i - p_j)^2`. High values mean rapid spatial changes → the penalty pushes the posterior toward spatial smoothness.

---

## Status

- Code: implemented and tested
- Gas signal integration: fixed (was broken, now passes integration test)
- DQA-AS integration: MEMPPlanner inherits full action library
- Ready for experiment (Iteration 3)
