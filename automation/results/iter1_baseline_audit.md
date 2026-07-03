# Baseline Audit Report

**Date**: 2026-06-07
**Auditor**: Claude Code (automated)
**Scope**: Compare current baseline implementations with official GitHub/paper algorithms

---

## 1. SurgeCastPlanner

**Source**: MAPIRlab/Gas-Source-Localization (C++/ROS2), based on "Active Source Localization" (2020)
**Current file**: `workspace/uav_diagsense/src/baselines/simple_planners.py` (line 89-121)

### Comparison

| Aspect | Official (MAPIRlab) | Current Implementation | Status |
|--------|-------------------|----------------------|--------|
| Gas detection | Binary hit/miss from sensor | Threshold `gas > 0.01` | ACCEPTABLE (simplified sensor model) |
| Upwind direction | Uses wind vector from anemometer | `wind / ||wind||`, upwind = `-u` | CORRECT |
| Cast expansion | `cast_amplitude *= expand_factor` per step | `width = min(cast_width, 1.0 + steps_since_hit * 0.3)` linear growth | DIFFERENT |
| Direction flip | Every 10 consecutive misses | Every single step (`cast_dir *= -1` always) | **INCORRECT** |
| Drift toward last hit | Implicit via upwind movement | Not implemented | MISSING |
| Step size control | Configurable step_size | Fixed 1.0m surge, variable cast | SIMPLIFIED |
| Source declaration | Not applicable (navigation-only) | Not applicable | N/A |
| Expand factor | Paper uses geometric expansion | Linear growth with cap | DIFFERENT |

### Critical Issues

1. **Cast direction flip is wrong**: Official flips every 10 consecutive misses. Current flips every step, making the cast zigzag extremely narrow (effectively staying in place laterally).

2. **Cast expansion is linear, not geometric**: Official uses multiplicative `expand_factor` (e.g., 1.5x per miss cycle). Current uses additive linear growth, which grows too slowly.

3. **No drift toward last hit**: Official implementations often bias movement toward the centroid of recent hits when plume is lost. Current has no memory of hit positions.

### Recommendation: **FIX REQUIRED**

Key fixes:
- Flip cast direction every N misses (default N=10), not every step
- Use geometric expansion: `cast_amplitude *= expand_factor` (default 1.5)
- Add drift toward last known gas detection position

---

## 2. InfotaxisPlanner

**Source**: Vergassola et al., Nature 2007; neurovertex/infotaxis (C++)
**Current file**: `workspace/uav_diagsense/src/baselines/info_planners.py` (line 7-51)

### Comparison

| Aspect | Official (Vergassola 2007) | Current Implementation | Status |
|--------|--------------------------|----------------------|--------|
| Candidate generation | 4 cardinal directions + stay in place (5 total) | 8 radial + MAP (9 total) | DIFFERENT (more candidates is acceptable) |
| Hit probability model | Poisson encounter rate from diffusion model | `exp(-dist/3.0)` Gaussian-like decay | **SIMPLIFIED** |
| Entropy computation | `H = -sum(p * log p)` over source posterior | Same formula | CORRECT |
| EIG formula | `EIG = H_current - (p_hit * H_hit + (1-p_hit) * H_miss)` | Same formula | CORRECT |
| Posterior update (hit) | Bayesian update using physical plume model | `post * p_hit_local` (element-wise) | **SIMPLIFIED** |
| Posterior update (miss) | Bayesian update: `post * (1 - p_hit)` | `post * (1 - 0.1 * p_hit_local)` | DIFFERENT (0.1 scaling) |
| p_hit computation | From diffusion-advection PDE solution | `sum(post * p_hit_local)` | APPROXIMATION |
| Grid resolution | Fixed grid, typically 100x100 | Uses posterior grid directly | ACCEPTABLE |
| Wind integration | Source model includes wind (advection-diffusion) | No wind in hit probability | **MISSING** |

### Critical Issues

1. **No physical plume model**: Official infotaxis uses a diffusion-advection source model to compute encounter rates. Current uses a simple distance-based Gaussian kernel unrelated to physics.

2. **Miss update has arbitrary 0.1 scaling**: The `(1 - 0.1 * p_hit_local)` factor is not from the paper. Should be `(1 - p_hit)` where p_hit is the expected encounter rate at that location.

3. **No wind in hit probability**: The whole point of infotaxis is that it works with wind-advected plumes. The hit probability should depend on wind direction (higher probability upwind of source).

### Recommendation: **FIX REQUIRED** (for strict fidelity) or **ACCEPTABLE** (for simplified benchmark)

For a paper benchmark, the simplified model is acceptable IF clearly documented as "simplified infotaxis." For claiming faithful reproduction of the official algorithm, a wind-aware plume model is needed.

---

## 3. KLDWaypointPlanner

**Source**: Information-theoretic variant (Hernandez-Bennet et al., various)
**Current file**: `workspace/uav_diagsense/src/baselines/info_planners.py` (line 54-89)

### Comparison

