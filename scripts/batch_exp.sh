#!/bin/bash
# CP-SBD-GSL batch experiment - clean serial runs
DIR="/tmp/cp_sbd_exp"
mkdir -p "$DIR"
echo "house,seed,map_dist,steps,elapsed,converge_type" > "$DIR/summary.csv"

cd /home/zyc/gsl_ws
source install/setup.bash

run_exp() {
    local H=$1 D=$2 SX=$3 SY=$4 SZ=$5 S=$6
    local LOG="$DIR/${H}_s${S}.log"
    echo "=== $(date +%T) $H seed=$S ==="

    # Clean only node processes
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 3

    local T0=$(date +%s%N)
    timeout 420 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=2,4-1_fast algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=true \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1
    local EXIT=$?
    local T1=$(date +%s%N)
    local ELAPSED=$(( (T1 - T0) / 1000000000 ))

    # Parse result
    local DIST="N/A" STEPS="N/A" CTYPE="N/A"
    local LAST=$(grep 'OPGSL-AI step=' "$LOG" | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | sed 's/.*step=\([0-9]*\).*/\1/')
        local EX=$(echo "$LAST" | sed 's/.*(\([-0-9.]*\),.*/\1/')
        local EY=$(echo "$LAST" | sed 's/.*,\([-0-9.]*\),[-0-9.]*)/\1/')
        DIST=$(python3 -c "print('%.3f'%((($EX-$SX)**2+($EY-$SY)**2)**0.5))" 2>/dev/null)
    fi

    if grep -q 'Found the emission source' "$LOG"; then CTYPE="found"
    elif grep -q 'DONE, CLOSING' "$LOG"; then CTYPE="closed"
    elif [ $EXIT -eq 124 ]; then CTYPE="timeout"
    else CTYPE="died"; fi

    echo "$H,$S,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$DIR/summary.csv"
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

# House01
for S in 0 1 2; do run_exp House01 /home/zyc/vgr_data_scenarios/House01 -0.40 -2.90 -0.30 $S; done
# House02
for S in 0 1 2; do run_exp House02 /home/zyc/vgr_data_scenarios/House02 0.0 -1.0 0.2 $S; done
# House03
for S in 0 1 2; do run_exp House03 /home/zyc/vgr_data_scenarios/House03 -0.45 1.9 -0.1 $S; done

echo ""
echo "=== FINAL SUMMARY ==="
cat "$DIR/summary.csv"