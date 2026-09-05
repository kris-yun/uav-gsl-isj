#!/usr/bin/env bash
set -Eeuo pipefail
# CPU/DDS-only diagnostic in the existing isolated V2 directory, no House data.
set +u
source /opt/ros/humble/setup.bash
source /home/zyc/CTPI_ONLINE_CORE_V2_20260905/message_install/setup.bash
set -u
export ROS_DOMAIN_ID=187
export ROS_LOCALHOST_ONLY=1
python3 /home/zyc/CTPI_ONLINE_CORE_V2_20260905/tools/ctpi_v2_ingress_ros_probe.py \
  --ingress /home/zyc/CTPI_ONLINE_CORE_V2_20260905/closed_loop/ctpi/ctpi_v2_ingress.py \
  --result /home/zyc/CTPI_ONLINE_CORE_V2_20260905/ROS_INGRESS_PROBE_R2.json
