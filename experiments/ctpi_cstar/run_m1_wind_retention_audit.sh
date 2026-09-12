#!/usr/bin/env bash
set -euo pipefail
OUT=${1:?provide fresh task tmpfs directory}
case "$OUT" in /dev/shm/m1_retention_20260911.*) ;; *) exit 2;; esac
cd "$OUT"
export TMPDIR="$OUT"
test ! -e results
mkdir results
INPUT=/home/zyc/M1_GMRF_SHADOW_20260910/cstar_m1_gmrf_shadow_inputs_20260910
g++ -std=c++17 -O2 m1_gmrf_shadow.cpp -I/home/zyc/ros2_ws/install/gmrf_wind_mapping/include -L/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -Wl,-rpath,/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib -lgmrf_wind_core -o replay
sha256sum replay m1_gmrf_shadow.cpp /home/zyc/ros2_ws/install/gmrf_wind_mapping/lib/libgmrf_wind_core.so > results/identity.sha256
for house in H01 H02 H03; do
  for wind in fast slow; do
    case_id=${house}_SA_${wind}
    ./replay "$INPUT/${house}.map" "$INPUT/${case_id}.obs" "results/${case_id}.txt" 20 aligned-latest-per-cell > "results/${case_id}.log" 2>&1
    tail -n 1 "results/${case_id}.log"
  done
done
sha256sum results/*.txt results/*.rejected results/*.log > results/outputs.sha256
