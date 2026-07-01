#!/bin/bash
# Batch run all experiments - fixed parsing
RESULTS_FILE="/tmp/all_results.csv"
echo "method,house,seed,distance,time_s,status" > $RESULTS_FILE

run_one() {
    METHOD=$1
    HOUSE=$2
    SEED=$3
    CONFIG=$4
    DPATH=$5
    SX=$6
    SY=$7
    TIMEOUT=$8
    
    cd /home/zyc/gsl_ws
    source install/setup.bash
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    sleep 1
    rm -f /tmp/gsl_result.csv /tmp/gsl_launch.log
    
    nohup ros2 launch vgr_bridge vgr_minimal.launch.py \
      gsl_method:=$METHOD \
      config_id:=$CONFIG \
      seed:=$SEED \
      vgr_data_path:=$DPATH \
      start_x:=$SX \
      start_y:=$SY \
      > /tmp/gsl_launch.log 2>&1 &
    
    sleep 12
    
    python3 /tmp/gsl_run_client.py $METHOD $TIMEOUT > /tmp/client_out.txt 2>&1
    
    sleep 2
    
    DIST="NaN"
    TIME="NaN"
    STATUS="FAIL"
    
    # Parse from CSV - use tail to skip dash lines
    if [ -f /tmp/gsl_result.csv ]; then
        LINE=$(tail -1 /tmp/gsl_result.csv)
        if [ -n "$LINE" ] && ! echo "$LINE" | grep -q '^-'; then
            TIME=$(echo "$LINE" | awk '{print $1}')
            DIST=$(echo "$LINE" | awk '{print $2}')
            STATUS="OK"
        fi
    fi
    
    # Fallback: parse from log
    if [ "$STATUS" = "FAIL" ]; then
        RESULT_LINE=$(grep 'RESULT IS' /tmp/gsl_launch.log 2>/dev/null | tail -1)
        if [ -n "$RESULT_LINE" ]; then
            if echo "$RESULT_LINE" | grep -q 'Success=1'; then
                STATUS="SUCCESS"
                # Try Error= field
                ERR_VAL=$(echo "$RESULT_LINE" | sed 's/.*Error=\([0-9.]*\).*/\1/')
                if [ "$ERR_VAL" != "$RESULT_LINE" ]; then
                    DIST=$ERR_VAL
                fi
                # Try Nav_d= field  
                NAV_VAL=$(echo "$RESULT_LINE" | sed 's/.*Nav_d=\([0-9.]*\).*/\1/')
                if [ "$NAV_VAL" != "$RESULT_LINE" ] && [ "$DIST" = "NaN" ]; then
                    DIST=$NAV_VAL
                fi
                TIME_VAL=$(echo "$RESULT_LINE" | sed 's/.*Search_t=\([0-9.]*\).*/\1/')
                if [ "$TIME_VAL" != "$RESULT_LINE" ]; then
                    TIME=$TIME_VAL
                fi
            else
                STATUS="FAIL"
                ERR_VAL=$(echo "$RESULT_LINE" | sed 's/.*Error=\([0-9.]*\).*/\1/')
                if [ "$ERR_VAL" != "$RESULT_LINE" ]; then
                    DIST=$ERR_VAL
                fi
            fi
        fi
    fi
    
    echo "$METHOD,$HOUSE,$SEED,$DIST,$TIME,$STATUS" >> $RESULTS_FILE
    echo "  -> $METHOD $HOUSE s=$SEED: dist=$DIST time=$TIME status=$STATUS"
    
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_actionserver 2>/dev/null
    sleep 1
}

echo "=== Starting batch experiments ==="

# OPGSL all houses
for s in 0 1 2 3 4; do
    echo "[OPGSL H01 s=$s]"
    run_one OPGSL H01 $s "2,4-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01" -0.9 0.15 120
done
for s in 0 1 2 3 4; do
    echo "[OPGSL H02 s=$s]"
    run_one OPGSL H02 $s "3,5-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02" -0.9 0.15 120
done
for s in 0 1 2 3 4; do
    echo "[OPGSL H03 s=$s]"
    run_one OPGSL H03 $s "1-2,5_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03" -0.9 0.15 120
done

# PMFS all houses
for s in 0 1 2 3 4; do
    echo "[PMFS H01 s=$s]"
    run_one PMFS H01 $s "2,4-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01" -0.9 0.15 120
done
for s in 0 1 2 3 4; do
    echo "[PMFS H02 s=$s]"
    run_one PMFS H02 $s "3,5-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02" -0.9 0.15 120
done
for s in 0 1 2 3 4; do
    echo "[PMFS H03 s=$s]"
    run_one PMFS H03 $s "1-2,5_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03" -0.9 0.15 120
done

# GrGSL all houses (fewer seeds due to timeout)
for s in 0 1 2; do
    echo "[GrGSL H01 s=$s]"
    run_one GrGSL H01 $s "2,4-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01" -0.9 0.15 360
done
for s in 0 1 2; do
    echo "[GrGSL H02 s=$s]"
    run_one GrGSL H02 $s "3,5-1_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02" -0.9 0.15 360
done
for s in 0 1 2; do
    echo "[GrGSL H03 s=$s]"
    run_one GrGSL H03 $s "1-2,5_fast" "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03" -0.9 0.15 360
done

echo "=== Batch complete ==="
echo "Results:"
cat $RESULTS_FILE
