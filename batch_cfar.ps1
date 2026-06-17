#!/bin/bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
RESULT_DIR=/tmp/uav_gsl_dqa/incremental
DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01

for SEED in 1 2 3 4 5 6 7 8 9; do
  OUTFILE=${RESULT_DIR}/House01_cfar_s${SEED}.csv
  if [ -f "$OUTFILE" ]; then echo "SKIP cfar s${SEED}"; continue; fi
  pkill -9 -f gsl_ 2>/dev/null || true
  pkill -9 -f vgr_ 2>/dev/null || true
  pkill -9 -f gmrf_ 2>/dev/null || true
  rm -rf /dev/shm/fastrtps_* 2>/dev/null || true
  sleep 2
  echo "RUN cfar s${SEED}"
  timeout 360 ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
    vgr_data_path:=$DATA_PATH config_id:=2,4-1_fast algorithm:=PMFS \
    source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
    start_x:=-5.0 start_y:=-5.0 seed:=$SEED maxSearchTime:=300.0 \
    method_id:=cfar dataset:=VGR_House01 server_results_file:=$OUTFILE \
    pwc_enabled:=false sdr_enabled:=false cfar_enabled:=true \
    review_modules_verbose:=true > ${RESULT_DIR}/House01_cfar_s${SEED}.log 2>&1
  LAST=$(tail -1 $OUTFILE 2>/dev/null)
  echo "  -> $LAST"
done
echo "CFAR_BATCH_DONE"
