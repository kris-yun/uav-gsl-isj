#!/bin/bash
# Clean baseline experiment script - No DDM, No WRAIG, No SBD
DIR="/tmp/cp_sbd_exp_clean"
mkdir -p "$DIR"
CSV="$DIR/clean_baseline.csv"
echo "method,house,seed,dist,steps,elapsed,converge_type" > "$CSV"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    sleep 2
}

run_exp() {
    local LABEL=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8
    local LOG="$DIR/${LABEL}_${H}_s${S}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=false \
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true \
        resultsFile:=$DIR/results_${LABEL}_${H}_s${S}.csv > "$LOG" 2>&1 &
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
    local LAST=$(grep "OPGSL-AI step=" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | sed "s/.*step=\([0-9]*\).*/\1/")
        local EX=$(echo "$LAST" | sed "s/.*(\([-0-9.]*\),.*/\1/")
        local EY=$(echo "$LAST" | sed "s/.*,\([-0-9.]*\),[-0-9.]*)/\1/")
        DIST=$(python3 -c "print('%.3f'%((($EX-$SX)**2+($EY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "CP-STOP" "$LOG"; then CTYPE="cp_stop"
    elif grep -q "CONVERGED" "$LOG"; then CTYPE="converged"
    else CTYPE="other"; fi
    echo "$LABEL,$H,$S,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$CSV"
    sleep 2
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2 3 4 5 6 7 8 9"
HOUSES="House01 House02 House03"

echo "=== CLEAN BASELINE EXPERIMENT $(date) ==="
echo "Config: No DDM, No WRAIG, No SBD, CP=true"

# Our method (clean)
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "Clean" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

echo "=== DONE $(date) ==="
