#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

SEEDS=(0 1 2)
HOUSES=(House01 House02 House03)
OUT=/tmp/cp_sbd_exp/eprocess_v5/results.csv
mkdir -p /tmp/cp_sbd_exp/eprocess_v5
echo  method,house,seed,dist,ep_stop_step,eproc_value > 

for house in ; do
  for seed in ; do
    echo === Running seed= ===
    LOGFILE=/tmp/cp_sbd_exp/eprocess_v5/Ours__s.log
    timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \
      environment:= \
      method:=M7_full_saisc_pf \
      seed:= \
      2>&1 | sed 's/\x1b\[[0-9;]*m//g' > 

    DIST=
    EP_STEP=
    EPROC=
    
    echo  -> dist= ep_stop_step= eproc=
    echo Ours, >> 
  done
done

echo === RESULTS ===
cat 
