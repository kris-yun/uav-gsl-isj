#!/usr/bin/env bash
set -e -o pipefail
ARCHIVE=${1:?source archive}
BUILD_ROOT=${CSTAR_PMFS_BUILD_ROOT:-/dev/shm/cstar_pmfs_cer_build_20260908}
test ! -e "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT/src/gsl_server"
tar -xf "$ARCHIVE" -C "$BUILD_ROOT/src/gsl_server"
mkdir -p "$BUILD_ROOT/deps/src"
cp -a /home/zyc/ros2_ws/src/GSL/gsl_actions "$BUILD_ROOT/deps/src/gsl_actions"
cp -a /home/zyc/ros2_ws/src/olfaction_msgs "$BUILD_ROOT/deps/src/olfaction_msgs"
cp -a /home/zyc/ros2_ws/src/gmrf_msgs "$BUILD_ROOT/deps/src/gmrf_msgs"
source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/local_setup.bash
CSTAR_GADEN_PREFIX=$(find /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install -mindepth 1 -maxdepth 1 -type d | sort | paste -sd:)
export CMAKE_PREFIX_PATH="$CSTAR_GADEN_PREFIX:${CMAKE_PREFIX_PATH:-}"
export AMENT_PREFIX_PATH="$CSTAR_GADEN_PREFIX:${AMENT_PREFIX_PATH:-}"
export COLCON_LOG_PATH="$BUILD_ROOT/log"
export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1
cd "$BUILD_ROOT"
colcon build --base-paths deps/src --packages-select olfaction_msgs gsl_actions gmrf_msgs \
  --build-base deps/build --install-base deps/install --cmake-args -DCMAKE_BUILD_TYPE=Release \
  > DEPENDENCY_BUILD.log 2>&1
source "$BUILD_ROOT/deps/install/local_setup.bash"
colcon build --packages-select gsl_server --build-base build --install-base install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF \
  > BUILD.log 2>&1
test -x install/gsl_server/lib/gsl_server/gsl_actionserver_node
sha256sum install/gsl_server/lib/gsl_server/gsl_actionserver_node > ALGORITHM_SHA256.txt
echo CSTAR_PMFS_CER_BUILD_PASS
