#!/usr/bin/env bash
set -euo pipefail
root=/home/zyc/CTPI_ONLINE_CORE_V2_20260905
stage="$root/gmrf_wind_failure_trace_v1"
test -d "$stage"
test ! -e "$stage/FAILED_ARM"
g++ -std=c++17 -O2 -Wall -Wextra -Werror -DCTPI_CHECKED_WIND -DCTPI_WIND_ITER_TRACE \
  -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include \
  -I/usr/include/eigen3 $(pkg-config --cflags opencv4) \
  "$root/tools/ctpi_v2_gmrf_spent_wind.cpp" \
  -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -lgmrf_wind_core -lopencv_imgcodecs -lopencv_core -lyaml-cpp -o "$stage/wind_replay"
"$stage/wind_replay" \
  "$root/gmrf_spent_wind_v2/NAVIGATION_MAP/navigation_slice.yaml" \
  "$root/gmrf_spent_wind_v1/H01_wind_trace.csv" \
  "$root/gmrf_checked_wind_v1/checked_latest_cell.json" "$stage/FAILED_ARM" \
  > "$stage/RUN.log" 2>&1
