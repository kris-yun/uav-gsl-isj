# 06 Direction 3: BAMS (Bayesian Adaptive Multi-hypothesis Search)

## Status: PARTIALLY VIABLE — M1+M2 work (+13.2% synthetic), but M3 fails repeatedly

## Method
3-module framework with cross-domain innovations:
- M1: Asymmetric Wind Likelihood (Physics: atmospheric dispersion)
- M2: Levy Flight Exploration (Biology: optimal foraging, Nature 1999)
- M3: Various attempts — all failed

## M3 Attempt Log (4 attempts, all failed)

| M3 Candidate | Source Field | Result | Failure Reason |
|---|---|---|---|
| Encounter Confidence | Bayesian decision theory | 0% | No effect on posterior |
| Spatial Diversity | Exploration theory | **-12%** | Pulls posterior away from source |
| Spatial Coherence (Laplacian) | Medicine: EEG/LORETA | **-10%** | Smooths out posterior peaks |
| Wind Reliability | Sensor fusion | 0% | Reliability always ~0.5, no effect |

### Why M3 Keeps Failing
M1 and M2 work because they modify the LIKELIHOOD (how observations update
the posterior). M3 candidates modify the POSTERIOR ITSELF or the UPDATE STRENGTH
— both degrade the carefully constructed likelihood signal.

## Synthetic Results (M1+M2, 5 scenarios × 10 seeds)

| Scenario | Baseline | M1+M2 | Improvement |
|----------|----------|-------|-------------|
| Strong wind (6 m/s) | 84.4m | 63.4m | **+24.9%** |
| Far source | 156.3m | 137.1m | **+12.2%** |
| Noisy | 74.4m | 66.5m | **+10.6%** |
| Medium wind | 77.4m | 69.0m | **+10.9%** |
| Weak wind | 107.3m | 97.7m | +9.0% |
| **Overall** | 100.0 | 86.8 | **+13.2%** |

## MATRIX Real Data Results (M1+M2)

| Trial | Wind | Baseline | M1+M2 | Result |
|-------|------|----------|-------|--------|
| 225_01 | 4.5 m/s | 4.4m | 2.8m | WIN |
| 225_02 | 5.5 m/s | 3.3m | 9.6m | LOSE |
| 312_01 | 3.3 m/s | 223m | 210m | WIN |
| 312_03 | 3.5 m/s | 203m | 192m | WIN |
| 313_01 | 3.6 m/s | 216m | 203m | WIN |
| 313_02 | 2.8 m/s | 211m | 200m | WIN |
| 313_04 | 2.7 m/s | 184m | 175m | WIN |
| 314_01 | 0.7 m/s | 294m | 310m | LOSE |
| 314_02 | 0.5 m/s | 295m | 313m | LOSE |

Win rate: 6/9 (but improvement on real data is modest)

## Key Problem
The BAMS approach uses a SIMPLE GRID-BASED POSTERIOR that cannot compete with
PMFS's filament simulation. Even with M1+M2 improvements, the absolute accuracy
(170-310m) is far worse than PMFS (4-7m) or SurgeCast (0.2-5m).

The grid-based posterior is fundamentally too weak for GSL. No amount of
module additions can compensate for a bad foundation.

## Code Location
- `workspace/scripts/run_bams_v31.py` (final synthetic version)
- `workspace/scripts/run_bams_v32.py` (with Bayesian stopping)
- `workspace/modules/bams/bams_search.py` (clean module)
- `workspace/modules/bams/run_bams_matrix.py` (MATRIX runner)
