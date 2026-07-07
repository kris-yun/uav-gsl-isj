#!/bin/bash
kill -9 $(pgrep -f vgr_sim_node) 2>/dev/null
kill -9 $(pgrep -f gsl_actionserver) 2>/dev/null
kill -9 $(pgrep -f batch) 2>/dev/null
kill -9 $(pgrep -f vgr_ablation) 2>/dev/null
kill -9 $(pgrep -f benchmark_runner) 2>/dev/null
sleep 3
echo "Remaining ROS processes:"
pgrep -c -f vgr_sim_node 2>/dev/null || echo 0