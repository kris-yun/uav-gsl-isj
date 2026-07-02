#!/bin/bash
DIR="/tmp/cp_sbd_exp"
mkdir -p "$DIR"
echo "method,house,seed,map_dist,steps,elapsed,converge_type" > "$DIR/extended_ablation.csv"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    sleep 2
}

run_exp() {
    local METHOD=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8 DDM=$9 WRAIG=${10} CP=${11}
    local LOG="$DIR/ext_${METHOD}_${H}_s${S}.log"
    echo "=== $(date +%T) $METHOD $H seed=$S ==="
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=true \
        opgsl_ddm:=$DDM opgsl_wraig:=$WRAIG opgsl_cp:=$CP \
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
    local LAST=$(grep "OPGSL-AI step=" "$LOG" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | sed "s/.*step=\([0-9]*\).*/\1/")
        local EX=$(echo "$LAST" | sed "s/.*(\([-0-9.]*\),.*/\1/")
        local EY=$(echo "$LAST" | sed "s/.*,\([-0-9.]*\),[-0-9.]*)/\1/")
        DIST=$(python3 -c "print('%.3f'%((($EX-$SX)**2+($EY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "DDM-STOP" "$LOG"; then CTYPE="ddm_stop"
    elif grep -q "CP-STOP" "$LOG"; then CTYPE="cp_stop"
    elif grep -q "CONVERGED" "$LOG"; then CTYPE="converged"
    elif grep -q "HARD TIMEOUT" "$LOG"; then CTYPE="timeout"
    else CTYPE="other"; fi
    echo "$METHOD,$H,$S,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$DIR/extended_ablation.csv"
    sleep 2
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2"
HOUSES="House01 House02 House03"

# NoCP: DDM+W-RAIG, no CP
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "NoCP" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S" true true false
done; done

# DDM-only: only DDM
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "DDMonLy" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S" true false false
done; done

# WRAIG-only: only W-RAIG
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "WRAIGonly" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S" false true false
done; done

# CP-only: only CP
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_exp "CPonly" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S" false false true
done; done

echo "=== EXTENDED ABLATION COMPLETE ==="
cat "$DIR/extended_ablation.csv"