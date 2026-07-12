#!/bin/bash
cd /home/zyc/gsl_ws
source install/setup.bash
killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
sleep 2
timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 config_id:=2,4-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 start_x:=0.30 start_y:=-1.20 seed:=0 timeout_sec:=240 use_sbd:=true opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true opgsl.event_driven.enabled:=true opgsl.event_driven.eta_fixed:=-1.0 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'RESULT|Found|eta|entropy|H_ratio' | tail -10
killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
