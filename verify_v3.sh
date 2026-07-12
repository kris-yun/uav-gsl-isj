#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
cd /home/zyc/gsl_ws

DIR=/tmp/cp_sbd_exp/verify_v3
mkdir -p "$DIR"
HELPER=/tmp/extract_helper.py

echo "=== Quick Verify: 3 seeds on House01 ==="
date

for SEED in 0 1 2; do
    echo "[House01] seed=$SEED"
    killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null || true
    sleep 2
    LOG="$DIR/House01_s${SEED}.log"
    T0=$(date +%s)
    timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
        config_id:=2,4-1_fast algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
        start_x:=0.30 start_y:=-1.20 seed:=$SEED \
        timeout_sec:=300 use_sbd:=true \
        opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
        opgsl.event_driven.enabled:=true \
        opgsl.event_driven.eta_fixed:=-1.0 \
        > "$LOG" 2>&1 || true
    T1=$(date +%s)
    ELAPSED=$(( T1 - T0 ))
    
    RESULT=$(python3 "$HELPER" "$LOG" -0.40 -2.90)
    DIST=$(echo "$RESULT" | cut -d"|" -f1)
    STEPS=$(echo "$RESULT" | cut -d"|" -f2)
    CTYPE=$(echo "$RESULT" | cut -d"|" -f3)
    
    ETA_LINE=$(grep "ETA:" "$LOG" | tail -1)
    ETA=$(echo "$ETA_LINE" | grep -oP "eta=[\d.]+" | cut -d= -f2)
    EPSTOP=$(grep "EP-STOP" "$LOG" | head -1 | grep -oP "eproc=[\d.]+" | cut -d= -f2)
    EDEFER=$(grep -c "EP-DEFERRED" "$LOG" || echo "0")
    
    echo "  -> dist=$DIST steps=$STEPS type=$CTYPE eta=$ETA eproc=$EPSTOP deferred=$EDEFER time=${ELAPSED}s"
done

echo "=== DONE ==="
date
