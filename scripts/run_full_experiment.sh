#!/bin/bash
# Run PMFS baseline (no WRANF) x 10 seeds, then WRANF x 10 seeds
RESULTS_DIR="/tmp/gsl_clean_results"
VGR_DATA="/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01"
CONFIG="2,4-1_fast"
SRC_X="-0.40"
SRC_Y="-2.90"
SRC_Z="-0.30"
START_X="-5.0"
START_Y="-5.0"
TIMEOUT=120

run_one() {
    local LAUNCH=$1 METHOD=$2 SEED=$3
    pkill -9 -f ros2 2>/dev/null; pkill -9 -f gsl_ 2>/dev/null
    rm -rf /dev/shm/fastrtps_*; sleep 2

    local CSV="$RESULTS_DIR/House01_${METHOD}_s${SEED}.csv"
    local SRV="$RESULTS_DIR/House01_${METHOD}_s${SEED}_server.csv"

    source /opt/ros/humble/setup.bash
    source ~/ros2_ws/install/setup.bash

    timeout $TIMEOUT ros2 launch vgr_bridge $LAUNCH \
        vgr_data_path:=$VGR_DATA config_id:=$CONFIG \
        source_x:=$SRC_X source_y:=$SRC_Y source_z:=$SRC_Z \
        start_x:=$START_X start_y:=$START_Y seed:=$SEED \
        output_csv:=$CSV server_results_file:=$SRV dataset:=VGR_House01 \
        > "$RESULTS_DIR/log_${METHOD}_s${SEED}.txt" 2>&1

    if [ -f "$CSV" ]; then
        local DIST=$(python3 -c "import csv; r=list(csv.DictReader(open('$CSV')))[0]; print(r['min_distance_to_source'])")
        echo "$METHOD s$SEED: min_dist=$DIST"
    else
        echo "$METHOD s$SEED: FAILED (no CSV)"
    fi
}

echo "=== Phase 1: PMFS Baseline (no WRANF) x 10 seeds ==="
for s in $(seq 0 9); do
    run_one "vgr_gsl_ablation_noWRANF.launch.py" "PMFS_baseline" $s
done

echo ""
echo "=== Phase 2: WRANF (SENPAI+GRACE+ESSA) x 10 seeds ==="
for s in $(seq 0 9); do
    run_one "vgr_gsl_wranf.launch.py" "WRANF" $s
done

echo ""
echo "=== Summary ==="
echo "PMFS Baseline:"
for s in $(seq 0 9); do
    f="$RESULTS_DIR/House01_PMFS_baseline_s${s}.csv"
    if [ -f "$f" ]; then
        python3 -c "import csv; r=list(csv.DictReader(open('$f')))[0]; print(f'  s$s: {float(r[\"min_distance_to_source\"]):.3f}m')"
    fi
done

echo "WRANF:"
for s in $(seq 0 9); do
    f="$RESULTS_DIR/House01_WRANF_s${s}.csv"
    if [ -f "$f" ]; then
        python3 -c "import csv; r=list(csv.DictReader(open('$f')))[0]; print(f'  s$s: {float(r[\"min_distance_to_source\"]):.3f}m')"
    fi
done
