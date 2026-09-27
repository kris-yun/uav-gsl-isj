#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/zyc/aod_house03_f1_full624_20260927
python3 "$ROOT/amplitude_implementation/test_amplitude_readout.py" > "$ROOT/IMPLEMENTATION_REGRESSION.log" 2>&1
python3 "$ROOT/execution/prepare_candidate_vm.py"
