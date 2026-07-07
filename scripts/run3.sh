#!/bin/bash
for seed in 0 1 2; do
    echo "=== Running seed $seed ==="
    timeout 140 ros2 launch vgr_bridge vgr_ablation.launch.py seed:=$seed timeout_sec:=120 opgsl_cp:=false opgsl_ddm:=false 2>&1 | grep -E 'RESULT|TIMEOUT|CONVERGED' | tail -2
    sleep 2
done
echo "=== DONE ==="