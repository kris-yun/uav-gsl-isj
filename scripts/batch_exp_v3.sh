#!/bin/bash
DIR="/tmp/cp_sbd_exp"
mkdir -p "$DIR"
echo "house,seed,map_dist,steps,elapsed,converge_type" > "$DIR/summary.csv"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    kill $(pgrep -f gsl_actionserver_node) 2>/dev/null
    kill $(pgrep -f vgr_sim_node) 2>/dev/null
    kill $(pgrep -f gsl_benchmark_runner) 2>/dev/null
    sleep 2
}

run_exp() {
    local H=$1 D=$2 CFG=$3 SX=$4 SY=$5 SZ=$6 S=$7
    local LOG="$DIR/${H}_s${S}.log"
    echo "=== $(date +%T) $H seed=$S config=$CFG ==="
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$D config_id:=$CFG algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$S \
        timeout_sec:=300 use_sbd:=true \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [ $WAIT -lt 360 ]; do
        sleep 5
        WAIT=$((WAIT + 5))
        if grep -q 'DONE, CLOSING' "$LOG" 2>/dev/null; then sleep 3; break; fi
        if grep -q 'search complete' "$LOG" 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $LPID 2>/dev/null; then break; fi
    done
    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))
    cleanup
    local DIST="N/A" STEPS="N/A" CTYPE="N/A"
    local LAST=$(grep 'OPGSL-AI step=' "$LOG" 2>/dev/null | tail -1)
    if [ -n "$LAST" ]; then
        STEPS=$(echo "$LAST" | sed 's/.*step=\([0-9]*\).*/\1/')
        local EX=$(echo "$LAST" | sed 's/.*(\([-0-9.]*\),.*/\1/')
        local EY=$(echo "$LAST" | sed 's/.*,\([-0-9.]*\),[-0-9.]*)/\1/')
        DIST=$(python3 -c "print('%.3f'%((($EX-$SX)**2+($EY-$SY)**2)**0.5))" 2>/dev/null)
    fi
    if grep -q 'Found the emission source' "$LOG"; then CTYPE="found"
    elif grep -q 'search complete' "$LOG"; then CTYPE="search_complete"
    elif grep -q 'DONE, CLOSING' "$LOG"; then CTYPE="closed"
    elif [ $ELAPSED -ge 350 ]; then CTYPE="timeout"
    else CTYPE="died"; fi
    echo "$H,$S,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$DIR/summary.csv"
    sleep 2
}

# House01: config 2,4-1_fast, source (-0.40, -2.90, -0.30)
for S in 0 1 2; do run_exp House01 /home/zyc/vgr_data_scenarios/House01 "2,4-1_fast" -0.40 -2.90 -0.30 $S; done
# House02: config 3,5-1_fast, source (0.00, -1.00, 0.20)
for S in 0 1 2; do run_exp House02 /home/zyc/vgr_data_scenarios/House02 "3,5-1_fast" 0.0 -1.0 0.2 $S; done
# House03: config 1-2,5_fast, source (-0.45, 1.90, -0.10)
for S in 0 1 2; do run_exp House03 /home/zyc/vgr_data_scenarios/House03 "1-2,5_fast" -0.45 1.9 -0.1 $S; done
echo "=== DONE ==="
cat "$DIR/summary.csv"