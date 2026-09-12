#!/usr/bin/env bash
set -euo pipefail
cd /home/zyc/M1_GMRF_SHADOW_20260910
mkdir aligned_field_v4
g++ -std=c++17 -O2 m1_gmrf_shadow.cpp -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -lgmrf_wind_core -o aligned_field_v4/replay
sha256sum aligned_field_v4/replay m1_gmrf_shadow.cpp /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so > aligned_field_v4/identity.sha256
for house in H01 H02 H03; do
  for wind in fast slow; do
    case_id=${house}_SA_${wind}
    aligned_field_v4/replay cstar_m1_gmrf_shadow_inputs_20260910/${house}.map cstar_m1_gmrf_shadow_inputs_20260910/${case_id}.obs aligned_field_v4/${case_id}.txt 20 aligned-field > aligned_field_v4/${case_id}.log 2>&1
    tail -n 1 aligned_field_v4/${case_id}.log
  done
done
sha256sum aligned_field_v4/*.txt aligned_field_v4/*.rejected aligned_field_v4/*.log > aligned_field_v4/outputs.sha256
