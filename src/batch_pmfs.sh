#!/bin/bash
# PMFS scenario experiments - OPGSL on A1_fast (PMFS environment)
DATA=/home/zyc/enva_vgr
OUT=/tmp/cp_sbd_exp
mkdir -p $OUT

PMFS_CSV=$OUT/pmfs_results.csv
if [ ! -f "$PMFS_CSV" ]; then
    echo "method,scenario,seed,map_dist,steps,elapsed,converge_type" > $PMFS_CSV
fi

CFG=A1_fast
SRC_X=5.0
SRC_Y=6.2
SRC_Z=0.5
START_X=1.0
START_Y=1.0
SCENARIO=PMFS_A1

for METHOD in Full NoDDM NoWRAIG NoCP; do
    case $METHOD in
        Full)    DDM=true; WRAIG=true; CP=true ;;
        NoDDM)   DDM=false; WRAIG=true; CP=true ;;
        NoWRAIG) DDM=true; WRAIG=false; CP=true ;;
        NoCP)    DDM=true; WRAIG=true; CP=false ;;
    esac

    for SEED in 0 1 2 3 4 5 6 7 8 9; do
        if grep -q "$METHOD,$SCENARIO,$SEED," $PMFS_CSV 2>/dev/null; then
            echo "SKIP $METHOD $SCENARIO seed=$SEED"
            continue
        fi

        echo "=== Running $METHOD $SCENARIO seed=$SEED ==="
        timeout 420 ros2 launch vgr_bridge vgr_ablation.launch.py \
            vgr_data_path:=$DATA \
            config_id:=$CFG \
            source_x:=$SRC_X \
            source_y:=$SRC_Y \
            source_z:=$SRC_Z \
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
            2>&1 | tee $OUT/log_pmfs_${METHOD}_${SEED}.txt

        FINAL_POS=$(grep "OPGSL-SDNBV RESULT" $OUT/log_pmfs_${METHOD}_${SEED}.txt | tail -1)
        MX=$(echo "$FINAL_POS" | grep -oP "posterior_MAP=\([\d.-]+" | grep -oP "[\d.-]+" | head -1)
        MY=$(echo "$FINAL_POS" | grep -oP "posterior_MAP=\([\d.-]+, [\d.-]+" | grep -oP "[\d.-]+" | tail -1)
        STEPS=$(grep -oP "step=\d+" $OUT/log_pmfs_${METHOD}_${SEED}.txt | tail -1 | grep -oP "\d+")
        ELAPSED=$(grep -oP "t=[\d.]+s" $OUT/log_pmfs_${METHOD}_${SEED}.txt | tail -1 | grep -oP "[\d.]+")

        if grep -q "found\|CONVERGED\|FAST EXIT\|CP-STOP\|DDM-STOP" $OUT/log_pmfs_${METHOD}_${SEED}.txt; then
            CTYPE="found"
        elif grep -q "HARD TIMEOUT" $OUT/log_pmfs_${METHOD}_${SEED}.txt; then
            CTYPE="timeout"
        else
            CTYPE="other"
        fi

        if [ -n "$MX" ] && [ -n "$MY" ]; then
            DIST=$(python3 -c "import math; d=math.sqrt(($MX-5.0)**2+($MY-6.2)**2); print(round(d,2))" 2>/dev/null)
        else
            DIST=""
        fi

        echo "$METHOD,$SCENARIO,$SEED,$DIST,$STEPS,$ELAPSED,$CTYPE" >> $PMFS_CSV
        echo "Result: dist=$DIST steps=$STEPS type=$CTYPE"
        sleep 2
    done
done

echo "=== PMFS experiments complete ==="
cat $PMFS_CSV
