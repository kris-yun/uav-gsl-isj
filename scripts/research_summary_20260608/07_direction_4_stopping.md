# 07 Direction 4: Stopping Criterion Improvement

## Status: ANALYSIS COMPLETE — PMFS premature declaration confirmed

## Key Discovery
PMFS declares "source found" after only ~6-25 seconds with 4-7m error.
The declaration is triggered by variance < threshold (default 1.5m²),
but the variance drops below threshold before the UAV has time to reach
the source.

## PMFS Baseline Analysis

### Official Configuration
- maxSearchTime: 300s
- distanceThreshold: 0.5m
- convergence_thr: PMFS=1.5, GrGSL=0.5
- flight_height: 1.0m
- scale: 3 (in official launch file; benchmark launch has 65 — WRONG)

### PMFS Behavior
| Metric | Value | Issue |
|--------|-------|-------|
| Search time | ~6-25s | Declares too fast |
| Posterior error | ~1.88m | Good posterior estimate |
| UAV path length | 0.3m | Barely moves |
| Variance at declaration | 0.40 | Below threshold 1.5 |
| Quadtree cells | 5 | Very coarse |

### Root Cause: scale Parameter
The `vgr_gsl_benchmark.launch.py` had scale=65 (default), which produces
a 1×1 PMFS grid (useless). The official `vgr_gsl_pmfs.launch.py` uses
scale=3 (29×38 grid, 1102 cells). BUT the scale parameter cannot be
dynamically passed to the GSL server due to ROS2 parameter declaration issues.

### Additional Issue: GMRF Wind Service
PMFS requires the GMRF wind estimation service to be running separately.
Without it, the quadtree has 0 cells and PMFS cannot function.

### Additional Issue: nav2_msgs
PMFS requires nav2_msgs for path planning (ComputePathToPose action).
This was not installed, causing PMFS to be unable to navigate.

## Comparison: PMFS vs SurgeCast

| Method | House01 | House02 | House03 | Behavior |
|--------|---------|---------|---------|----------|
| PMFS | 4.46m (26s) | 5.44m (26s) | 7.21m (26s) | Declares early, doesn't reach source |
| SurgeCast | 0.21m (50s) | 4.15m (305s) | 2.90m (302s) | Runs full time, reaches source |

**SurgeCast achieves 0.21m on House01 — essentially perfect.**

## Implication for Research Direction
Any method that improves PMFS from 5m to 3m is still much worse than
SurgeCast's 0.2m. The improvement would not be meaningful.

A different angle is needed — either:
1. Focus on scenarios where SurgeCast fails (complex environments)
2. Combine PMFS + SurgeCast strengths
3. Move to a different problem setting (UAV, outdoor, 3D)

## VM Configuration Issues Found
1. numpy 2.x breaks gadentools (fixed by downgrading to 1.26.4)
2. GMRF wind service must be started separately before PMFS
3. nav2_msgs must be installed for PMFS navigation
4. scale parameter not properly passed to GSL server
5. convergence_thr parameter not properly passed to GSL server
