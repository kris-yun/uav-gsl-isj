#!/usr/bin/env bash
set -euo pipefail
root=/home/zyc/CTPI_ONLINE_CORE_V2_20260905
stage="$root/gmrf_checked_wind_v1"
test -d "$stage"
test ! -e "$stage/IDENTITY.json"
g++ -std=c++17 -O2 -Wall -Wextra -Werror -DCTPI_CHECKED_WIND \
  -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include \
  -I/usr/include/eigen3 $(pkg-config --cflags opencv4) \
  "$root/tools/ctpi_v2_gmrf_spent_wind.cpp" \
  -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -lgmrf_wind_core -lopencv_imgcodecs -lopencv_core -lyaml-cpp \
  -o "$stage/wind_replay"
python3 "$root/tools/ctpi_v2_checked_wind_run.py"
