#!/bin/bash
cd /home/zyc/gsl_ws
source install/setup.bash
pkill -9 -f vgr_sim_node 2>/dev/null
pkill -9 -f gsl_actionserver 2>/dev/null
sleep 1
rm -f /tmp/gsl_result.csv /tmp/gsl_launch.log

METHOD=$1
SEED=$2
HOUSE=$3
CONFIG=$4
DPATH=$5
SX=$6
SY=$7

nohup ros2 launch vgr_bridge vgr_minimal.launch.py \
  gsl_method:=$METHOD \
  config_id:=$CONFIG \
  seed:=$SEED \
  vgr_data_path:=$DPATH \
  start_x:=$SX \
  start_y:=$SY \
  > /tmp/gsl_launch.log 2>&1 &

echo "LAUNCHED PID=$! $METHOD $HOUSE seed=$SEED"
