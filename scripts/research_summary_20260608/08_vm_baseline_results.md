# 08 VM Baseline Results

## Experiment Setup
- Platform: Ubuntu VM (ROS2 Humble, GADEN simulator)
- Dataset: VGR House01-03 (indoor CFD simulation)
- Seeds: 3 per house per algorithm (limited by time)
- maxSearchTime: 300s
- distanceThreshold: 0.5m
- flight_height: 1.0m

## Results Summary

### House01 (source=(-0.4, -2.9), config=2,4-1_fast)
| Method | Seed | Min Dist | Time | S@2m |
|--------|------|----------|------|------|
| PMFS | s0 | 2.70m | 25s | 0 |
| PMFS | s1 | 7.33m | 26s | 0 |
| PMFS | s2 | 3.37m | 25s | 0 |
| SurgeCast | s0 | 0.24m | 139s | 1 |
| SurgeCast | s1 | 0.08m | 4s | 1 |
| SurgeCast | s2 | 0.30m | 8s | 1 |

### House02 (source=(0.0, -1.0), config=3,5-1_fast)
| Method | Seed | Min Dist | Time | S@2m |
|--------|------|----------|------|------|
| PMFS | s0 | 7.37m | 26s | 0 |
| PMFS | s1 | 4.19m | 41s | 0 |
| PMFS | s2 | 4.75m | 26s | 0 |
| SurgeCast | s0 | 5.13m | 323s | 0 |
| SurgeCast | s1 | 2.28m | 320s | 1 |
| SurgeCast | s2 | 5.05m | 317s | 0 |

### House03 (source=(-0.45, 1.9), config=1-2,5_fast)
| Method | Seed | Min Dist | Time | S@2m |
|--------|------|----------|------|------|
| PMFS | s0 | 4.56m | 26s | 0 |
| PMFS | s1 | 12.43m | 26s | 0 |
| PMFS | s2 | 4.65m | 26s | 0 |
| SurgeCast | s0 | 2.90m | 317s | 0 |
| SurgeCast | s1 | — | — | — |
| SurgeCast | s2 | — | — | — |

### Aggregated Summary
| House | PMFS Mean | SurgeCast Mean | Observation |
|-------|-----------|---------------|-------------|
| House01 | 4.46m (26s) | **0.21m** (50s) | SurgeCast dominates |
| House02 | 5.44m (26s) | **4.15m** (305s) | SurgeCast better but 12× slower |
| House03 | 7.21m (26s) | **2.90m** (302s) | SurgeCast better but 12× slower |

### Key Findings
1. **PMFS declares too early** (~26s) with 4-7m error
2. **SurgeCast achieves near-perfect on House01** (0.21m) but takes 50-300s
3. **SurgeCast fails on House02** (5.13m on one seed)
4. **All methods fail on complex environments** (House02, House03)
5. PMFS posterior error is 1.88m (good) but UAV doesn't move to reach it

### Failed Experiments
- GrGSL: consistently timed out (180s) on all houses — configuration issue
- Many experiments failed due to resource contention between sequential runs
- numpy 2.x breaking gadentools caused mass failures (fixed)
- GMRF wind service not running caused PMFS quadtree=0 cells (fixed)
- nav2_msgs not installed caused PMFS navigation failure (fixed)

## Data Files
- `/tmp/gsl_final_results/*.csv` on VM
- `workspace/outputs/adpf_pilot_results.csv` (AD-PF experiments)
- `workspace/outputs/adpf_pilot_v2.csv` (AD-PF v2)
- `workspace/outputs/sdpf_pilot.csv` (SD-PF experiments)
