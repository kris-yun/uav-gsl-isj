#!/bin/bash
# GBI-GSL Full Experiment Reproduction Script
# Usage: bash run_all_experiments.sh [output_dir]
# Default output: /tmp/gsl_reproduce

set -e
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTDIR="${1:-/tmp/gsl_reproduce}"
mkdir -p "$OUTDIR"

# Scenario configs: NAME|DATAPATH|CONFIG|SX|SY|SZ|STX|STY
SCENARIOS=(
    "H01_gnd|/home/zyc/vgr_data_scenarios/House01|2,4-1_fast|-0.40|-2.90|-0.30|0.30|-1.20"
    "H01_air|/home/zyc/vgr_data_scenarios/House01|1,3-2,4_fast|-0.60|1.95|0.40|-0.90|0.15"
    "H02_air|/home/zyc/vgr_data_scenarios/House02/House02|3,5-1_fast|0.00|-1.00|0.20|-0.50|-2.50"
    "H03_gnd|/home/zyc/vgr_data_scenarios/House03/House03|1-2,5_fast|-0.45|1.90|-0.10|2.00|0.00"
)

SEEDS="0 1 2 3 4 5 6 7 8 9"
RESULTS="$OUTDIR/results.csv"
echo "method,scenario,seed,error_m,localized,elapsed_s" > "$RESULTS"

for SC in "${SCENARIOS[@]}"; do
    IFS='|' read -r NAME DPATH CFG SX SY SZ STX STY <<< "$SC"
    
    for SEED in $SEEDS; do
        # --- Our method (GBI-GSL) ---
        RUN="$OUTDIR/OPGSL_${NAME}_s${SEED}"
        mkdir -p "$RUN"
        LOG="$OUTDIR/OPGSL_${NAME}_s${SEED}.log"
        echo "[$(date +%H:%M:%S)] OPGSL $NAME s=$SEED"
        timeout 420 ros2 launch vgr_bridge vgr_ablation.launch.py \
            vgr_data_path:="$DPATH" config_id:="$CFG" \
            algorithm:=OPGSL method:=M7_full_saisc_pf \
            opgsl.event_driven.enabled:=true \
            source_x:="$SX" source_y:="$SY" source_z:="$SZ" \
            start_x:="$STX" start_y:="$STY" \
            flight_height:=1.0 seed:="$SEED" timeout_sec:=300 \
            run_dir:="$RUN" > "$LOG" 2>&1 || true
        ERR=$(sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -oP 'Final distance.*:\s*\K[\d.]+' | tail -1)
        [ -z "$ERR" ] && ERR=$(sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -oP 'Error=\K[\d.]+' | tail -1)
        LOC=0; [ -n "$ERR" ] && (( $(echo "$ERR < 2.0" | bc -l) )) && LOC=1
        echo "OPGSL,$NAME,$SEED,${ERR:-NA},$LOC,300" >> "$RESULTS"
        
        # --- SurgeCast ---
        RUN="$OUTDIR/SurgeCast_${NAME}_s${SEED}"
        mkdir -p "$RUN"
        LOG="$OUTDIR/SurgeCast_${NAME}_s${SEED}.log"
        echo "[$(date +%H:%M:%S)] SurgeCast $NAME s=$SEED"
        timeout 420 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
            vgr_data_path:="$DPATH" config_id:="$CFG" \
            algorithm:=SensorAwareSurgeCastPF method:=B3_surge_cast_pf_official \
            source_x:="$SX" source_y:="$SY" source_z:="$SZ" \
            start_x:="$STX" start_y:="$STY" \
            flight_height:=1.0 seed:="$SEED" timeout_sec:=300 \
            run_dir:="$RUN" > "$LOG" 2>&1 || true
        ERR=$(sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -oP 'Final distance.*:\s*\K[\d.]+' | tail -1)
        LOC=0; [ -n "$ERR" ] && (( $(echo "$ERR < 2.0" | bc -l) )) && LOC=1
        echo "SurgeCast,$NAME,$SEED,${ERR:-NA},$LOC,300" >> "$RESULTS"
        
        # --- GrGSL ---
        RUN="$OUTDIR/GrGSL_${NAME}_s${SEED}"
        mkdir -p "$RUN"
        LOG="$OUTDIR/GrGSL_${NAME}_s${SEED}.log"
        echo "[$(date +%H:%M:%S)] GrGSL $NAME s=$SEED"
        timeout 420 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
            vgr_data_path:="$DPATH" config_id:="$CFG" \
            algorithm:=GrGSL method:=B5_GrGSL_official \
            source_x:="$SX" source_y:="$SY" source_z:="$SZ" \
            start_x:="$STX" start_y:="$STY" \
            flight_height:=1.0 seed:="$SEED" timeout_sec:=300 \
            run_dir:="$RUN" > "$LOG" 2>&1 || true
        ERR=$(sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -oP 'Final distance.*:\s*\K[\d.]+' | tail -1)
        LOC=0; [ -n "$ERR" ] && (( $(echo "$ERR < 2.0" | bc -l) )) && LOC=1
        echo "GrGSL,$NAME,$SEED,${ERR:-NA},$LOC,300" >> "$RESULTS"
        
        # --- PMFS (needs wind_value_server, already in launch file) ---
        RUN="$OUTDIR/PMFS_${NAME}_s${SEED}"
        mkdir -p "$RUN"
        LOG="$OUTDIR/PMFS_${NAME}_s${SEED}.log"
        echo "[$(date +%H:%M:%S)] PMFS $NAME s=$SEED"
        timeout 420 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
            vgr_data_path:="$DPATH" config_id:="$CFG" \
            algorithm:=PMFS method:=B4_PMFS_official \
            source_x:="$SX" source_y:="$SY" source_z:="$SZ" \
            start_x:="$STX" start_y:="$STY" \
            flight_height:=1.0 seed:="$SEED" timeout_sec:=300 \
            run_dir:="$RUN" > "$LOG" 2>&1 || true
        ERR=$(sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -oP 'Final distance.*:\s*\K[\d.]+' | tail -1)
        LOC=0; [ -n "$ERR" ] && (( $(echo "$ERR < 2.0" | bc -l) )) && LOC=1
        echo "PMFS,$NAME,$SEED,${ERR:-NA},$LOC,300" >> "$RESULTS"
    done
done

echo "=== ALL EXPERIMENTS COMPLETE ==="
echo "Results: $RESULTS"
cat "$RESULTS"