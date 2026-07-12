#!/bin/bash
# WA-GBI Verification Test
# Run 3 seeds on House01 with new sigmoid-based eta
# Expected: similar or better performance than old linear eta

source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTDIR="/tmp/cp_sbd_exp/wagbi_verify"
mkdir -p "$OUTDIR"
LOG="$OUTDIR/verify_run.log"

echo "=== WA-GBI Verification Test ===" | tee "$LOG"
echo "Date: $(date)" | tee -a "$LOG"
echo "Code version: WA-GBI sigmoid eta" | tee -a "$LOG"
echo "" | tee -a "$LOG"

for seed in 0 1 2; do
    echo "--- House01 seed=$seed ---" | tee -a "$LOG"
    AUDIT="$OUTDIR/h01_s${seed}.csv"
    
    timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
        environment:=House01 \
        method:=M7_full_saisc_pf \
        seed:=$seed \
        audit_file:="$AUDIT" 2>&1 | grep -E 'RESULT|EP-STOP|eta|sigmoid|WA-GBI' | tee -a "$LOG"
    
    echo "" | tee -a "$LOG"
    sleep 5
done

echo "=== Verification Complete ===" | tee -a "$LOG"
echo "Results in: $OUTDIR" | tee -a "$LOG"
