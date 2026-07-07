#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
OUT=/tmp/v63_exp
mkdir -p $OUT
CSV=$OUT/results_v63.csv
echo "method,scenario,seed,final_error,localized,steps,type" > $CSV

for SEED in $(seq 0 9); do
    LOG=$OUT/v63_s${SEED}.log
    echo "=== Running seed $SEED ==="
    ros2 launch vgr_bridge vgr_ablation.launch.py seed:=$SEED timeout_sec:=120 config_id:=2,4-1_fast opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false opgsl.event_driven.enabled:=true > $LOG 2>&1 &
    LAUNCH_PID=$!
    ELAPSED=0
    while [ $ELAPSED -lt 500 ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        if grep -q "search complete" $LOG 2>/dev/null; then sleep 3; break; fi
        if grep -q "FAST EXIT" $LOG 2>/dev/null; then sleep 3; break; fi
        if grep -q "DONE, CLOSING" $LOG 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $LAUNCH_PID 2>/dev/null; then break; fi
    done
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    kill -9 $LAUNCH_PID 2>/dev/null
    sleep 2
    
    # Extract result from log
    ERROR=$(grep "benchmark.*wrote.*final_error" $LOG | grep -oP 'final_error=\K[0-9.]+')
    STEPS=$(grep "RESULT.*steps=" $LOG | grep -oP 'steps=\K[0-9]+')
    HITS=$(grep "RESULT.*hits=" $LOG | grep -oP 'hits=\K[0-9]+')
    MAP_POS=$(grep "RESULT.*posterior_MAP" $LOG | grep -oP 'posterior_MAP=\K\([^)]+\)')
    TERM=$(grep "benchmark.*wrote" $LOG | grep -oP 'termination=\K\w+')
    
    if [ -n "$ERROR" ]; then
        echo "ED_Bayes_V63,2,4-1_fast,$SEED,$ERROR,0,$STEPS,$TERM" >> $CSV
        echo "  RESULT: MAP=$MAP_POS error=${ERROR}m steps=$STEPS hits=$HITS"
    else
        echo "ED_Bayes_V63,2,4-1_fast,$SEED,999,0,0,failed" >> $CSV
        echo "  FAILED: no result found"
    fi
done

echo ""
echo "=== RESULTS ==="
cat $CSV
echo ""
echo "=== STATS ==="
tail -n +2 $CSV | awk -F',' '{sum+=$4; n++; if($4<min||min=="")min=$4; if($4>max)max=$4} END{printf "n=%d mean=%.2f min=%.2f max=%.2f\n", n, sum/n, min, max}'