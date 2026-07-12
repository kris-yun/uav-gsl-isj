#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
cd /home/zyc/gsl_ws

DIR=/tmp/cp_sbd_exp/final_v3
RESULTS="$DIR/results.csv"
HELPER=/tmp/extract_helper.py
mkdir -p "$DIR"

if [ ! -f "$RESULTS" ]; then
    echo "method,house,seed,dist,steps,elapsed,converge_type,eproc_value,eta_final" > "$RESULTS"
fi

HOUSES=(House01 House02 House03)
CONFIGS=(2,4-1_fast 3,5-1_fast 1-2,5_fast)
SOURCES_X=(-0.40 0.00 -0.45)
SOURCES_Y=(-2.90 -1.00 1.90)
SOURCES_Z=(-0.30 0.20 -0.10)
STARTS_X=(0.30 -0.50 2.00)
STARTS_Y=(-1.20 -2.50 0.00)

cleanup() {
    killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null || true
    sleep 3
}

run_one() {
    local LABEL=$1 H=$2 CFG=$3 SX=$4 SY=$5 SZ=$6 STX=$7 STY=$8 SEED=$9
    local TAG="${LABEL},${H},${SEED},"
    if grep -q "$TAG" "$RESULTS" 2>/dev/null; then
        echo "[SKIP] $TAG already done"
        return 0
    fi
    cleanup
    local LOG="$DIR/${LABEL}_${H}_s${SEED}.log"
    local T0=$(date +%s)
    timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$H \
        config_id:=$CFG algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED \
        timeout_sec:=300 use_sbd:=true \
        opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
        opgsl.event_driven.enabled:=true \
        opgsl.event_driven.eta_fixed:=-1.0 \
        > "$LOG" 2>&1 || true
    local T1=$(date +%s)
    local ELAPSED=$(( T1 - T0 ))
    sleep 2
    local RESULT=$(python3 "$HELPER" "$LOG" "$SX" "$SY")
    local DIST=$(echo "$RESULT" | cut -d"|" -f1)
    local STEPS=$(echo "$RESULT" | cut -d"|" -f2)
    local CTYPE=$(echo "$RESULT" | cut -d"|" -f3)
    local ETA=$(grep "ETA:" "$LOG" | tail -1 | grep -oP "eta=[\d.]+" | cut -d= -f2)
    local EPROC=$(grep "EP-STOP" "$LOG" | head -1 | grep -oP "eproc=[\d.]+" | cut -d= -f2)
    local EDEFER=$(grep -c "EP-DEFERRED" "$LOG" || echo "0")
    [ -z "$ETA" ] && ETA="N/A"
    [ -z "$EPROC" ] && EPROC="N/A"
    echo "${LABEL},${H},${SEED},${DIST},${STEPS},${ELAPSED},${CTYPE},${EPROC},${ETA}" >> "$RESULTS"
    echo "  -> dist=${DIST} steps=${STEPS} type=${CTYPE} eta=${ETA} eproc=${EPROC} deferred=${EDEFER} time=${ELAPSED}s"
    cleanup
}

echo "=== Final Experiment v3 (adaptive params, eta_power=1.0) ==="
date

RUN_COUNT=0
for h_idx in 0 1 2; do
    H=${HOUSES[$h_idx]}
    for SEED in 0 1 2 3 4; do
        echo "[$H] seed=$SEED"
        date
        run_one "Ours" "$H" "${CONFIGS[$h_idx]}" "${SOURCES_X[$h_idx]}" "${SOURCES_Y[$h_idx]}" "${SOURCES_Z[$h_idx]}" "${STARTS_X[$h_idx]}" "${STARTS_Y[$h_idx]}" "$SEED"
        RUN_COUNT=$((RUN_COUNT + 1))
        # Checkpoint: print summary every 5 runs
        if [ $((RUN_COUNT % 5)) -eq 0 ]; then
            echo "--- CHECKPOINT after $RUN_COUNT runs ---"
            tail -6 "$RESULTS"
            echo "---"
        fi
    done
}

echo "=== COMPLETE ==="
date
cat "$RESULTS"
