# 11 Experiment Logs

## Direction 1: AD-PF
- Script: `workspace/scripts/run_adpf_pilot.py`
- Script: `workspace/scripts/run_adpf_synthetic.py`
- Results: `workspace/outputs/adpf_pilot_results.csv`
- Results: `workspace/outputs/adpf_pilot_v2.csv`
- Conclusion: +3.3% on real data, +20% on weak-wind synthetic only

## Direction 2: LP-PF
- Script: `workspace/scripts/run_lppf_pilot.py`
- Script: `workspace/scripts/run_lppf_v2.py`
- Conclusion: AUDIT FAIL — data leakage, overfitting

## Direction 3: BAMS
- Script: `workspace/scripts/run_bams_v31.py` (synthetic)
- Script: `workspace/scripts/run_bams_v32.py` (with stopping)
- Module: `workspace/modules/bams/bams_search.py`
- Module: `workspace/modules/bams/run_bams_matrix.py`
- VM Results: `/tmp/bams_results/bams_matrix_results.csv`
- Conclusion: M1+M2 +13.2% synthetic, M3 fails 4 times

## Direction 4: SD-PF (Sensor Dynamics)
- Script: `workspace/scripts/run_sdpf_pilot.py`
- Results: `workspace/outputs/sdpf_pilot.csv`
- Conclusion: +3.5% on real data, sensor dynamics contribution negligible

## VM Baseline Runs
- Script: `workspace/scripts/run_baselines_final.py`
- Results on VM: `/tmp/gsl_final_results/*.csv`
- PMFS (correct): scale=3, GMRF running, convergence_thr=1.5
- SurgeCast: runs full 300s
- House01 PMFS mean: 4.46m
- House01 SurgeCast mean: 0.21m

## Key VM Files
- PMFS launch: `~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_pmfs.launch.py`
- Benchmark launch: `~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_benchmark.launch.py`
- GSL server source: `~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/`
- GMRF wind: `~/ros2_ws/src/GMRF-wind/`
- VGR data: `/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/`

## VM Configuration Fixes Applied
1. numpy downgraded from 2.2.6 to 1.26.4 (gadentools compatibility)
2. nav2_msgs installed (PMFS navigation requirement)
3. GMRF wind service must be started before PMFS
4. scale=3 hardcoded in PMFS launch (not 65)
5. convergence_thr parameter added to launch file
6. server_results_file and server_path_file added to launch file

## Research Log
- Full log: `workspace/outputs/research_direction_log.md`
