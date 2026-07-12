#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
cd /home/zyc/gsl_ws

DIR=/tmp/cp_sbd_exp/eprocess
mkdir -p "$DIR"
LOG="$DIR/verify_House01_s0_st10.log"
rm -f "$LOG"

echo "=== Starting verification run: House01 seed=0 max_steps=10 ==="
date

timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
    vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
    config_id:=2,4-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf \
    source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
    start_x:=0.30 start_y:=-1.20 seed:=0 \
    timeout_sec:=240 use_sbd:=true \
    opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
    opgsl.event_driven.enabled:=true \
    opgsl.event_driven.eta_fixed:=-1.0 \
    opgsl_max_steps:=10 \
    > "$LOG" 2>&1 || true

echo "=== Run complete ==="
date

echo "--- Key output ---"
grep -E "MAXSTEPS-STOP|EP-STOP|final_error|OPGSL-SDNBV RESULT|Found the emission" "$LOG" | sed "s/\x1b\[[0-9;]*m//g"