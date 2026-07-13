#!/bin/bash
# Unified experiment script v4 - Fixed: overflow, determinism, parsing
DIR="/tmp/cp_sbd_exp_final"
mkdir -p "$DIR"
CSV="$DIR/all_results.csv"
echo "method,house,seed,dist,steps,elapsed,converge_type" > "$CSV"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    pkill -9 -f "ros2 launch" 2>/dev/null
    sleep 2
}

run_ours() {
    local H=$1 D=$2 CFG=$3 SX=$4 SY=$5 SZ=$6 S=$7
    local LOG="$DIR/Ours_${H}_s${S}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=false \
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true \
        resultsFile:=$DIR/res_Ours_${H}_s${S}.csv > "$LOG" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [ $WAIT -lt 360 ]; do
        sleep 5
        WAIT=$((WAIT + 5))
        if grep -q "OPGSL-SDNBV RESULT" "$LOG" 2>/dev/null; then sleep 3; break; fi
        if grep -q "DONE, CLOSING" "$LOG" 2>/dev/null; then sleep 2; break; fi
        if ! kill -0 $LPID 2>/dev/null; then break; fi
    done
    local T1=$(date +%s)
    cleanup

    local DIST="" STEPS="" CTYPE="other"
    local RESULT=$(grep "OPGSL-SDNBV RESULT" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$RESULT" ]; then
        STEPS=$(echo "$RESULT" | sed 's/.*steps=\([0-9]*\).*/\1/')
        local RAW=$(echo "$RESULT" | grep -o 'posterior_MAP=([-0-9.e, ]*)' | sed 's/posterior_MAP=(//' | sed 's/)//')
        local MX=$(echo "$RAW" | cut -d',' -f1)
        local MY=$(echo "$RAW" | cut -d',' -f2)
        DIST=$(python3 -c "print('%.3f'%((($MX-$SX)**2+($MY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "EP-STOP" "$LOG"; then CTYPE="ep_stop"
    elif grep -q "CP-STOP" "$LOG"; then CTYPE="cp_stop"
    fi
    echo "Ours,$H,$S,$DIST,$STEPS,$((T1-T0)),$CTYPE" | tee -a "$CSV"
    sleep 1
}

run_baseline() {
    local ALG=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8
    local LOG="$DIR/${ALG}_${H}_s${S}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=$ALG \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        output_csv:=$DIR/res_${ALG}_${H}_s${S}.csv > "$LOG" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [ $WAIT -lt 360 ]; do
        sleep 5
        WAIT=$((WAIT + 5))
        if grep -q "DONE, CLOSING" "$LOG" 2>/dev/null; then sleep 2; break; fi
        if ! kill -0 $LPID 2>/dev/null; then break; fi
    done
    local T1=$(date +%s)
    cleanup

    local DIST="" CTYPE="other"
    local RES=$(grep "final_error=" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$RES" ]; then
        DIST=$(echo "$RES" | sed 's/.*final_error=\([-0-9.]*\).*/\1/')
    fi
    if grep -q "Found the emission source\|termination=success" "$LOG"; then CTYPE="found"
    elif grep -q "timed out\|timeout" "$LOG"; then CTYPE="timeout"
    fi
    echo "$ALG,$H,$S,$DIST,,$((T1-T0)),$CTYPE" | tee -a "$CSV"
    sleep 1
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2 3 4 5 6 7 8 9"
HOUSES="House01 House02 House03"

echo "=== FINAL EXPERIMENT $(date) ==="
echo "Fixes: overflow safety, seed jitter, EP-STOP parsing"

# Our method: 10 seeds x 3 houses = 30 runs
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_ours "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

# Baselines: 3 seeds x 3 houses x 3 methods = 27 runs
for ALG in SensorAwareSurgeCastPF GrGSL PMFS; do
    for S in 0 1 2; do for H in $HOUSES; do
        IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
        run_baseline "$ALG" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
    done; done
done

echo "=== DONE $(date) ==="
echo "Total runs: 57 (30 ours + 27 baselines)"
