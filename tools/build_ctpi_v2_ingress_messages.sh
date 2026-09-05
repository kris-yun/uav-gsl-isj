#!/usr/bin/env bash
set -Eeuo pipefail
# Restore only the required message types in an isolated, persistent install.
set +u
source /opt/ros/humble/setup.bash
set -u
ROOT=/home/zyc/CTPI_ONLINE_CORE_V2_20260905
colcon --log-base "$ROOT/message_log" build \
  --base-paths /home/zyc/ros2_ws/src/olfaction_msgs \
  --build-base "$ROOT/message_build" --install-base "$ROOT/message_install" \
  --executor sequential --cmake-args -DCMAKE_BUILD_TYPE=Release
