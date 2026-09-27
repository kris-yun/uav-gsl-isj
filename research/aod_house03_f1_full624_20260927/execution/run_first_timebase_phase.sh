#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/zyc/aod_house03_f1_full624_20260927
python3 "$ROOT/execution/build_timebase_logger_vm.py" > "$ROOT/timebase_build.log" 2>&1
# An exit of 10 is the signed metadata HOLD; it is never followed by more runs.
python3 "$ROOT/execution/first_gaden_timebase_vm.py" > "$ROOT/first_timebase_phase.log" 2>&1
