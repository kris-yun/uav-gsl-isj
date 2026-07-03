#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

DATA=/home/zyc/enva_vgr
OUT=/tmp/cp_sbd_exp
PMFS_CSV=$OUT/pmfs_results.csv
echo "method,scenario,seed,map_dist,steps,elapsed,converge_type" > $PMFS_CSV

CFG=A1_fast
SRC_X=5.0
SRC_Y=6.2
SCENARIO=PMFS_A1
START_X=1.0
START_Y=1.0

for METHOD in Full NoDDM NoWRAIG NoCP; do
    case $METHOD in
        Full)    DDM=true; WRAIG=true; CP=true ;;
        NoDDM)   DDM=false; WRAIG=true; CP=true ;;
        NoWRAIG) DDM=true; WRAIG=false; CP=true ;;
        NoCP)    DDM=true; WRAIG=true; CP=false ;;
    esac

    for SEED in 0 1 2 3 4 5 6 7 8 9; do
        if grep -q "$METHOD,$SCENARIO,$SEED," $PMFS_CSV 2>/dev/null; then
            continue
        fi

        LOG=$OUT/log_pmfs_${METHOD}_${SEED}.txt
        timeout 420 ros2 launch vgr_bridge vgr_ablation.launch.py \
            vgr_data_path:=$DATA \
            config_id:=$CFG \
            source_x:=$SRC_X \
            source_y:=$SRC_Y \
            source_z:=0.5 \
            start_x:=$START_X \
            start_y:=$START_Y \
            seed:=$SEED \
            timeout_sec:=300.0 \
            use_sbd:=false \
            opgsl_ddm:=$DDM \
            opgsl_wraig:=$WRAIG \
            opgsl_cp:=$CP \
            opgsl_wraig_beta:=0.5 \
            resultsFile:=$OUT/pmfs_run_${METHOD}_${SEED}.csv \
            2>&1 | tee $LOG

        RESULT_LINE=$(grep "OPGSL-SDNBV RESULT" "$LOG" | tail -1)
        MX=$(echo "$RESULT_LINE" | sed "s/.*posterior_MAP=(\([0-9.-]*\),.*/\1/")
        MY=$(echo "$RESULT_LINE" | sed "s/.*,[ ]*\([0-9.-]*\),.*/\1/")
        STEPS=$(echo "$RESULT_LINE" | sed "s/.*steps=\([0-9]*\).*/\1/")
        ELAPSED=$(echo "$RESULT_LINE" | sed "s/.*t=\([0-9.]*\)s.*/\1/")

        if grep -q "found\|CONVERGED\|FAST EXIT\|CP-STOP\|DDM-STOP\|search complete" "$LOG"; then
            CTYPE="found"
        elif grep -q "HARD TIMEOUT" "$LOG"; then
            CTYPE="timeout"
        else
            CTYPE="other"
        fi

        DIST=$(python3 -c "import math; d=math.sqrt(($MX-$SRC_X)**2+($MY-$SRC_Y)**2); print(round(d,2))" 2>/dev/null)
        echo "$METHOD,$SCENARIO,$SEED,$DIST,$STEPS,$ELAPSED,$CTYPE" >> $PMFS_CSV
        echo "Done: $METHOD seed=$SEED dist=$DIST steps=$STEPS"
        sleep 2
    done
done
echo "=== COMPLETE ==="
cat $PMFS_CSV
