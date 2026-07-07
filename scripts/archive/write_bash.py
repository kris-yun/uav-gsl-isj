import os
script = """#!/bin/bash
DIR=/tmp/edbayes_exp
mkdir -p ""
CSV="/results.csv"
echo "method,seed,final_error,localized2,steps,type" > ""
cd /home/zyc/gsl_ws
source install/setup.bash

run_one() {
    local M= S= E=
    local L="/_s.log"
    pkill -9 -f gsl_actionserver 2>/dev/null
    pkill -9 -f vgr_sim 2>/dev/null
    pkill -9 -f benchmark_runner 2>/dev/null
    sleep 2
    ros2 launch vgr_bridge vgr_ablation.launch.py vgr_data_path:=/home/zyc/enva_vgr config_id:=2,4-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf source_x:=5.00 source_y:=6.20 source_z:=0.50 start_x:=4.0 start_y:=4.0 seed:= timeout_sec:=120 use_sbd:=true opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false  > "" 2>&1 &
    local P=$!
    local W=0
    while [  -lt 180 ]; do
        sleep 5
        W=
        if grep -q "DONE, CLOSING" "" 2>/dev/null; then sleep 3; break; fi
        if ! kill -0  2>/dev/null; then break; fi
    done
    pkill -9 -f gsl_actionserver 2>/dev/null
    pkill -9 -f vgr_sim 2>/dev/null
    pkill -9 -f benchmark_runner 2>/dev/null
    local FE=
    local L2=
    local ST=0
    local T="other"
    if grep -q "Found the emission" ""; then T="found"
    elif grep -q "action_failure" ""; then T="timeout"
    fi
    echo ",,,,," | tee -a ""
    sleep 2
}

echo "=== ED-Bayes (event-driven) 10 seeds ==="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one ED_Bayes  "opgsl.event_driven.enabled:=true"
done

echo "=== Baseline (continuous) 10 seeds ==="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one Baseline  "opgsl.event_driven.enabled:=false"
done

echo "=== Summary ==="
cat ""
"""
with open("/tmp/run_edbayes.sh", "w") as f:
    f.write(script)
os.chmod("/tmp/run_edbayes.sh", 0o755)
print("Script written to /tmp/run_edbayes.sh")