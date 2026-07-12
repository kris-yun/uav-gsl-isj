#!/bin/bash
DIR="/tmp/cp_sbd_exp/eta_ablation"
mkdir -p "$DIR"
RESULTS="$DIR/results.csv"
echo "method,house,seed,eta,dist,steps,elapsed,converge_type" > "$RESULTS"
cd /home/zyc/gsl_ws
source install/setup.bash

run_one() {
    local LABEL=$1 H=$2 CFG=$3 SX=$4 SY=$5 SZ=$6 STX=$7 STY=$8 SEED=$9 ETA=${10}
    local LOG="$DIR/${LABEL}_${H}_s${SEED}.log"
    
    local T0=$(date +%s)
    timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$H \
        config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED \
        timeout_sec:=240 use_sbd:=true \
        opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
        opgsl.event_driven.enabled:=true \
        opgsl.event_driven.eta_fixed:=$ETA \
        > "$LOG" 2>&1
    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))
    
    sleep 2
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
    fi
    echo "${LABEL},${H},${SEED},${ETA},${DIST:-NaN},${STEPS:-0},${ELAPSED},${CTYPE}" >> "$RESULTS"
    echo "  -> dist=${DIST:-NaN} steps=${STEPS:-0} type=${CTYPE} time=${ELAPSED}s"
}

HOUSES=("House01" "House02" "House03")
CONFIGS=("2,4-1_fast" "3,5-1_fast" "1-2,5_fast")
SOURCES_X=("-0.40" "0.00" "-0.45")
SOURCES_Y=("-2.90" "-1.00" "1.90")
SOURCES_Z=("-0.30" "0.20" "-0.10")
STARTS_X=("0.30" "-0.50" "2.00")
STARTS_Y=("-1.20" "-2.50" "0.00")

echo "=== Fixed eta ablation (0.5, 0.7, 1.0) ==="
for h_idx in 0 1 2; do
    H=${HOUSES[$h_idx]}
    for ETA in 0.5 0.7 1.0; do
        for SEED in 0 1 2 3 4; do
            echo "[$H] eta=$ETA seed=$SEED"
            run_one "FixedEta_${ETA}" "$H" "${CONFIGS[$h_idx]}" "${SOURCES_X[$h_idx]}" "${SOURCES_Y[$h_idx]}" "${SOURCES_Z[$h_idx]}" "${STARTS_X[$h_idx]}" "${STARTS_Y[$h_idx]}" "$SEED" "$ETA"
        done
    done
done

echo "=== Adaptive eta ==="
for h_idx in 0 1 2; do
    H=${HOUSES[$h_idx]}
    for SEED in 0 1 2 3 4; do
        echo "[$H] adaptive seed=$SEED"
        run_one "Adaptive" "$H" "${CONFIGS[$h_idx]}" "${SOURCES_X[$h_idx]}" "${SOURCES_Y[$h_idx]}" "${SOURCES_Z[$h_idx]}" "${STARTS_X[$h_idx]}" "${STARTS_Y[$h_idx]}" "$SEED" "-1.0"
    done
done

echo "=== COMPLETE ==="
cat "$RESULTS"