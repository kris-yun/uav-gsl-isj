#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
cd /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws
export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 OMP_NUM_THREADS=1
colcon build --executor sequential --packages-select gaden_common gaden_filament_simulator gaden_preprocessing --allow-overriding gaden_common gaden_filament_simulator --cmake-args -DCMAKE_BUILD_TYPE=Release "-DCMAKE_EXE_LINKER_FLAGS=-L/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc -Wl,-rpath,/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc"
