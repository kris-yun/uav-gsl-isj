#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/ros2_ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
python3 /home/zyc/d1a_common_replay_20260930/run_native_vm.py --run-id ocb_r2_cfg00_r01 --mode on
