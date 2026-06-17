#!/bin/bash
# Incremental module experiment - one run at a time
HOUSE=$1
SEED=$2
CONDITION=$3
RESULT_DIR=/tmp/uav_gsl_dqa/incremental
mkdir -p $RESULT_DIR

if [ "$HOUSE" = "House01" ]; then
  DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01
  CONFIG="2,4-1_fast"
  SRC_X=-0.40; SRC_Y=-2.90; SRC_Z=-0.30
  ST_X=-5.0; ST_Y=-5.0
elif [ "$HOUSE" = "House02" ]; then
  DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House02
  CONFIG="3,5-1_fast"
  SRC_X=0.0; SRC_Y=-1.0; SRC_Z=-0.30
  ST_X=-5.39; ST_Y=-6.45
elif [ "$HOUSE" = "House03" ]; then
  DATA_PATH=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House03
  CONFIG="1-2,5_fast"
  SRC_X=-0.45; SRC_Y=1.9; SRC_Z=-0.30
  ST_X=3.15; ST_Y=5.14
fi

PWC=false; PSDE_ON=false; PSDE_FIN=false; SDR=false; MHC=false
EGS=false; DIRL=false; RGC=false; EAE=false

case "$CONDITION" in
  baseline) ;;
  sdr) SDR=true ;;
  pwc) PWC=true ;;
  psde) PSDE_ON=true; PSDE_FIN=true ;;
  pwc_sdr) PWC=true; SDR=true ;;
  sdr_mhc) SDR=true; MHC=true ;;
  dirl) DIRL=true ;;
  dirl_rgc) DIRL=true; RGC=true ;;
  full_psd) PWC=true; SDR=true; PSDE_ON=true; PSDE_FIN=true ;;
  full_review) EGS=true; DIRL=true; RGC=true; EAE=true ;;
esac

OUTFILE=${RESULT_DIR}/${HOUSE}_${CONDITION}_s${SEED}.csv
LOGFILE=${RESULT_DIR}/${HOUSE}_${CONDITION}_s${SEED}.log

source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

pkill -9 -f gsl_ 2>/dev/null || true
pkill -9 -f vgr_ 2>/dev/null || true
pkill -9 -f gmrf_ 2>/dev/null || true
rm -rf /dev/shm/fastrtps_* 2>/dev/null || true
sleep 2

ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
  vgr_data_path:=$DATA_PATH \
  config_id:=$CONFIG \
  algorithm:=PMFS \
  source_x:=$SRC_X source_y:=$SRC_Y source_z:=$SRC_Z \
  start_x:=$ST_X start_y:=$ST_Y \
  seed:=$SEED \
  maxSearchTime:=300.0 \
  method_id:=$CONDITION \
  dataset:=VGR_$HOUSE \
  server_results_file:=$OUTFILE \
  pwc_enabled:=$PWC \
  psde_online_enabled:=$PSDE_ON \
  psde_final_enabled:=$PSDE_FIN \
  sdr_enabled:=$SDR \
  mhc_enabled:=$MHC \
  egs_enabled:=$EGS \
  dirl_enabled:=$DIRL \
  rgc_enabled:=$RGC \
  eae_enabled:=$EAE \
  review_modules_verbose:=true 2>&1 | tee $LOGFILE

echo "DONE: $HOUSE $CONDITION seed=$SEED"
