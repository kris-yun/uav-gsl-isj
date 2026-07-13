#!/bin/bash
# Baseline comparison v2 - Parse final_error from log
DIR="/tmp/cp_sbd_exp_clean"
CSV="$DIR/baselines_clean.csv"
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

run_baseline() {
    local LABEL=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8 ALG=$9
    local LOG="$DIR/${LABEL}_${H}_s${S}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=$ALG \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        output_csv:=$DIR/results_${LABEL}_${H}_s${S}.csv > "$LOG" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [ $WAIT -lt 360 ]; do
        sleep 5
        WAIT=$((WAIT + 5))
        if grep -q "DONE, CLOSING" "$LOG" 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $LPID 2>/dev/null; then break; fi
    done
    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))
    cleanup

    local DIST="" CTYPE="other"
    # Parse final_error from benchmark runner log
    local RESULT=$(grep "final_error=" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$RESULT" ]; then
        DIST=$(echo "$RESULT" | sed 's/.*final_error=\([-0-9.]*\).*/\1/')
    fi
    # Also try the RESULT line from OPGSL
    if [ -z "$DIST" ]; then
        local OPRES=$(grep "OPGSL-SDNBV RESULT" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
        if [ -n "$OPRES" ]; then
            local RAW=$(echo "$OPRES" | grep -o 'posterior_MAP=([-0-9., ]*)' | sed 's/posterior_MAP=(//' | sed 's/)//')
            local MX=$(echo "$RAW" | cut -d',' -f1)
            local MY=$(echo "$RAW" | cut -d',' -f2)
            DIST=$(python3 -c "print('%.3f'%((($MX-$SX)**2+($MY-$SY)**2)**0.5))" 2>/dev/null)
        fi
    fi

    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "termination=success" "$LOG"; then CTYPE="found"
    elif grep -q "CP-STOP\|EP-STOP" "$LOG"; then CTYPE="cp_stop"
    elif grep -q "timed out\|timeout" "$LOG"; then CTYPE="timeout"
    else CTYPE="other"; fi

    echo "$LABEL,$H,$S,$DIST,,$ELAPSED,$CTYPE" | tee -a "$CSV"
    sleep 2
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2"
HOUSES="House01 House02 House03"
ALGORITHMS="SensorAwareSurgeCastPF GrGSL PMFS"

echo "=== BASELINE EXPERIMENT v2 $(date) ==="

for ALG in $ALGORITHMS; do
    for S in $SEEDS; do
        for H in $HOUSES; do
            IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
            run_baseline "$ALG" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S" "$ALG"
        done
    done
done

echo "=== DONE $(date) ==="
