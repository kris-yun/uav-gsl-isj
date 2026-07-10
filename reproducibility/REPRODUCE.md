# GBI-GSL Experiment Reproducibility Guide

## Environment

- **OS**: Ubuntu 22.04 (VM: zyc@192.168.111.128, password: 123456)
- **ROS2**: Humble
- **Workspace**: /home/zyc/gsl_ws
- **Dataset**: GADEN olfaction dataset (Zenodo: 10842409)
  - Data path: /home/zyc/vgr_data_scenarios/
  - Houses used: House01, House02/House02, House03/House03
  - Only need GADEN_files.zip (30.9GB), not OpenFOAM_files or models_FBX

## Scenario Configurations

| Scenario | Data Path | Config ID | Source XYZ | Start XY |
|----------|-----------|-----------|------------|----------|
| H01_gnd | House01 | 2,4-1_fast | -0.40,-2.90,-0.30 | 0.30,-1.20 |
| H01_air | House01 | 1,3-2,4_fast | -0.60,1.95,0.40 | -0.90,0.15 |
| H02_air | House02/House02 | 3,5-1_fast | 0.00,-1.00,0.20 | -0.50,-2.50 |
| H03_gnd | House03/House03 | 1-2,5_fast | -0.45,1.90,-0.10 | 2.00,0.00 |

IMPORTANT: Source coordinates are from the GADEN dataset. Do NOT modify them.

## How to Run Our Method (GBI-GSL / OPGSL)

    source /opt/ros/humble/setup.bash
    source /home/zyc/gsl_ws/install/setup.bash

    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
        config_id:=2,4-1_fast \
        algorithm:=OPGSL \
        method:=M7_full_saisc_pf \
        opgsl.event_driven.enabled:=true \
        source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
        start_x:=0.30 start_y:=-1.20 \
        flight_height:=1.0 \
        seed:=0 timeout_sec:=300 \
        run_dir:=/tmp/exp/OPGSL_H01_gnd_s0

Key parameters:
- method:=M7_full_saisc_pf (canonical name for our full method)
- opgsl.event_driven.enabled:=true (enables event-driven updates)
- Ablation: opgsl.modules.cp:=false, opgsl.modules.ddm:=false, etc.

## How to Run Baselines (SurgeCast, GrGSL, PMFS)

All baselines use vgr_gsl_pmfs.launch.py:

    # SurgeCast
    ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
        config_id:=2,4-1_fast \
        algorithm:=SensorAwareSurgeCastPF \
        method:=B3_surge_cast_pf_official \
        source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
        start_x:=0.30 start_y:=-1.20 \
        flight_height:=1.0 seed:=0 timeout_sec:=300 \
        run_dir:=/tmp/exp/SurgeCast_H01_gnd_s0

    # GrGSL: algorithm:=GrGSL method:=B5_GrGSL_official
    # PMFS: algorithm:=PMFS method:=B4_PMFS_official

### PMFS Wind Field Configuration (CRITICAL)

PMFS requires real wind field data from GADEN. Without it, PMFS falls back to
uniform wind and produces incorrect deterministic results.

What was fixed (must be applied to reproduce):
1. gsl_server/CMakeLists.txt: set(USE_GADEN ON) (was OFF)
2. vgr_gsl_pmfs.launch.py: Added wind_value_server node + 5s TimerAction delay
3. PMFSLib.cpp: Added retry logic (10 attempts x 2s wait_for_service)

Why: Python wind_value_server <-> C++ PMFS DDS service discovery is unreliable.
The 5-second delay ensures the service is registered before PMFS tries to call it.

Verification: After launch, look for:
    [gsl_actionserver_node]: Wind data loaded from service (NNN cells)
If you see "Wind service unavailable", the DDS fix did not work.

## Data Extraction

Results written by gsl_benchmark_runner to run_dir:
- run_status.json (status, method, seed)
- official_gsl_results.csv (PMFS/GrGSL/SurgeCast results)
- saisc_pf_audit.csv (OPGSL algorithm trace)

Parsing logs: Logs contain ANSI color codes. Strip before parsing:
    sed 's/\x1b\[[0-9;]*m//g' logfile.log | grep 'RESULT IS'

## Known Issues

1. DDS service discovery: Python<->C++ service calls unreliable. Fixed with
   5s startup delay + 10-retry logic.
2. PMFS determinism: PMFS GMRF wind estimator is deterministic. Endpoint
   distance varies by seed because UAV trajectory differs.
3. H02/H03 data path: House02 and House03 have NESTED paths
   (e.g., House02/House02). Using flat path will fail silently.
4. ANSI color codes: GSL logs contain ANSI escape codes. Always strip.
5. benchmark_runner crash: Runner may crash but does not affect algorithm.
   Extract results from GSL log RESULT IS line.
6. Method naming: Paper uses "GBI-GSL", code uses "OPGSL".
   Canonical method name is M7_full_saisc_pf.

## File Structure

    reproducibility/
    +-- REPRODUCE.md
    +-- launch/
    |   +-- vgr_ablation.launch.py    (our method + ablation)
    |   +-- vgr_gsl_pmfs.launch.py    (all baselines + wind_value_server)
    +-- scripts/
    |   +-- run_pmfs.sh               (PMFS batch runner)
    +-- wind_value_server.py          (wind field service node)
    +-- gsl_benchmark_runner.py       (result extraction)
    +-- setup_vgr_bridge.py           (entry points)
## Recent Updates (2026-07-10)

### Regret-Based Adaptive Eta
The adaptive learning rate ¦Ç now uses Gr¨¹nwald's Safe Bayesian framework:
- Formula: ¦Ç_t = 1/(1 + ¦Ã?_t), where ¦Ã?_t is EMA of mixability gap
- Replaces hand-crafted coefficients {0.6, 0.3, 0.15, 0.35}
- Reference: Gr¨¹nwald (2012), Gr¨¹nwald & van Ommen (2017)

### Experiment Data
- Main benchmark: 160 runs (4 methods ¡Á 4 scenarios ¡Á 10 seeds)
- Ablation H01_gnd: 70 runs (7 configs ¡Á 10 seeds) - COMPLETE
- Ablation H01_air: 70 runs (7 configs ¡Á 10 seeds) - RUNNING

### Key Results
| Method | Overall Error | Success Rate |
|--------|--------------|-------------|
| GBI-GSL | 1.62¡À0.72m | 92.5% |
| SurgeCast | 2.74¡À1.77m | 30% |
| GrGSL | 4.86¡À3.22m | 12.5% |
| PMFS | 3.43¡À2.05m | 50% |
