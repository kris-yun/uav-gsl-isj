#!/usr/bin/env bash
set -euo pipefail
root=/home/zyc/CTPI_ONLINE_CORE_V2_20260905
stage="$root/gmrf_spent_wind_v2"
test -d "$stage"
test ! -e "$stage/H01_RESULT"
g++ -std=c++17 -O2 -Wall -Wextra -Werror \
  -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include \
  -I/usr/include/eigen3 $(pkg-config --cflags opencv4) \
  "$root/tools/ctpi_v2_gmrf_spent_wind.cpp" \
  -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib \
  -lgmrf_wind_core -lopencv_imgcodecs -lopencv_core -lyaml-cpp \
  -o "$stage/wind_replay"
sha256sum "$stage/wind_replay" \
  "$root/tools/ctpi_v2_gmrf_spent_wind.cpp" \
  "$root/ros2_package/src/gsl_server/algorithms/PMFS/CTPIGmrfWindV2.hpp" \
  /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so \
  /home/zyc/ros2_ws/install/gmrf_wind_mapping/include/gmrf_wind_core/gmrf_map.h \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House01/occupancy.yaml \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House01/occupancy.pgm \
  "$root/gmrf_spent_wind_v1/H01_wind_trace.csv" \
  "$stage/CONTRACT.json"
"$stage/wind_replay" \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House01/occupancy.yaml \
  "$root/gmrf_spent_wind_v1/H01_wind_trace.csv" "$stage/CONTRACT.json" "$stage/H01_RESULT"
