#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/zyc/aod_house03_f1_full624_20260927
python3 "$ROOT/execution/first_gaden_timebase_vm.py" > "$ROOT/first_timebase_phase.log" 2>&1
