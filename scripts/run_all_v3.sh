#!/bin/bash
# CP-SBD-GSL validation - NO daemon kill, targeted cleanup only
DIR="/tmp/cp_sbd_quick"
mkdir -p "$DIR"
RESULTS="$DIR/summary.csv"
echo "house,seed,map_dist,steps,elapsed,converge_type" > "$RESULTS"

SEEDS="0 1 2"
TIMEOUT=300

# Reset daemon once
ros2 daemon stop 2>/dev/null
sleep 1
ros2 daemon start 2>/dev/null
sleep 2

cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    # Kill ONLY the node processes, NOT the daemon
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 3
}

run_one() {
    local HNAME=$1 DPATH=$2 SX=$3 SY=$4 SZ=$5 SEED=$6
    local LOG="$DIR/${HNAME}_s${SEED}.log"
    echo "=== $(date +%H:%M:%S) Running $HNAME seed=$SEED ==="

    cleanup

    local T0=$(date +%s)

    # Launch in background, wait for gsl_actionserver to exit
    timeout $((TIMEOUT + 120)) ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$DPATH config_id:=2,4-1_fast algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$SEED \
        timeout_sec:=$TIMEOUT use_sbd:=true \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1 &
    local LAUNCH_PID=$!

    # Wait for gsl_actionserver to appear and then exit
    local WAITED=0
    local GSL_PID=""
    while [ $WAITED -lt $((TIMEOUT + 60)) ]; do
        # Check if launch process still alive
        if ! kill -0 $LAUNCH_PID 2>/dev/null; then
            break
        fi
        # Check if gsl_actionserver appeared
        if [ -z "$GSL_PID" ]; then
            GSL_PID=$(pgrep -f gsl_actionserver_node 2>/dev/null | head -1)
        fi
        # If gsl_actionserver appeared and then died, we're done
        if [ -n "$GSL_PID" ] && ! kill -0 $GSL_PID 2>/dev/null; then
            sleep 5  # Let launch file clean up
            break
        fi
        sleep 5
        WAITED=$((WAITED + 5))
    done

    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))

    # Kill leftovers
    cleanup

    # Extract result
    local DIST="N/A" STEPS="N/A" CTYPE="N/A"

    local LAST_STEP=$(grep 'OPGSL-AI step=' "$LOG" 2>/dev/null | tail -1)
    if [ -n "$LAST_STEP" ]; then
        STEPS=$(echo "$LAST_STEP" | sed 's/.*step=\([0-9]*\).*/\1/')
        local EX=$(echo "$LAST_STEP" | grep -oP '\([\-\d.]+,\K[\-\d.]+')
        local EY=$(echo "$LAST_STEP" | grep -oP '\([\-\d.]+,[\-\d.]+,\K[\-\d.]+')
        DIST=$(python3 -c "d=(($EX-$SX)**2+($EY-$SY)**2)**0.5; print('%.3f'%d)" 2>/dev/null)
    fi

    if grep -q 'Found the emission source' "$LOG" 2>/dev/null; then
        CTYPE="found"
    elif [ $ELAPSED -ge $TIMEOUT ]; then
        CTYPE="timeout"
    elif grep -q 'DONE, CLOSING' "$LOG" 2>/dev/null; then
        CTYPE="closed"
    else
        CTYPE="died"
    fi

    echo "$HNAME,$SEED,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$RESULTS"
}

# Run all
for SEED in $SEEDS; do run_one "House01" "/home/zyc/vgr_data_scenarios/House01" "-0.40" "-2.90" "-0.30" $SEED; done
for SEED in $SEEDS; do run_one "House02" "/home/zyc/vgr_data_scenarios/House02" "0.0" "-1.0" "0.2" $SEED; done
for SEED in $SEEDS; do run_one "House03" "/home/zyc/vgr_data_scenarios/House03" "-0.45" "1.9" "-0.1" $SEED; done

echo ""
echo "=== SUMMARY ==="
cat "$RESULTS"