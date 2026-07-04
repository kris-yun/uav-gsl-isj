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

echo "=== Proposed (Event-Driven Posterior + Modules) ==="
for S in 0 1 2 3 4 5 6 7 8 9; do
    echo "Proposed seed $S..."
    cleanup
    timeout 360 ros2 launch vgr_bridge vgr_edpa_full.launch.py seed:=$S resultsFile:=/tmp/exp_final/proposed_s${S}.csv > /tmp/exp_final/proposed_s${S}.log 2>&1
    cleanup
    sleep 1
done

echo "=== Baseline (Continuous Posterior + Modules) ==="
for S in 0 1 2 3 4 5 6 7 8 9; do
    echo "Baseline seed $S..."
    cleanup
    timeout 360 ros2 launch vgr_bridge vgr_baseline_full.launch.py seed:=$S resultsFile:=/tmp/exp_final/baseline_s${S}.csv > /tmp/exp_final/baseline_s${S}.log 2>&1
    cleanup
    sleep 1
done

echo "=== DONE ==="
