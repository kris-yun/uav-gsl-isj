#!/bin/bash
# Standardized experiment script for ISJ paper
# All methods use SAME source positions for fair comparison
# Source positions from GADEN defaults (realistic scenario)

DIR="/tmp/cp_sbd_exp/isj_final"
mkdir -p "$DIR"
CSV="$DIR/results.csv"
echo "method,house,seed,dist,steps,elapsed,converge_type" > "$CSV"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

# Source positions (GADEN defaults - same for ALL methods)
declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2 3 4 5 6 7 8 9"
HOUSES="House01 House02 House03"

run_exp() {
    local LABEL=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8
    local LOG="$DIR/${LABEL}_${H}_s${S}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=true \
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true \
        resultsFile:=$DIR/${LABEL}_${H}_s${S}.csv > "$LOG" 2>&1 &
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
    local DIST="" STEPS="" CTYPE="other"
    local LAST=$(grep "RESULT:" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | grep -oP 'steps=\K\d+')
        local MAP=$(echo "$LAST" | grep -oP 'MAP=\(\K[^)]+')
        local MX=$(echo "$MAP" | cut -d, -f1)
        local MY=$(echo "$MAP" | cut -d, -f2)
        DIST=$(python3 -c "import math; print(math.sqrt(($MX-($SX))**2+($MY-($SY))**2))" 2>/dev/null)
    fi
    if grep -q "EP-STOP" "$LOG" 2>/dev/null; then CTYPE="ep_stop"; fi
    if grep -q "TIMEOUT" "$LOG" 2>/dev/null; then CTYPE="timeout"; fi
    echo "$LABEL,$H,$S,${DIST:-N/A},${STEPS:-N/A},$ELAPSED,$CTYPE" >> "$CSV"
    echo "  $LABEL $H seed=$S: dist=${DIST:-N/A} steps=${STEPS:-N/A} type=$CTYPE ${ELAPSED}s"
}

echo "=== ISJ Final Experiment $(date) ==="
echo "Source positions: H01=(-0.40,-2.90), H02=(0.0,-1.0), H03=(-0.45,1.9)"

for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "Ours" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

echo "=== ALL DONE $(date) ==="