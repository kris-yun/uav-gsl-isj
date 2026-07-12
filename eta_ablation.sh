#!/bin/bash
# eta_ablation.sh - Run eta ablation experiments
# Tests: adaptive eta vs fixed eta=0.1, 0.3, 0.5, 0.7, 1.0

set -e
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTPUT_DIR="/tmp/cp_sbd_exp/eta_ablation"
mkdir -p "$OUTPUT_DIR"
RESULTS="$OUTPUT_DIR/results.csv"
echo "method,house,seed,eta,dist,steps,elapsed,converge_type" > "$RESULTS"

# Configurations
HOUSES=("House01" "House02" "House03")
CONFIGS=("2,4-1_fast" "3,5-1_fast" "1-2,5_fast")
SOURCES_X=("-0.40" "0.00" "-0.45")
SOURCES_Y=("-2.90" "-1.00" "1.90")
SOURCES_Z=("-0.30" "0.20" "-0.10")
STARTS_X=("0.30" "-0.50" "2.00")
STARTS_Y=("-1.20" "-2.50" "0.00")

ETA_VALUES=("0.1" "0.3" "0.5" "0.7" "1.0")
SEEDS=$(seq 0 4)  # 5 seeds per config

for h_idx in 0 1 2; do
    HOUSE=${HOUSES[$h_idx]}
    CONFIG=${CONFIGS[$h_idx]}
    SX=${SOURCES_X[$h_idx]}
    SY=${SOURCES_Y[$h_idx]}
    SZ=${SOURCES_Z[$h_idx]}
    STX=${STARTS_X[$h_idx]}
    STY=${STARTS_Y[$h_idx]}
    
    for ETA in "${ETA_VALUES[@]}"; do
        for SEED in $SEEDS; do
            echo "[$HOUSE] fixed_eta=$ETA seed=$SEED"
            
            timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
                vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
                config_id:=$CONFIG algorithm:=OPGSL method:=M7_full_saisc_pf \
                source_x:=$SX source_y:=$SY source_z:=$SZ \
                start_x:=$STX start_y:=$STY seed:=$SEED timeout_sec:=240 \
                use_sbd:=true opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
                opgsl.event_driven.enabled:=true \
                opgsl.event_driven.eta_fixed:=$ETA \
                2>&1 | tail -1 | tee -a /tmp/eta_ablation_raw.log || echo "TIMEOUT/ERROR"
            
            # Extract result from log
            DIST=$(grep -oP 'MAP distance.*?(\d+\.\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+\.\d+' | tail -1)
            STEPS=$(grep -oP 'Total steps.*?(\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+' | tail -1)
            ELAPSED=$(grep -oP 'Elapsed time.*?(\d+\.\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+\.\d+' | tail -1)
            STATUS=$(grep -oP 'converge_type.*?(\w+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\w+$' | tail -1)
            
            echo "FixedEta_$ETA,$HOUSE,$SEED,$ETA,${DIST:-NaN},${STEPS:-0},${ELAPSED:-0},${STATUS:-unknown}" >> "$RESULTS"
        done
    done
done

# Also run adaptive eta (eta_fixed=-1 means use surprisal)
for h_idx in 0 1 2; do
    HOUSE=${HOUSES[$h_idx]}
    CONFIG=${CONFIGS[$h_idx]}
    SX=${SOURCES_X[$h_idx]}
    SY=${SOURCES_Y[$h_idx]}
    SZ=${SOURCES_Z[$h_idx]}
    STX=${STARTS_X[$h_idx]}
    STY=${STARTS_Y[$h_idx]}
    
    for SEED in $SEEDS; do
        echo "[$HOUSE] adaptive_eta seed=$SEED"
        
        timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
            vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
            config_id:=$CONFIG algorithm:=OPGSL method:=M7_full_saisc_pf \
            source_x:=$SX source_y:=$SY source_z:=$SZ \
            start_x:=$STX start_y:=$STY seed:=$SEED timeout_sec:=240 \
            use_sbd:=true opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
            opgsl.event_driven.enabled:=true \
            opgsl.event_driven.eta_fixed:=-1.0 \
            2>&1 | tail -1 | tee -a /tmp/eta_ablation_raw.log || echo "TIMEOUT/ERROR"
        
        DIST=$(grep -oP 'MAP distance.*?(\d+\.\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+\.\d+' | tail -1)
        STEPS=$(grep -oP 'Total steps.*?(\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+' | tail -1)
        ELAPSED=$(grep -oP 'Elapsed time.*?(\d+\.\d+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\d+\.\d+' | tail -1)
        STATUS=$(grep -oP 'converge_type.*?(\w+)' /tmp/eta_ablation_raw.log 2>/dev/null | grep -oP '\w+$' | tail -1)
        
        echo "Adaptive,$HOUSE,$SEED,adaptive,${DIST:-NaN},${STEPS:-0},${ELAPSED:-0},${STATUS:-unknown}" >> "$RESULTS"
    done
done

echo "=== ETA ABLATION COMPLETE ==="
echo "Results: $RESULTS"
wc -l "$RESULTS"
cat "$RESULTS"
