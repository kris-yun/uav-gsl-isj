#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
cd /home/zyc/pmfs_official_alignment_r5_20261009/ws
export LD_LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH}
export LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LIBRARY_PATH}
export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 OMP_NUM_THREADS=1
colcon build --executor sequential --packages-select basic_sim gaden_player simulated_gas_sensor simulated_anemometer pmfs_env gsl_server --allow-overriding gaden_player gsl_server pmfs_env --cmake-args -DCMAKE_BUILD_TYPE=Release
