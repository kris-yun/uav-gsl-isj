#!/bin/bash
# Batch experiment: WC-RIF vs PMFS vs GrGSL on House01/02/03
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTDIR=/tmp/batch_results
mkdir -p $OUTDIR

run_exp() {
    local ALG=$1 SEED=$2 CONFIG=$3 DPATH=$4 SX=$5 SY=$6 SZ=$7 STARTX=$8 STARTY=$9
    local TAG="${ALG}_s${SEED}"
    local RDIR="$OUTDIR/$TAG"
    mkdir -p "$RDIR"

    pkill -9 -f vgr_sim_node 2>/dev/null; pkill -9 -f gsl_actionserver 2>/dev/null
    sleep 2

    timeout 360 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        algorithm:=$ALG method:=$ALG method_family:=baseline ablation_id:=$ALG \
        scenario_id:=test dataset:=VGR \
        config_id:=$CONFIG \
        vgr_data_path:=$DPATH \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STARTX start_y:=$STARTY \
        seed:=$SEED flight_height:=1.0 timeout_sec:=300 \
        run_dir:=$RDIR > "$RDIR/launch.log" 2>&1

    RESULT=$(cat $RDIR/official_gsl_results.csv 2>/dev/null)
    echo "$ALG,$SEED,$RESULT"
}

echo "method,seed,status,time,error" > $OUTDIR/results.csv

# House01: source(-0.60, 1.95), config=2,4-1_fast, start=(-1.5, -2.5)
for ALG in WC_RIF_GSL PMFS GrGSL; do
    for SEED in 0 1 2; do
        echo "Running $ALG seed=$SEED on House01..."
        R=$(run_exp $ALG $SEED 2,4-1_fast /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 -0.60 1.95 0.40 -1.5 -2.5)
        echo "H01,$R" >> $OUTDIR/results.csv
    done
done

# House02: source from VGR
for ALG in WC_RIF_GSL PMFS GrGSL; do
    for SEED in 0 1 2; do
        echo "Running $ALG seed=$SEED on House02..."
        R=$(run_exp $ALG $SEED 3,5-1_fast /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02 -0.50 2.00 0.40 -1.5 -2.5)
        echo "H02,$R" >> $OUTDIR/results.csv
    done
done

# House03: source from VGR
for ALG in WC_RIF_GSL PMFS GrGSL; do
    for SEED in 0 1 2; do
        echo "Running $ALG seed=$SEED on House03..."
        R=$(run_exp $ALG $SEED 1-2,5_fast /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03 -0.45 1.90 -0.10 -1.5 -2.5)
        echo "H03,$R" >> $OUTDIR/results.csv
    done
done

echo "=== ALL DONE ==="
echo "Results: $OUTDIR/results.csv"
cat $OUTDIR/results.csv
