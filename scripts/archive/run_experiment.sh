#!/bin/bash
# ED-Bayes Experiment Runner - 10 seeds × (proposed + baselines)
# Correctly extracts final_error from benchmark runner output

DIR="/tmp/edbayes_exp"
mkdir -p ""
CSV="/experiment_results.csv"
echo "method,seed,final_error,localized2,steps,elapsed,converge_type" > ""

cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

run_one() {
    local METHOD= SEED= LAUNCH= EXTRA=
    local LOG="/_s.log"
    cleanup
    local T0=1783155094
    
    # All runs use House01 A1_fast scenario
    ros2 launch vgr_bridge  \
        vgr_data_path:=/home/zyc/enva_vgr config_id:=2,4-1_fast \
        algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=5.00 source_y:=6.20 source_z:=0.50 \
        start_x:=4.0 start_y:=4.0 seed:= \
        timeout_sec:=120 use_sbd:=true \
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false \
         > "" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [  -lt 180 ]; do
        sleep 5
        WAIT=
        if grep -q 'DONE, CLOSING' "" 2>/dev/null; then sleep 3; break; fi
        if ! kill -0  2>/dev/null; then break; fi
    done
    local T1=1783155095
    local ELAPSED=
    cleanup
    
    # Extract final_error from benchmark output
    local FERR=
    local LOC2=
    local STEPS=
    if [ -z "" ]; then
        STEPS=
    fi
    local CTYPE="other"
    if grep -q 'Found the emission source' ""; then CTYPE="found"
    elif grep -q 'CP-STOP' ""; then CTYPE="cp_stop"
    elif grep -q 'DDM-STOP' ""; then CTYPE="ddm_stop"
    elif grep -q 'action_failure' ""; then CTYPE="timeout"
    fi
    
    echo ",,,,,," | tee -a ""
    sleep 2
}

echo "===== Running Proposed Method (ED-Bayes, event-driven) - 10 seeds ====="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one "ED_Bayes"  "vgr_ablation.launch.py" "opgsl.event_driven.enabled:=true"
done

echo ""
echo "===== Running Baseline (Continuous model, no event-driven) - 10 seeds ====="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one "Baseline"  "vgr_ablation.launch.py" "opgsl.event_driven.enabled:=false"
done

echo ""
echo "===== Summary ====="
cat ""
echo ""
echo "Results saved to "
