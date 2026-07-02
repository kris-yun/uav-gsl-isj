#!/bin/bash
DIR="/tmp/cp_sbd_exp"
mkdir -p "$DIR"
echo "method,house,seed,map_dist,steps,elapsed,converge_type" > "$DIR/baselines2.csv"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    sleep 2
}

run_baseline() {
    local ALG=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8
    local LOG="$DIR/bl2_${ALG}_${H}_s${S}.log"
    echo "=== $(date +%T) $ALG $H seed=$S ==="
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=$ALG \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=false \
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1 &
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
    local DIST="N/A" STEPS="N/A" CTYPE="N/A"
    # For OPGSL-based algorithms
    local LAST=$(grep "OPGSL-AI step=" "$LOG" 2>/dev/null | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | sed "s/.*step=\([0-9]*\).*/\1/")
        local EX=$(echo "$LAST" | sed "s/.*(\([-0-9.]*\),.*/\1/")
        local EY=$(echo "$LAST" | sed "s/.*,\([-0-9.]*\),[-0-9.]*)/\1/")
        DIST=$(python3 -c "print('%.3f'%((($EX-$SX)**2+($EY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    # For PMFS: check result file
    if [ "$DIST" = "N/A" ] && [ -f /tmp/gsl_result.csv ]; then
        local RESULT=$(tail -1 /tmp/gsl_result.csv 2>/dev/null)
        if [ -n "$RESULT" ]; then
            DIST="result_available"
        fi
    fi
    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "search complete" "$LOG"; then CTYPE="search_complete"
    elif grep -q "DONE, CLOSING" "$LOG"; then CTYPE="closed"
    elif [ $ELAPSED -ge 350 ]; then CTYPE="timeout"
    else CTYPE="died"; fi
    echo "$ALG,$H,$S,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$DIR/baselines2.csv"
    sleep 2
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2"
HOUSES="House01 House02 House03"

for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_baseline "PMFS" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_baseline "GrGSL" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_baseline "SensorAwareSurgeCastPF" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

echo "=== BASELINES COMPLETE ==="
cat "$DIR/baselines2.csv"