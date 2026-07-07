#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
OUT=/tmp/house01b_exp
mkdir -p $OUT
CSV=$OUT/results_house01b.csv
echo "method,scenario,seed,final_error,localized,steps,type" > $CSV

for SEED in $(seq 0 4); do
    LOG=$OUT/opgsl_s${SEED}.log
    echo "=== OPGSL 1,3-2,4_fast seed $SEED ==="
    ros2 launch vgr_bridge vgr_ablation.launch.py seed:=$SEED timeout_sec:=120 config_id:=1,3-2,4_fast source_x:=-0.60 source_y:=1.95 source_z:=0.40 opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false opgsl.event_driven.enabled:=true > $LOG 2>&1 &
    LAUNCH_PID=$!
    ELAPSED=0
    while [ $ELAPSED -lt 500 ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        if grep -q "DONE, CLOSING" $LOG 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $LAUNCH_PID 2>/dev/null; then break; fi
    done
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    kill -9 $LAUNCH_PID 2>/dev/null
    sleep 2
    
    ERROR=$(grep "benchmark.*wrote.*final_error" $LOG | grep -oP 'final_error=\K[0-9.]+')
    if [ -n "$ERROR" ]; then
        echo "OPGSL,1,3-2,4_fast,$SEED,$ERROR,0,0,timeout" >> $CSV
        echo "  RESULT: error=${ERROR}m"
    else
        echo "OPGSL,1,3-2,4_fast,$SEED,999,0,0,failed" >> $CSV
        echo "  FAILED"
    fi
done

echo ""
echo "=== RESULTS ==="
cat $CSV