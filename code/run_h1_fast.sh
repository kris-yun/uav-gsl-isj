#!/bin/bash
# Fast ablation runner with early-stop: kills ROS2 as soon as result file appears
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

RDIR="/tmp/ablation_v2"
DATA="/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01"

run_one() {
    local SEED=$1 COND=$2 PWC=$3 MAC=$4 SDR=$5
    local TAG="House01_${COND}_s${SEED}"
    local RES="$RDIR/${TAG}_server.csv"
    
    if [ -s "$RES" ]; then
        echo "[SKIP] $TAG: $(cat $RES)"
        return 0
    fi
    
    killall -9 gsl_actionserver_node vgr_sim_node gmrf_wind_mapping_node gsl_benchmark_runner 2>/dev/null
    rm -rf /dev/shm/fastrtps_* 2>/dev/null
    sleep 1
    
    echo "[START] $TAG $(date +%H:%M:%S)"
    
    # Launch in background
    timeout 400 ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
        vgr_data_path:=$DATA config_id:=2,4-1_fast \
        source_x:=-0.40 source_y:=-2.90 \
        start_x:=-5.0 start_y:=-5.0 seed:=$SEED \
        server_results_file:=$RES \
        server_path_file:=$RDIR/${TAG}_traj.csv \
        output_csv:=$RDIR/${TAG}_result.csv \
        pwc_enabled:=$PWC mac_enabled:=$MAC sdr_enabled:=$SDR tdc_enabled:=false \
        > $RDIR/${TAG}.log 2>&1 &
    LAUNCH_PID=$!
    
    # Early stop: poll for result file, kill when it appears
    for i in $(seq 1 420); do
        sleep 1
        if [ -s "$RES" ]; then
            sleep 2  # let it flush
            kill -9 $LAUNCH_PID 2>/dev/null
            killall -9 gsl_actionserver_node vgr_sim_node gmrf_wind_mapping_node gsl_benchmark_runner 2>/dev/null
            rm -rf /dev/shm/fastrtps_* 2>/dev/null
            echo "[DONE] $TAG $(date +%H:%M:%S): $(cat $RES)"
            return 0
        fi
        # Check if launch died
        if ! kill -0 $LAUNCH_PID 2>/dev/null; then
            if [ -s "$RES" ]; then
                echo "[DONE] $TAG $(date +%H:%M:%S): $(cat $RES)"
            else
                echo "[FAIL] $TAG: launch exited without result"
            fi
            return 0
        fi
    done
    
    # Timeout
    kill -9 $LAUNCH_PID 2>/dev/null
    killall -9 gsl_actionserver_node vgr_sim_node gmrf_wind_mapping_node gsl_benchmark_runner 2>/dev/null
    rm -rf /dev/shm/fastrtps_* 2>/dev/null
    if [ -s "$RES" ]; then
        echo "[DONE] $TAG $(date +%H:%M:%S): $(cat $RES)"
    else
        echo "[FAIL] $TAG: 400s timeout, no result"
    fi
}

# Run all conditions for seeds 1-9
for SEED in $(seq 1 9); do
    for COND in baseline pwc mac pwc_mac sdr full; do
        case $COND in
            baseline) run_one $SEED baseline false false false ;;
            pwc)      run_one $SEED pwc      true  false false ;;
            mac)      run_one $SEED mac      false true  false ;;
            pwc_mac)  run_one $SEED pwc_mac  true  true  false ;;
            sdr)      run_one $SEED sdr      false false true  ;;
            full)     run_one $SEED full     true  true  true  ;;
        esac
    done
done

echo ""
echo "=== House01 ALL SEEDS Summary ==="
for SEED in $(seq 0 9); do
    for COND in baseline pwc mac pwc_mac sdr full; do
        F="$RDIR/House01_${COND}_s${SEED}_server.csv"
        [ -f "$F" ] && echo "s${SEED} ${COND}: $(cat $F)"
    done
done
