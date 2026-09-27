#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
ROOT=/home/zyc/ros2_ws/brg_closedloop_20260927
P=/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927
python3 "$P/integration/add_readonly_audit.py" --pmfs-dir "$ROOT/src/gsl_server/src/gsl_server/algorithms/PMFS"
export CMAKE_BUILD_PARALLEL_LEVEL=1 MAKEFLAGS=-j1
colcon --log-base "$ROOT/log_audit" build --base-paths "$ROOT/src" --packages-select gsl_server --build-base /dev/shm/brg_closedloop_build_20260927 --install-base "$ROOT/install" --executor sequential --parallel-workers 1 --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
sha256sum "$ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" > "$ROOT/binary_audit.sha256"
