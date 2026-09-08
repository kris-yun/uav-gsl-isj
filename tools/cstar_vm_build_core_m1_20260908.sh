#!/usr/bin/env bash
set -euo pipefail

BUILD_ROOT=${CSTAR_BUILD_ROOT:-/dev/shm/cstar_pmfs_core_m1_build_20260908}
SOURCE_ROOT="$BUILD_ROOT/src/gsl_server"
DEPS_ROOT="$BUILD_ROOT/deps/install"

test -d "$SOURCE_ROOT"
test -f "$DEPS_ROOT/setup.bash"
test ! -e "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node"

set +u
source /opt/ros/humble/setup.bash
source "$DEPS_ROOT/setup.bash"
set -u
export CMAKE_BUILD_PARALLEL_LEVEL=1
export MAKEFLAGS=-j1

colcon --log-base "$BUILD_ROOT/log" build \
  --base-paths "$SOURCE_ROOT" \
  --build-base "$BUILD_ROOT/build" \
  --install-base "$BUILD_ROOT/install" \
  --packages-select gsl_server \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF

sha256sum "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
printf '%s\n' "CSTAR_CORE_M1_BUILD=PASS"
