#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

mkdir -p /tmp/exp_final

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

run_one() {
    local LAUNCH= SEED= RESULTS=
    cleanup
    timeout 360 ros2 launch vgr_bridge  seed:= resultsFile:= > /dev/null 2>&1
    cleanup
    sleep 1
}

echo '=== Event-Driven Posterior + Search Modules (Proposed) ==='
for S in 0 1 2 3 4 5 6 7 8 9; do
    echo "  EDPA seed ..."
    run_one vgr_edpa_full.launch.py  /tmp/exp_final/proposed_s.csv
done

echo '=== Baseline (Search Modules Only, Continuous Posterior) ==='
for S in 0 1 2 3 4 5 6 7 8 9; do
    echo "  Baseline seed ..."
    run_one vgr_baseline_full.launch.py  /tmp/exp_final/baseline_s.csv
done

echo '=== Done! ==='
echo 'Results in /tmp/exp_final/'
