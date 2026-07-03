#!/bin/bash
# CP-SBD-GSL validation - serial runs with proper cleanup
DIR="/tmp/cp_sbd_quick"
mkdir -p "$DIR"
RESULTS="$DIR/summary.csv"
echo "house,seed,map_dist,steps,elapsed,converge_type" > "$RESULTS"

SEEDS="0 1 2"
TIMEOUT=300

cd /home/zyc/gsl_ws
source install/setup.bash

run_one() {
    local HNAME=$1 DPATH=$2 SX=$3 SY=$4 SZ=$5 SEED=$6
    local LOG="$DIR/${HNAME}_s${SEED}.log"
    echo "=== Running $HNAME seed=$SEED ==="

    # Kill old
    pkill -9 -f gsl_actionserver 2>/dev/null; pkill -9 -f vgr_sim_node 2>/dev/null; pkill -9 -f gsl_benchmark 2>/dev/null
    sleep 3

    local T0=$(date +%s)

    # Launch foreground with timeout
    timeout $((TIMEOUT + 60)) ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$DPATH config_id:=2,4-1_fast algorithm:=OPGSL \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 seed:=$SEED \
        timeout_sec:=$TIMEOUT use_sbd:=true \
        resultsFile:=/tmp/gsl_result.csv > "$LOG" 2>&1

    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))

    # Kill leftovers
    pkill -9 -f gsl_actionserver 2>/dev/null; pkill -9 -f vgr_sim_node 2>/dev/null
    sleep 2

    # Extract result
    local DIST="N/A" STEPS="N/A" CTYPE="N/A"

    local LAST_STEP=$(grep 'OPGSL-AI step=' "$LOG" | tail -1)
    if [ -n "$LAST_STEP" ]; then
        STEPS=$(echo "$LAST_STEP" | sed 's/.*step=\([0-9]*\).*/\1/')
        local POS=$(echo "$LAST_STEP" | sed 's/.*(\([-0-9.]*\),\([-0-9.]*\),.*/\1 \2/')
        local EX=$(echo "$POS" | awk '{print $1}')
        local EY=$(echo "$POS" | awk '{print $2}')
        DIST=$(python3 -c "d=(($EX-$SX)**2+($EY-$SY)**2)**0.5; print('%.3f'%d)" 2>/dev/null)
    fi

    if grep -q 'Found the emission source' "$LOG"; then
        CTYPE="found"
    elif [ $ELAPSED -ge $TIMEOUT ]; then
        CTYPE="timeout"
    elif grep -q 'DONE, CLOSING' "$LOG"; then
        CTYPE="closed"
    else
        CTYPE="died"
    fi

    echo "$HNAME,$SEED,$DIST,$STEPS,$ELAPSED,$CTYPE" | tee -a "$RESULTS"
}

# Run all: 3 houses x 3 seeds
for SEED in $SEEDS; do run_one "House01" "/home/zyc/vgr_data_scenarios/House01" "-0.40" "-2.90" "-0.30" $SEED; done
for SEED in $SEEDS; do run_one "House02" "/home/zyc/vgr_data_scenarios/House02" "0.0" "-1.0" "0.2" $SEED; done
for SEED in $SEEDS; do run_one "House03" "/home/zyc/vgr_data_scenarios/House03" "-0.45" "1.9" "-0.1" $SEED; done

echo ""
echo "=== SUMMARY ==="
cat "$RESULTS"
echo ""
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
