#!/bin/bash
cd /home/zyc/gsl_ws
source install/setup.bash
killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
sleep 2
timeout 90 ros2 launch vgr_bridge vgr_ablation.launch.py vgr_data_path:=/home/zyc/vgr_data_scenarios/House02 config_id:=3,5-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf source_x:=0.00 source_y:=-1.00 source_z:=0.20 start_x:=-0.50 start_y:=-2.50 seed:=0 timeout_sec:=60 use_sbd:=true opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true opgsl.event_driven.enabled:=true opgsl.event_driven.eta_fixed:=0.5 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'RESULT|Found|steps|Error|Traceback|move_base' | tail -10
killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
