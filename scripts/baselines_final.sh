#!/bin/bash
DIR="/tmp/cp_sbd_exp"
mkdir -p "$DIR"
echo "method,house,seed,dist,steps,elapsed,status" > "$DIR/baselines_final.csv"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

run_bl() {
    local ALG=$1 H=$2 D=$3 CFG=$4 SX=$5 SY=$6 SZ=$7 S=$8
    local LOG="$DIR/final_${ALG}_${H}_s${S}.log"
    echo "=== $(date +%T) $ALG $H seed=$S ==="
    cleanup
    local T0=$(date +%s)
    # Use official PMFS launch file (not ablation launch)
    ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=$ALG \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 flight_height:=0.3 \
        run_dir:="/tmp/gsl_runs/${ALG}_${H}_s${S}" \
        > "$LOG" 2>&1 &
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
    # Parse result
    local DIST="N/A" STEPS="N/A" STATUS="other"
    if grep -q "Found the emission source" "$LOG"; then STATUS="found"; fi
    if grep -q "Could not find" "$LOG"; then STATUS="not_found"; fi
    # Get last goal position
    local LAST_GOAL=$(grep "Sending goal" "$LOG" | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
    if [ -n "$LAST_GOAL" ]; then
        local GX=$(echo "$LAST_GOAL" | sed 's/.*(\([-0-9.]*\),.*/\1/')
        local GY=$(echo "$LAST_GOAL" | sed 's/.*,\s*\([-0-9.]*\))/\1/')
        DIST=$(python3 -c "print('%.3f'%((($GX-$SX)**2+($GY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    echo "$ALG,$H,$S,$DIST,$STEPS,$ELAPSED,$STATUS" | tee -a "$DIR/baselines_final.csv"
    sleep 2
}

declare -A HCFG
HCFG[House01]="/home/zyc/vgr_data_scenarios/House01:2,4-1_fast:-0.40:-2.90:-0.30"
HCFG[House02]="/home/zyc/vgr_data_scenarios/House02:3,5-1_fast:0.0:-1.0:0.2"
HCFG[House03]="/home/zyc/vgr_data_scenarios/House03:1-2,5_fast:-0.45:1.9:-0.1"

SEEDS="0 1 2"
HOUSES="House01 House02 House03"

# Run PMFS
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_bl "PMFS" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

# Run GrGSL
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_bl "GrGSL" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

# Run SensorAwareSurgeCastPF
for S in $SEEDS; do for H in $HOUSES; do
    IFS=: read D CFG SX SY SZ <<< "${HCFG[$H]}"
    run_bl "SensorAwareSurgeCastPF" "$H" "$D" "$CFG" "$SX" "$SY" "$SZ" "$S"
done; done

echo "=== BASELINES COMPLETE ==="
cat "$DIR/baselines_final.csv"