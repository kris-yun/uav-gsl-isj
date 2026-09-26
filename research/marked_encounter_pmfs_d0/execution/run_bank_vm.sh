#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 /home/zyc/marked_encounter_pmfs_d0_20260927/execution/run_bank_vm.py "$@"
