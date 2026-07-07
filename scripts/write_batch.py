#!/usr/bin/env python3
"""Write batch experiment script for VM"""
script = '''#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

RESULTS_DIR="/tmp/edpa_experiments"
mkdir -p $RESULTS_DIR

echo "=== EDPA-GSL 10-Seed Batch Experiment ==="
echo "Source: (5.0, 6.2), Start: (4.0, 4.0), Epsilon: 0.5m"

for SEED in 0 1 2 3 4 5 6 7 8 9; do
    echo "--- Seed $SEED ---"
    
    # Run EDPA-GSL (our method)
    CSV_FILE="$RESULTS_DIR/edpa_s${SEED}.csv"
    timeout 300 ros2 launch vgr_bridge vgr_edpa.launch.py \
        seed:=$SEED \
        resultsFile:=$CSV_FILE \
        > "$RESULTS_DIR/edpa_s${SEED}.log" 2>&1
    
    # Extract result
    DIST=$(grep "map_dist" "$CSV_FILE" 2>/dev/null | tail -1 | cut -d, -f4)
    STEPS=$(grep "steps" "$CSV_FILE" 2>/dev/null | tail -1 | cut -d, -f5)
    echo "EDPA seed=$SEED: dist=$DIST steps=$STEPS"
    
    # Kill any remaining processes
    pkill -f gsl_actionserver 2>/dev/null
    pkill -f vgr_sim_node 2>/dev/null
    pkill -f gsl_benchmark 2>/dev/null
    sleep 2
done

echo ""
echo "=== Summary ==="
for SEED in 0 1 2 3 4 5 6 7 8 9; do
    CSV_FILE="$RESULTS_DIR/edpa_s${SEED}.csv"
    if [ -f "$CSV_FILE" ]; then
        DIST=$(grep "map_dist" "$CSV_FILE" 2>/dev/null | tail -1 | cut -d, -f4)
        echo "Seed $SEED: $DIST"
    else
        echo "Seed $SEED: FAILED"
    fi
done
'''

path = r"D:\ZYC\A-gas\scripts\batch_edpa.sh"
with open(path, "w", encoding="utf-8") as f:
    f.write(script)
print("Written batch script")
