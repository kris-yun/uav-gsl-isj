#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
OUT=/tmp/isj_final_exp
CSV=$OUT/all_results.csv
# Keep baselines, reset OPGSL
cp $OUT/baselines.csv $CSV

run_one() {
    local method_name=$1 extra_args=$2 config=$3 sx=$4 sy=$5 sz=$6 stx=$7 sty=$8 datapath=$9 seed=${10}
    local logfile="$OUT/${config}_${method_name}_s${seed}.log"
    if grep -q "${method_name},${config},${seed}," $CSV 2>/dev/null; then
        return 0
    fi
    echo "[$(date +%H:%M:%S)] $method_name $config s$seed"
    local start_time=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \
        vgr_data_path:=$datapath config_id:=$config \
        source_x:=$sx source_y:=$sy source_z:=$sz \
        start_x:=$stx start_y:=$sty seed:=$seed \
        timeout_sec:=180 resultsFile:=$OUT/null.txt \
        $extra_args > $logfile 2>&1 &
    local PID=$!
    local ELAPSED=0
    while [ $ELAPSED -lt 250 ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        if grep -q "DONE, CLOSING" $logfile 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $PID 2>/dev/null; then break; fi
    done
    local end_time=$(date +%s)
    local wall_time=$((end_time - start_time))
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    pkill -9 -f benchmark_runner 2>/dev/null
    kill -9 $PID 2>/dev/null
    sleep 3
    local ERROR=$(grep "wrote.*final_error" $logfile | grep -oP 'final_error=\K[0-9.]+')
    local STEPS=$(grep "OPGSL-AI step=" $logfile | tail -1 | grep -oP 'step=\K[0-9]+')
    if [ -n "$ERROR" ]; then
        echo "$method_name,$config,$seed,$ERROR,${STEPS:-0},$wall_time,ok" >> $CSV
        echo "  -> ${ERROR}m"
    else
        echo "$method_name,$config,$seed,999,0,$wall_time,failed" >> $CSV
        echo "  -> FAILED"
    fi
}

declare -a CFGS=("2,4-1_fast" "1,3-2,4_fast" "3,5-1_fast" "1-2,5_fast")
declare -a SXS=("-0.40" "-0.60" "0.00" "-0.45")
declare -a SYS=("-2.90" "1.95" "-1.00" "1.90")
declare -a SZS=("-0.30" "0.40" "0.20" "-0.10")
declare -a STXS=("-0.90" "-0.90" "1.06" "2.20")
declare -a STYS=("0.15" "0.15" "-2.50" "0.49")
declare -a DPATHS=("/home/zyc/vgr_data_scenarios/House01" "/home/zyc/vgr_data_scenarios/House01" "/home/zyc/vgr_data_scenarios/House02/House02" "/home/zyc/vgr_data_scenarios/House03/House03")

for idx in 0 1 2 3; do
    cfg=${CFGS[$idx]}; sx=${SXS[$idx]}; sy=${SYS[$idx]}; sz=${SZS[$idx]}
    stx=${STXS[$idx]}; sty=${STYS[$idx]}; dp=${DPATHS[$idx]}
    # OPGSL fixed timeout (new code)
    for seed in $(seq 0 9); do
        run_one "OPGSL_v8" "algorithm:=OPGSL use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false opgsl.event_driven.enabled:=true" "$cfg" "$sx" "$sy" "$sz" "$stx" "$sty" "$dp" "$seed"
    done
done

echo "=== OPGSL_v8 COMPLETE ==="
echo "OPGSL_v8 runs: $(grep OPGSL_v8 $CSV | wc -l)"
echo "Baseline runs: $(grep -E 'SurgeCast|GrGSL' $CSV | wc -l)"