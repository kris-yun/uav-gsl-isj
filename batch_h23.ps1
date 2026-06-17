#!/bin/bash
RESULT_DIR=/tmp/uav_gsl_dqa/incremental
mkdir -p $RESULT_DIR
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

for HOUSE in House02 House03; do
  if [ "$HOUSE" = "House02" ]; then
    DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02
    CONFIG="3,5-1_fast"
    SX=0.0; SY=-1.0; SZ=-0.30
    STX=-5.39; STY=-6.45
  else
    DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03
    CONFIG="1-2,5_fast"
    SX=-0.45; SY=1.9; SZ=-0.30
    STX=3.15; STY=5.14
  fi
  
  for SEED in 0 1 2 3 4; do
    for COND in baseline sdr; do
      OUTFILE=${RESULT_DIR}/${HOUSE}_${COND}_s${SEED}.csv
      if [ -f "$OUTFILE" ]; then
        echo "SKIP $HOUSE $COND seed=$SEED"
        continue
      fi
      SDR=false
      if [ "$COND" = "sdr" ]; then SDR=true; fi
      
      pkill -9 -f gsl_ 2>/dev/null || true
      pkill -9 -f vgr_ 2>/dev/null || true
      pkill -9 -f gmrf_ 2>/dev/null || true
      rm -rf /dev/shm/fastrtps_* 2>/dev/null || true
      sleep 2
      
      echo "RUN $HOUSE $COND seed=$SEED"
      timeout 360 ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
        vgr_data_path:=$DATA_PATH config_id:=$CONFIG algorithm:=PMFS \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=$STX start_y:=$STY seed:=$SEED \
        maxSearchTime:=300.0 method_id:=$COND dataset:=VGR_$HOUSE \
        server_results_file:=$OUTFILE \
        pwc_enabled:=false sdr_enabled:=$SDR review_modules_verbose:=true \
        > ${RESULT_DIR}/${HOUSE}_${COND}_s${SEED}.log 2>&1
      
      tail -1 $OUTFILE 2>/dev/null
    done
  done
done
echo "BATCH2_DONE"
