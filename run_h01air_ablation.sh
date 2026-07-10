#!/bin/bash
# H01_air ablation: 7 configs x 10 seeds = 70 runs
# Source: House01, config 1,3-2,4_fast, source at (-0.60, 1.95, 0.40)

source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

RESULTS="/tmp/v8_exp/ablation_h01air/results.csv"
mkdir -p /tmp/v8_exp/ablation_h01air
echo "config,seed,error_m,localized,elapsed_s" > "$RESULTS"

CONFIGS=(
    "M7_full_saisc_pf:Full"
    "M7_full_saisc_pf:A1_FixedEta:opgsl.modules.adaptive_eta:=false"
    "M7_full_saisc_pf:A2_NoEProc:opgsl.e_process.enabled:=false"
    "M7_full_saisc_pf:A3_NoDDM:opgsl.ddm.enabled:=false"
    "M7_full_saisc_pf:A4_NoLevy:opgsl.modules.levy:=false"
    "M7_full_saisc_pf:A5_NoUpwind:opgsl.modules.upwind_tracking:=false"
    "M7_full_saisc_pf:A6_NoGPAlt:opgsl.altitude.gp:=false"
)

for cfg in "${CONFIGS[@]}"; do
    IFS=':' read -r method name extra_args <<< "$cfg"
    echo "=== Running $name ==="
    for seed in $(seq 0 9); do
        echo "  Seed $seed..."
        LOG="/tmp/v8_exp/ablation_h01air/${name}_s${seed}.log"
        EXTRA=""
        if [ -n "$extra_args" ]; then
            EXTRA="$extra_args"
        fi
        
        timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py \
            method:=M7_full_saisc_pf \
            algorithm:=OPGSL \
            opgsl.event_driven.enabled:=true \
            opgsl.seed:=$seed \
            scenario:=H01_air \
            $EXTRA 2>&1 > "$LOG"
        
        # Extract result from log
        DIST=$(grep -oP 'Final endpoint distance.*?: \K[0-9.]+' "$LOG" | tail -1)
        LOC=$(grep -oP 'Localized.*?: \K[01]' "$LOG" | tail -1)
        ELAPSED=$(grep -oP 'elapsed.*?: \K[0-9.]+' "$LOG" | tail -1)
        
        if [ -z "$DIST" ]; then
            DIST=$(grep -oP 'distance.*?: \K[0-9.]+' "$LOG" | tail -1)
        fi
        if [ -z "$LOC" ]; then
            LOC="0"
        fi
        if [ -z "$ELAPSED" ]; then
            ELAPSED="300"
        fi
        
        echo "$name,$seed,$DIST,$LOC,$ELAPSED" >> "$RESULTS"
        echo "    -> dist=$DIST loc=$LOC"
        
        # Kill any lingering processes
        pkill -f gsl_actionserver 2>/dev/null
        pkill -f vgr_sim_node 2>/dev/null
        sleep 2
    done
done

echo "=== DONE ==="
cat "$RESULTS"
