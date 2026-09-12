#!/usr/bin/env bash
set -euo pipefail
cd /home/zyc/M1_GMRF_SHADOW_20260910
mkdir results_v1
sha256sum replay m1_gmrf_shadow.cpp /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so /home/zyc/ros2_ws/install/gmrf_wind_mapping/include/gmrf_wind_core/gmrf_map.h > results_v1/identity.sha256
for house in H01 H02 H03; do
  for source in SA SB; do
    for wind in fast slow; do
      case_id=${house}_${source}_${wind}
      ./replay cstar_m1_gmrf_shadow_inputs_20260910/${house}.map cstar_m1_gmrf_shadow_inputs_20260910/${case_id}.obs results_v1/${case_id}.txt > results_v1/${case_id}.log 2>&1
      tail -n 1 results_v1/${case_id}.log
    done
  done
done
sha256sum results_v1/*.txt results_v1/*.log > results_v1/outputs.sha256
