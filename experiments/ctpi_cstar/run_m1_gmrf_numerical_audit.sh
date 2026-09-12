#!/usr/bin/env bash
set -euo pipefail
cd /home/zyc/M1_GMRF_SHADOW_20260910
mkdir numerical_v2
g++ -std=c++17 -O2 m1_gmrf_shadow.cpp -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -lgmrf_wind_core -o numerical_v2/replay
sha256sum numerical_v2/replay m1_gmrf_shadow.cpp /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so > numerical_v2/identity.sha256
# SA/SB had byte-identical wind inputs/results: use one representative per wind.
for house in H01 H02 H03; do
  for wind in fast slow; do
    case_id=${house}_SA_${wind}
    numerical_v2/replay cstar_m1_gmrf_shadow_inputs_20260910/${house}.map cstar_m1_gmrf_shadow_inputs_20260910/${case_id}.obs numerical_v2/${case_id}.txt 20 > numerical_v2/${case_id}.log 2>&1
    tail -n 1 numerical_v2/${case_id}.log
  done
done
sha256sum numerical_v2/*.txt numerical_v2/*.rejected numerical_v2/*.log > numerical_v2/outputs.sha256
