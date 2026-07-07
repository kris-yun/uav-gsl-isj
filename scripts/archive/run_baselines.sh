#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
OUT=/tmp/baseline_exp
mkdir -p $OUT

for ALGO in PMFS GrGSL SurgeCast SensorAwareSurgeCastPF; do
    CSV=$OUT/results_${ALGO}.csv
    echo "method,scenario,seed,final_error,localized,steps,type" > $CSV
    
    for SEED in $(seq 0 9); do
        LOG=$OUT/${ALGO}_s${SEED}.log
        echo "=== $ALGO seed $SEED ==="
        
        # Set algorithm-specific parameters
        EXTRA_ARGS=""
        if [ "$ALGO" = "PMFS" ]; then
            EXTRA_ARGS="use_sbd:=false"
        elif [ "$ALGO" = "GrGSL" ]; then
            EXTRA_ARGS="use_sbd:=false"
        elif [ "$ALGO" = "SurgeCast" ]; then
            EXTRA_ARGS="use_sbd:=false"
        elif [ "$ALGO" = "SensorAwareSurgeCastPF" ]; then
            EXTRA_ARGS="use_sbd:=false"
        fi
        
        ros2 launch vgr_bridge vgr_ablation.launch.py seed:=$SEED timeout_sec:=120 config_id:=2,4-1_fast algorithm:=$ALGO $EXTRA_ARGS > $LOG 2>&1 &
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
        
        # Extract result
        ERROR=$(grep "benchmark.*wrote.*final_error" $LOG | grep -oP 'final_error=\K[0-9.]+')
        STEPS=$(grep "RESULT.*steps=" $LOG | grep -oP 'steps=\K[0-9]+')
        TERM=$(grep "benchmark.*wrote" $LOG | grep -oP 'termination=\K\w+')
        
        if [ -n "$ERROR" ]; then
            echo "$ALGO,2,4-1_fast,$SEED,$ERROR,0,$STEPS,$TERM" >> $CSV
            echo "  RESULT: error=${ERROR}m steps=$STEPS"
        else
            # Try to extract from RESULT line
            MAP_ERROR=$(grep "RESULT" $LOG | head -1 | grep -oP 'error=\K[0-9.]+')
            if [ -n "$MAP_ERROR" ]; then
                echo "$ALGO,2,4-1_fast,$SEED,$MAP_ERROR,0,0,map_only" >> $CSV
                echo "  RESULT (map): error=${MAP_ERROR}m"
            else
                echo "$ALGO,2,4-1_fast,$SEED,999,0,0,failed" >> $CSV
                echo "  FAILED"
            fi
        fi
    done
    
    echo ""
    echo "=== $ALGO RESULTS ==="
    cat $CSV
    echo ""
done

echo "=== ALL BASELINES COMPLETE ==="