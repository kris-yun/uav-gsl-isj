#!/usr/bin/env bash
set -Ee -o pipefail
ROOT="$(git rev-parse --show-toplevel)"
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
BUILD=/home/zyc/persistent_source_pmfs_build_20260926
cmake -S "$ROOT/ros2_package" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DPFDI_LOW_MEMORY_BUILD=ON
cmake --build "$BUILD" --target persistent_source_r1_replay -- -j1
sha256sum "$BUILD/persistent_source_r1_replay" "$ROOT/ros2_package/tools/persistent_source_r1_replay.cpp"
