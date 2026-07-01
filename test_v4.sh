#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

mkdir -p /tmp/exp_v4
pkill -9 -f ros2 2>/dev/null
pkill -9 -f gsl 2>/dev/null
sleep 2

echo "[$(date)] Starting SD-NBV v4 test on House01 seed=0 ..."

timeout 330 ros2 launch vgr_bridge vgr_opgsl3d_ablation.launch.py \
  vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
  algorithm:=OPGSL \
  method:=M0_sc_pf_hard_base \
  method_family:=proposed_ablation \
  ablation_id:=SDNBVv4 \
  run_id:=SDNBVv4_House01_s0 \
  run_dir:=/tmp/exp_v4/SDNBVv4_s0 \
  output_dir:=/tmp/exp_v4 \
  environment_id:=House01 \
  scenario_id:=House01_default \
  dataset:=House01 \
  config_id:=2,4-1_fast \
  source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
  start_x:=-0.9 start_y:=0.15 \
  seed:=0 \
  flight_height:=0.3 \
  timeout_sec:=300.0 \
  resultsFile:=/tmp/exp_v4/SDNBVv4_s0_result.txt \
  > /tmp/exp_v4/SDNBVv4_s0.log 2>&1 || true

result=$(grep "RESULT IS:" /tmp/exp_v4/SDNBVv4_s0.log 2>/dev/null | tail -1)
echo "RESULT: $result"
echo "[$(date)] Done."