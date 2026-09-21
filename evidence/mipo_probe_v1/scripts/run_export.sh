#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /dev/shm/house1_msgs_install/setup.bash
export LD_LIBRARY_PATH="/dev/shm/house2_gaden_install/gaden_player/lib:/dev/shm/house2_gaden_install/gaden_common/lib:/dev/shm/house2_gaden_install/gaden_msgs/lib:/dev/shm/house2_gaden_build/gaden_common/third_party/gaden_core/third_party/libbsc:/dev/shm/house1_msgs_install/lib:/opt/ros/humble/lib:${LD_LIBRARY_PATH:-}"
export AMENT_PREFIX_PATH="/dev/shm/house2_gaden_install/gaden_player:/dev/shm/house2_gaden_install/gaden_common:/dev/shm/house2_gaden_install/gaden_msgs:${AMENT_PREFIX_PATH:-}"
export ROS_DOMAIN_ID=221
export ROS_LOG_DIR=/home/zyc/ros2_ws/mipo_probe_v1_20260921/logs/ros
export OMP_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
set -Ee -o pipefail
python3 /home/zyc/ros2_ws/mipo_probe_v1_20260921/scripts/export_mipo_patch.py query --out /home/zyc/ros2_ws/mipo_probe_v1_20260921
