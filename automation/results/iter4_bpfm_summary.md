# Iteration 4: BPFM Implementation Summary

**Date**: 2026-06-07
**Status**: COMPLETE

---

## What Is BPFM

**Bayesian Particle Flow Mapping** — borrowed from epidemiological source estimation (Riley et al. 2003; Wallinga & Teunis 2004).

**Core idea**: Maintain particles representing candidate source locations. Particles flow along wind trajectories instead of random diffusion — when gas is detected, particles move upwind (toward the source); when no gas, particles diffuse (explore).

**Cross-domain mapping**:
- Transport network → wind field
- Infection chain → gas plume trajectory
- Contact tracing → upwind back-trace
- Superspreader → high-concentration zone

**Why this works**: Standard grid posteriors can have spurious isolated peaks. Particle-based representation naturally concentrates mass where evidence is strong, and the wind-driven flow means particles converge toward the source faster than random diffusion.

---

## Implementation Files

### `workspace/uav_diagsense/src/bpfm/bpfm_estimator.py`

**`BPFMEstimator`** — particle-based posterior with wind-driven flow.

- Maintains `n_particles` (default 200) particles in 2D space
- **Flow step**: on hit, all particles shift upwind by `flow_speed`; on miss, particles diffuse isotropically
- **Weight update**: upwind likelihood model — particles upwind of the observation (along plume axis) get higher weight; crosswind spread penalized
- **Resampling**: systematic resampling when ESS drops below threshold; jitter added to prevent collapse
- **Posterior**: kernel density estimate over grid from weighted particles
- Methods: `update(x, wind, hit)`, `posterior()`, `entropy()`, `entropy_norm()`, `map_estimate()`, `particle_centroid()`

### `workspace/uav_diagsense/src/bpfm/bpfm_planner.py`

**`BPFMPlanner`** — uses BPFM posterior for action selection.

- KLD-based waypoint scoring over BPFM posterior
- Candidates include: radial directions, MAP estimate, particle centroid, upwind points (when gas detected), last-hit position (when plume lost)
- Entropy-adaptive mode selection (fast/explore vs slow/exploit vs hover/confirm)

---

## Tests

### `workspace/uav_diagsense/tests/test_bpfm.py`

| Test | What it checks | Status |
|------|---------------|--------|
| `test_particle_init` | Particles initialized correctly, weights sum to 1 | PASS |
| `test_flow_upwind_on_hit` | Centroid moves upwind on hit (east wind → negative x shift) | PASS |
| `test_diffusion_on_miss` | Particle spread increases on miss (exploration) | PASS |
| `test_posterior_convergence` | 20 upwind observations → MAP within 3m of source | PASS |
| `test_ess_resampling` | Resampling triggers and preserves particle diversity | PASS |

### Key design decisions

1. **Upwind likelihood model** (not proximity): When gas is detected at position x with wind w, the source is UPWIND of x. The weight model gives high weight to particles that are upwind and aligned with the plume axis — this is the epidemiological insight (trace contacts backward along the transport network).

2. **Systematic resampling with jitter**: Prevents particle degeneracy while maintaining diversity. Jitter of 0.15 cell-sizes prevents all particles from collapsing to a single location.

3. **Flow speed vs diffusion**: Flow speed (0.8) is ~4x the diffusion sigma (0.2), giving strong directional bias on hits while maintaining exploration on misses.

---

## Status

- Code: implemented and tested (5/5 tests pass)
- Integration: BPFMPlanner follows same interface as other planners
- Ready for experiment
