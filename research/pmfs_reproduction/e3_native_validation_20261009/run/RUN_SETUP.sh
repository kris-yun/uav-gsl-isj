#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/setup.bash
export LD_LIBRARY_PATH=/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH
export ROS_DOMAIN_ID=76 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
unset GADEN_RNG_SEED
