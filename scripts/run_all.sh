#!/bin/bash
# CP-SBD-GSL validation runner
set -e

DIR="/tmp/cp_sbd_quick"
mkdir -p "$DIR"
RESULTS="$DIR/summary.csv"
echo "house,seed,map_dist,steps,elapsed,converge_type" > "$RESULTS"

HOUSES=("House01:House02:House03")
PATHS=("/home/zyc/vgr_data_scenarios/House01" "/home/zyc/vgr_data_scenarios/House02" "/home/zyc/vgr_data_scenarios/House03")
SXS=(-0.40 0.0 -0.45)
SYS=(-2.90 -1.0 1.9)
SZS=(-0.30 0.2 -0.1)
SEEDS=(0 1 2)
TIMEOUT=300

cd /home/zyc/gsl_ws
source install/setup.bash

run_one() {
    local IDX=$1 SEED=$2
    local HNAME=${HOUSES[$IDX]##*:}  # Not needed, just use idx
    local HNAME
    case $IDX in
        0) HNAME="House01";;
        1) HNAME="House02";;
        2) HNAME="House03";;
    esac
    local DPATH=${PATHS[$IDX]}
    local SX=${SXS[$IDX]}
    local SY=${SYS[$IDX]}
    local SZ=${SZS[$IDX]}
    local LOG="$DIR/${HNAME}_s${SEED}.log"

    echo "=== Running $HNAME seed=$SEED ==="

    # Kill old processes
    pkill -9 -f gsl_actionserver 2>/dev/null || true
    pkill -9 -f vgr_sim_node 2>/dev/null || true
    pkill -9 -f gsl_benchmark 2>/dev/null || true
    sleep 3

    local T0=$(date +%s)

    # Launch in background
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$DPATH \
        config_id:=2,4-1_fast algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$SEED \
        timeout_sec:=$TIMEOUT use_sbd:=true \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1 &
    local PID=$!

    # Wait for process to finish or timeout
    local ELAPSED=0
    while [ $ELAPSED -lt $((TIMEOUT + 60)) ]; do
        if ! kill -0 $PID 2>/dev/null; then
            break
        fi
        sleep 10
        ELAPSED=$(( $(date +%s) - T0 ))
    done

    # Kill if still running
    kill -9 $PID 2>/dev/null || true
    pkill -9 -f gsl_actionserver 2>/dev/null || true
    pkill -9 -f vgr_sim_node 2>/dev/null || true
    sleep 2

    local T1=$(date +%s)
    local TOTAL_ELAPSED=$((T1 - T0))

    # Extract results from log
    local DIST="N/A"
    local STEPS="N/A"
    local CTYPE="N/A"

    # Get last OPGSL-AI step position
    local LAST_STEP=$(grep 'OPGSL-AI step=' "$LOG" | tail -1)
    if [ -n "$LAST_STEP" ]; then
        STEPS=$(echo "$LAST_STEP" | grep -oP 'step=\K\d+')
        local EX=$(echo "$LAST_STEP" | grep -oP '\K-?[\d.]+' | head -2 | tail -1)
        local EY=$(echo "$LAST_STEP" | grep -oP '\K-?[\d.]+' | head -3 | tail -1)
        DIST=$(python3 -c "print('%.3f' % (($EX - $SX)**2 + ($EY - $SY)**2)**0.5)")
    fi

    if grep -q 'Found the emission source' "$LOG"; then
        CTYPE="found"
    elif grep -q 'DONE, CLOSING' "$LOG"; then
        CTYPE="closed"
    elif [ $TOTAL_ELAPSED -ge $TIMEOUT ]; then
        CTYPE="timeout"
    else
        CTYPE="died"
    fi

    echo "$HNAME,$SEED,$DIST,$STEPS,$TOTAL_ELAPSED,$CTYPE" | tee -a "$RESULTS"
}

# Run all
for IDX in 0 1 2; do
    for SEED in "${SEEDS[@]}"; do
        run_one $IDX $SEED
    done
done

echo ""
echo "=== SUMMARY ==="
python3 -c "
import csv
rows = list(csv.DictReader(open('$RESULTS')))
for h in ['House01','House02','House03']:
    ds = [float(r['map_dist']) for r in rows if r['house']==h and r['map_dist']!='N/A']
    if ds:
        print(f'{h}: n={len(ds)} median={sorted(ds)[len(ds)//2]:.2f}m mean={sum(ds)/len(ds):.2f}m')
    else:
        print(f'{h}: no valid results')
"
