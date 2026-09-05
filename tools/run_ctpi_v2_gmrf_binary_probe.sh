#!/usr/bin/env bash
set -e -o pipefail
source /opt/ros/humble/setup.bash
source /home/zyc/CTPI_ONLINE_CORE_V2_20260905/message_install/olfaction_msgs/share/olfaction_msgs/local_setup.bash
export PYTHONPATH="/home/zyc/ros2_ws/install/gmrf_msgs/local/lib/python3.10/dist-packages:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:${LD_LIBRARY_PATH:-}"
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=193
python3 /home/zyc/CTPI_ONLINE_CORE_V2_20260905/tools/ctpi_v2_gmrf_binary_probe.py --output /home/zyc/CTPI_ONLINE_CORE_V2_20260905/GMRF_BINARY_PROBE_R3.json
