#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 /home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/tools/build_full_open_banks_vm.py
