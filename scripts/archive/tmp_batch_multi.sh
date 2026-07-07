#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUT=/tmp/multi_house_exp
mkdir -p $OUT
CSV=$OUT/all_results.csv
echo "method,house,scenario,seed,final_error,steps,type" > $CSV

run_one() {
    local algo=$1 house=$2 config=$3 sx=$4 sy=$5 sz=$6 stx=$7 sty=$8 seed=$9
    local logfile="$OUT/${house}_${config}_${algo}_s${seed}.log"
    
    # Determine data path
    local datapath
    if [ "$house" = "House01" ]; then
        datapath="/home/zyc/vgr_data_scenarios/House01"
    else
        datapath="/home/zyc/vgr_data_scenarios/${house}/${house}"
    fi
    
    # Skip if already done
    if grep -q "${algo},${house},${config},${seed}," $CSV 2>/dev/null; then
        echo "[$(date +%H:%M:%S)] SKIP $algo $house/$config seed=$seed"
        return 0
    fi
    
    echo "[$(date +%H:%M:%S)] $algo $house/$config seed=$seed"
    
    local extra_args=""
    if [ "$algo" = "OPGSL" ]; then
        extra_args="algorithm:=OPGSL use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false opgsl.event_driven.enabled:=true"
    else
        extra_args="algorithm:=$algo use_sbd:=false"
    fi
    
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$datapath config_id:=$config \
        source_x:=$sx source_y:=$sy source_z:=$sz \
        start_x:=$stx start_y:=$sty seed:=$seed \
        timeout_sec:=180 resultsFile:=$OUT/null_results.txt \
        $extra_args > $logfile 2>&1 &
    local PID=$!
    
    local ELAPSED=0
    while [ $ELAPSED -lt 250 ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        if grep -q "DONE, CLOSING" $logfile 2>/dev/null; then
            sleep 3
            break
        fi
        if ! kill -0 $PID 2>/dev/null; then
            break
        fi
    done
    
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    pkill -9 -f benchmark_runner 2>/dev/null
    kill -9 $PID 2>/dev/null
    sleep 3
    
    local ERROR=$(grep "wrote.*final_error" $logfile | grep -oP 'final_error=\K[0-9.]+')
    local STEPS=$(grep "steps=" $logfile | tail -1 | grep -oP 'steps=\K[0-9]+')
    local TYPE="timeout"
    
    if [ -n "$ERROR" ]; then
        echo "$algo,$house,$config,$seed,$ERROR,${STEPS:-0},$TYPE" >> $CSV
        echo "  -> error=${ERROR}m steps=${STEPS:-?}"
    else
        # Try to extract from RESULT line
        local RESULT_ERROR=$(grep "RESULT IS:" $logfile | grep -oP 'Search_d=\K[0-9.]+')
        if [ -n "$RESULT_ERROR" ]; then
            echo "$algo,$house,$config,$seed,$RESULT_ERROR,0,result" >> $CSV
            echo "  -> error=${RESULT_ERROR}m (from result)"
        else
            echo "$algo,$house,$config,$seed,999,0,failed" >> $CSV
            echo "  -> FAILED"
        fi
    fi
}

# Scenario: HOUSE CONFIG SX SY SZ STX STY
# House01 has flat path, House02+ have nested path
SCENARIOS=(
    "House01 2,4-1_fast -0.40 -2.90 -0.30 -0.90 0.15"
    "House01 1,3-2,4_fast -0.60 1.95 0.40 -0.90 0.15"
    "House02 3,5-1_fast 0.00 -1.00 0.20 1.06 -2.50"
    "House02 4,5-3_fast 1.00 -2.30 -0.10 -3.00 3.00"
    "House03 1-2,5_fast -0.45 1.90 -0.10 7.10 -0.51"
    "House03 5-3_fast 8.20 5.00 -0.20 2.00 0.00"
)

ALGORITHMS=("OPGSL" "SurgeCast" "GrGSL")
SEEDS=3

for scenario in "${SCENARIOS[@]}"; do
    read -r house config sx sy sz stx sty <<< "$scenario"
    for algo in "${ALGORITHMS[@]}"; do
        for seed in $(seq 0 $((SEEDS-1))); do
            run_one "$algo" "$house" "$config" "$sx" "$sy" "$sz" "$stx" "$sty" "$seed"
        done
    done
done

echo ""
echo "=== ALL EXPERIMENTS COMPLETE ==="
cat $CSV