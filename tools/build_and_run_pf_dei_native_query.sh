#!/usr/bin/env bash
set -euo pipefail

root=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828
include=/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/include
libbsc_include=/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/third_party/libbsc
result="$root/synthetic_native/FilamentSimulation_gasType_10_sourcePosition_-2.00_0.07_0.20"
occupancy=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv

set +u
source /opt/ros/humble/setup.bash
set -u

g++ -std=c++20 -O2 -I"$include" -I"$libbsc_include" "$root/pf_dei_native_forward_query.cpp" \
    -L"$root/gaden_install/gaden_common/lib" \
    -Wl,-rpath,"$root/gaden_install/gaden_common/lib" \
    -lgaden -lfmt -lz -lbsc -o "$root/pf_dei_native_forward_query"

sha256sum "$root/pf_dei_native_forward_query"
export LD_LIBRARY_PATH="$root/gaden_install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
"$root/pf_dei_native_forward_query" \
    "$occupancy" "$result" "$root/converted_wind_house02" \
    "$root/pf_dei_synthetic_schedule.csv" "$root/shared_query.csv"
head -8 "$root/shared_query.csv"
