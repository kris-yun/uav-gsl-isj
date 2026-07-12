#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

RESULTS_DIR=/tmp/v8_exp/ablation_corrected
mkdir -p $RESULTS_DIR
RESULTS=$RESULTS_DIR/results.csv
echo "config,scenario,seed,error_m,localized,elapsed_s" > $RESULTS

run_one() {
    local CONFIG=$1 SCENARIO=$2 SEED=$3 EXTRA=$4
    local D C SX SY SZ STX STY
    case $SCENARIO in
        H01_gnd) D=/home/zyc/vgr_data_scenarios/House01; C="2,4-1_fast"; SX=-0.40; SY=-2.90; SZ=-0.30; STX=0.30; STY=-1.20;;
        H01_air) D=/home/zyc/vgr_data_scenarios/House01; C="1,3-2,4_fast"; SX=-0.60; SY=1.95; SZ=0.40; STX=-0.90; STY=0.15;;
    esac
    local LOG=$RESULTS_DIR/log_${CONFIG}_${SCENARIO}_${SEED}.txt
    local START=$(date +%s)
    echo "Running: $CONFIG $SCENARIO seed=$SEED"
    timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:="$D" config_id:="$C" \
        algorithm:=OPGSL method:=M7_full_saisc_pf \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED timeout_sec:=240 \
        use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true \
        opgsl.event_driven.enabled:=true \
        $EXTRA > $LOG 2>&1
    ERR=$(grep -oP "final_error[=:]\s*\K[0-9.]+" $LOG 2>/dev/null | tail -1)
    LOC=$(grep -oP "localized[=:]\s*\K[01]" $LOG 2>/dev/null | tail -1)
    [ -z "$ERR" ] && ERR=99.000
    [ -z "$LOC" ] && LOC=0
    END=$(date +%s)
    ELAPSED=$((END - START))
    echo "$CONFIG,$SCENARIO,$SEED,$ERR,$LOC,$ELAPSED" >> $RESULTS
    echo "  -> err=$ERR loc=$LOC elapsed=${ELAPSED}s"
    killall -9 gsl_actionserver_node vgr_sim_node gsl_benchmark_runner 2>/dev/null
    sleep 2
}

for SCENARIO in H01_gnd H01_air; do
    for SEED in 0 1 2 3 4 5 6 7 8 9; do
        run_one Full $SCENARIO $SEED ""
        run_one A1_FixedEta $SCENARIO $SEED "opgsl.modules.adaptive_eta:=false"
        run_one A2_NoEvtDrv $SCENARIO $SEED "opgsl.event_driven.enabled:=false"
        run_one A3_NoCP $SCENARIO $SEED "opgsl_cp:=false"
        run_one A4_NoLevy $SCENARIO $SEED "opgsl.modules.levy:=false"
        run_one A5_NoUpwind $SCENARIO $SEED "opgsl.modules.upwind_tracking:=false"
        run_one A6_NoGPAlt $SCENARIO $SEED "opgsl.altitude.gp:=false"
    done
done

echo "=== ABLATION COMPLETE ==="
cat $RESULTS