#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/zyc/marked_encounter_pmfs_d0_20260927
python3 "$ROOT/execution/prepare_build_vm.py"
SNAP=/home/zyc/wind_alignment_d0_20260926/inputs
"$ROOT/build/native_parity_replay" "$SNAP" C "$ROOT/parity_off" > "$ROOT/parity_off.log" 2>&1
MARK_EXPORT_ON=1 "$ROOT/build/native_parity_replay" "$SNAP" C "$ROOT/parity_on" > "$ROOT/parity_on.log" 2>&1
python3 "$ROOT/execution/check_parity_vm.py"
