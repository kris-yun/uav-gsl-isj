#!/usr/bin/env bash
set -Ee -o pipefail
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
export LD_LIBRARY_PATH=/home/zyc/ros2_ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}
exec python3 /home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/tools/bind_native_bank_views_vm.py
