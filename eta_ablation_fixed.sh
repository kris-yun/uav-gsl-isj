#!/bin/bash
# eta_ablation.sh - Fixed version with proper result extraction
DIR="/tmp/cp_sbd_exp/eta_ablation"
mkdir -p "$DIR"
RESULTS="$DIR/results.csv"
echo "method,house,seed,eta,dist,steps,elapsed,converge_type" > "$RESULTS"

cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

run_eta_exp() {
    local LABEL=$1 H=$2 CFG=$3 SX=$4 SY=$5 SZ=$6 STX=$7 STY=$8 SEED=$9 ETA=${10}
    local LOG="$DIR/${LABEL}_${H}_s${SEED}.log"
    cleanup
    
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$H \
        config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED \
        timeout_sec:=240 use_sbd:=true \
        opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
        opgsl.event_driven.enabled:=true \
        opgsl.event_driven.eta_fixed:=$ETA \
        > "$LOG" 2>&1 &
    local LPID=$!
    
    local WAIT=0
    while [ $WAIT -lt 300 ]; do
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
    elif grep -q "DDM-STOP" "$LOG"; then CTYPE="ddm_stop"
    elif grep -q "CONVERGED" "$LOG"; then CTYPE="converged"
    fi
    
    echo "${LABEL},${H},${SEED},${ETA},${DIST:-NaN},${STEPS:-0},${ELAPSED},${CTYPE}" >> "$RESULTS"
    echo "  -> dist=${DIST:-NaN} steps=${STEPS:-0} type=${CTYPE}"
}

# Houses and configs
HOUSES=("House01" "House02" "House03")
CONFIGS=("2,4-1_fast" "3,5-1_fast" "1-2,5_fast")
SOURCES_X=("-0.40" "0.00" "-0.45")
SOURCES_Y=("-2.90" "-1.00" "1.90")
SOURCES_Z=("-0.30" "0.20" "-0.10")
STARTS_X=("0.30" "-0.50" "2.00")
STARTS_Y=("-1.20" "-2.50" "0.00")

# Fixed eta values
ETA_VALUES=("0.3" "0.5" "0.7" "1.0")
SEEDS=$(seq 0 4)

echo "=== Starting eta ablation ==="
for h_idx in 0 1 2; do
    H=${HOUSES[$h_idx]}
    CFG=${CONFIGS[$h_idx]}
    SX=${SOURCES_X[$h_idx]}
    SY=${SOURCES_Y[$h_idx]}
    SZ=${SOURCES_Z[$h_idx]}
    STX=${STARTS_X[$h_idx]}
    STY=${STARTS_Y[$h_idx]}
    
    for ETA in "${ETA_VALUES[@]}"; do
        for SEED in $SEEDS; do
            echo "[$H] eta=$ETA seed=$SEED"
            run_eta_exp "FixedEta_${ETA}" "$H" "$CFG" "$SX" "$SY" "$SZ" "$STX" "$STY" "$SEED" "$ETA"
        done
    done
done

# Adaptive eta (eta_fixed=-1)
for h_idx in 0 1 2; do
    H=${HOUSES[$h_idx]}
    CFG=${CONFIGS[$h_idx]}
    SX=${SOURCES_X[$h_idx]}
    SY=${SOURCES_Y[$h_idx]}
    SZ=${SOURCES_Z[$h_idx]}
    STX=${STARTS_X[$h_idx]}
    STY=${STARTS_Y[$h_idx]}
    
    for SEED in $SEEDS; do
        echo "[$H] adaptive seed=$SEED"
        run_eta_exp "Adaptive" "$H" "$CFG" "$SX" "$SY" "$SZ" "$STX" "$STY" "$SEED" "-1.0"
    done
done

echo "=== ETA ABLATION COMPLETE ==="
echo "Results: $RESULTS"
cat "$RESULTS"