| Aspect | Literature Standard | Current Implementation | Status |
|--------|-------------------|----------------------|--------|
| KLD formula | `KL(p_new || p_old)` | `sum(p_new * log(p_new / p))` | CORRECT |
| Candidate generation | Varies (often same as infotaxis) | 8 radial + MAP | ACCEPTABLE |
| Posterior update | Bayesian update from measurement model | `post * (1 + p_hit_local)` | **NON-STANDARD** |
| Selection | argmax KLD | argmax KLD | CORRECT |

### Issues

1. **Non-standard posterior update**: `post * (1 + p_hit_local)` is not a valid Bayesian update. A proper update would be `post * p(measurement | source=h)`. The `(1 + p_hit_local)` formulation can exceed 1 and doesn't have a probabilistic interpretation.

2. **Same simplified hit model as infotaxis**: No physical plume model.

### Recommendation: **ACCEPTABLE** (documented as simplified variant)

The KLD scoring itself is correct in structure. The posterior update heuristic produces reasonable behavior despite lacking formal justification.

---

## 4. KLDPlumeMemoryPlanner (KLD-PM)

**Source**: Novel extension (not from a single paper)
**Current file**: `workspace/uav_diagsense/src/baselines/kld_plume_memory.py`

### Assessment

This is a **novel composite baseline**, not a reproduction of an existing algorithm. It combines:
- KLD waypoint selection (standard)
- Plume memory (inspired by bee waggle dance literature)
- Diagnostic mode selection (inspired by medical triage)

**No official implementation to compare against.** This is fine as a project-specific baseline, but should NOT be cited as "reproducing" any published algorithm.

### Recommendation: **ACCEPTABLE** as novel baseline. Document its components clearly.

---

## 5. AdaptiveKLDPlanner

**Source**: Novel extension (IPP/CIPP literature inspired)
**Current file**: `workspace/uav_diagsense/src/baselines/adaptive_kld.py`

### Assessment

Another **novel composite baseline**:
- Adaptive candidate radius based on entropy
- Frontier-based candidates from posterior peaks
- Path-aware KLD scoring (midpoint bonus)

**No official implementation to compare against.** Same guidance as KLD-PM.

### Recommendation: **ACCEPTABLE** as novel baseline.

---

## 6. ThompsonKLDPlanner

**Source**: Thompson Sampling (bandit literature) + KLD
**Current file**: `workspace/uav_diagsense/src/baselines/thompson_kld.py`

### Assessment

**Novel composite baseline** combining:
- Thompson Sampling (well-established in bandit literature)
- KLD as utility function
- Adaptive temperature from posterior entropy

The Thompson Sampling mechanism is correctly implemented (softmax with adaptive tau). No issues found.

### Recommendation: **ACCEPTABLE** as novel baseline.

---

## 7. Simple Planners (Random, Coverage, GreedyMAP, Spiral)

**Current file**: `workspace/uav_diagsense/src/baselines/simple_planners.py`

These are trivial reference baselines, not reproductions of published algorithms. Their purpose is to establish lower bounds.

### Recommendation: **ACCEPTABLE**. No audit needed for trivial baselines.

---

## Summary

| Baseline | Type | Fidelity to Official | Action |
|----------|------|---------------------|--------|
| SurgeCastPlanner | Reproduction | LOW (3 bugs) | **FIX** |
| InfotaxisPlanner | Reproduction | MEDIUM (simplified plume model) | FIX or document |
| KLDWaypointPlanner | Reproduction | MEDIUM (non-standard update) | Document |
| KLDModePlanner | Extension | N/A (novel) | Acceptable |
| KLDPlumeMemoryPlanner | Novel | N/A | Acceptable |
| AdaptiveKLDPlanner | Novel | N/A | Acceptable |
| ThompsonKLDPlanner | Novel | N/A | Acceptable |
| RandomPlanner | Trivial | N/A | Acceptable |
| CoveragePlanner | Trivial | N/A | Acceptable |
| GreedyMAPPlanner | Trivial | N/A | Acceptable |
| SpiralPlanner | Trivial | N/A | Acceptable |

### Statistics
- **Total baselines**: 11
- **Using official logic faithfully**: 0 (0%)
- **Reproductions needing fixes**: 2 (SurgeCast, Infotaxis)
- **Reproductions with acceptable simplification**: 1 (KLD)
- **Novel baselines (no official to compare)**: 4
- **Trivial reference baselines**: 4

### Priority Fixes

1. **SurgeCast** (HIGH): Fix cast direction flip (every 10 misses), geometric expansion, add hit drift
2. **Infotaxis** (MEDIUM): Either implement wind-aware plume model or explicitly document as "simplified infotaxis"
3. **KLD** (LOW): Document the non-standard posterior update heuristic

---

## Official Implementations Available

| Repo | Language | Algorithms | Usable? |
|------|----------|-----------|---------|
| MAPIRlab/Gas-Source-Localization | C++/ROS2 | PMFS, GrGSL, surge_cast, spiral, particle_filter | Needs porting to Python |
| neurovertex/infotaxis | C++ | Infotaxis | Needs porting to Python |
| smueller18/TDKernelDMVW | Python | KernelDM, KernelDM+V/W | Directly usable |

**Recommendation**: For SurgeCast and Infotaxis, port the core logic from the official C++ repos to Python rather than fixing the current simplified implementations. This ensures algorithmic fidelity for the paper.

