#!/usr/bin/env bash
set -Ee -o pipefail
ROOT=/home/zyc/ros2_ws/brg_closedloop_20260927
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
mkdir -p "$ROOT/src"
[[ ! -e "$ROOT/src/gsl_server" ]]
cp -a /home/zyc/native_pmfs_recovery_v1/src/gsl_server "$ROOT/src/gsl_server"
P=/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927
python3 "$P/integration/apply_humble_patch.py" --pmfs-dir "$ROOT/src/gsl_server/src/gsl_server/algorithms/PMFS" --dry-run > "$ROOT/patch_dryrun.json"
python3 "$P/integration/apply_humble_patch.py" --pmfs-dir "$ROOT/src/gsl_server/src/gsl_server/algorithms/PMFS" > "$ROOT/patch.json"
export CMAKE_BUILD_PARALLEL_LEVEL=1 MAKEFLAGS=-j1
colcon --log-base "$ROOT/log" build --base-paths "$ROOT/src" --packages-select gsl_server --build-base /dev/shm/brg_closedloop_build_20260927 --install-base "$ROOT/install" --executor sequential --parallel-workers 1 --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DPFDI_LOW_MEMORY_BUILD=ON -DCMAKE_CXX_FLAGS=-fno-omit-frame-pointer
sha256sum "$ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" > "$ROOT/binary.sha256"
