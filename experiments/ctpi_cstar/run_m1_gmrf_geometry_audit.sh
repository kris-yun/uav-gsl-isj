#!/usr/bin/env bash
set -euo pipefail
cd /home/zyc/M1_GMRF_SHADOW_20260910
mkdir geometry_v3
g++ -std=c++17 -O2 m1_gmrf_shadow.cpp -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -lgmrf_wind_core -o geometry_v3/replay
sha256sum geometry_v3/replay m1_gmrf_shadow.cpp /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so > geometry_v3/identity.sha256
for house in H01 H02 H03; do
  case_id=${house}_SA_fast
  geometry_v3/replay cstar_m1_gmrf_shadow_inputs_20260910/${house}.map cstar_m1_gmrf_shadow_inputs_20260910/${case_id}.obs geometry_v3/${case_id}.txt 1 aligned-geometry > geometry_v3/${case_id}.log 2>&1
  tail -n 1 geometry_v3/${case_id}.log
done
