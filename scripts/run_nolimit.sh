#!/bin/bash
pkill -9 -f ros2 2>/dev/null
pkill -9 -f gsl_ 2>/dev/null
rm -rf /dev/shm/fastrtps_*
sleep 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch vgr_bridge vgr_gsl_ablation_noWRANF.launch.py \
    vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 \
    config_id:=2,4-1_fast \
    source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
    start_x:=-5.0 start_y:=-5.0 \
    seed:=0 \
    output_csv:=/tmp/gsl_clean_results/House01_PMFS_nolimit_s0.csv \
    server_results_file:=/tmp/gsl_clean_results/House01_PMFS_nolimit_s0_server.csv \
    dataset:=VGR_House01
