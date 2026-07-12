#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTDIR=/tmp/v8_exp/v9_kappa_driven
mkdir -p $OUTDIR
CSV=$OUTDIR/results.csv
echo "method,scenario,seed,error_m,localized" > $CSV

run_ours() {
    local SC=$1 CFG=$2 SX=$3 SY=$4 SZ=$5 STX=$6 STY=$7 SEED=$8
    local LOG=$OUTDIR/ours_${SC}_${SEED}.log
    echo "[$(date +%H:%M:%S)] OURS $SC seed=$SEED"
    timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$SC config_id:=$CFG \
        algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED timeout_sec:=240 \
        use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true \
        opgsl.event_driven.enabled:=true > $LOG 2>&1
    ERR=$(grep -oP "final_error[=:]\s*\K[0-9.]+" $LOG 2>/dev/null | tail -1)
    LOC=$(grep -oP "localized[=:]\s*\K[01]" $LOG 2>/dev/null | tail -1)
    [ -z "$ERR" ] && ERR=NaN
    [ -z "$LOC" ] && LOC=0
    echo "OPGSL,$SC,$SEED,$ERR,$LOC" >> $CSV
    echo "  -> error=$ERR loc=$LOC"
    killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
    sleep 3
}

# H01_gnd
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_ours House01 2,4-1_fast -0.40 -2.90 -0.30 0.30 -1.20 $s
done

# H01_air
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_ours House01 1,3-2,4_fast -0.60 1.95 0.40 -0.90 0.15 $s
done

# H02_air
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_ours House02/House02 3,5-1_fast 0.00 -1.00 0.20 -0.50 -2.50 $s
done

# H03_gnd
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_ours House03/House03 1-2,5_fast -0.45 1.90 -0.10 2.00 0.00 $s
done

echo "=== BENCHMARK COMPLETE ==="
cat $CSV