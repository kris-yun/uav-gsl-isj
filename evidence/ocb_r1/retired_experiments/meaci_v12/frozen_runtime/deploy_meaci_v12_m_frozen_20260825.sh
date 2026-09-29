#!/usr/bin/env bash
set -e
set +u
source /opt/ros/humble/setup.bash
source /dev/shm/house1_msgs_install/local_setup.bash
source /dev/shm/house2_gaden_install/local_setup.bash
source /dev/shm/house1_vgr_install/local_setup.bash
export CMAKE_PREFIX_PATH="/dev/shm/house1_msgs_install:/home/zyc/ros2_ws/install/gmrf_msgs:${CMAKE_PREFIX_PATH}"
set -u

root=/home/zyc/meaci_v12_m_freeze_20260825
test -f "$root/src/gsl_server/package.xml"
test -f "$root/src/gsl_server/src/gsl_server/algorithms/PMFS/internal/RCSDTFEIV12.hpp"
test -f "$root/src/gsl_server/src/gsl_server/algorithms/PMFS/internal/V12ResponseBank.hpp"

colcon --log-base "$root/log" build \
  --base-paths "$root/src/gsl_server" \
  --build-base "$root/build" \
  --install-base "$root/install" \
  --executor sequential \
  --cmake-args -DPFDI_LOW_MEMORY_BUILD=ON -DCMAKE_BUILD_TYPE=Release

binary="$root/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
test -x "$binary"
sha256sum "$binary"
