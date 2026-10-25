#!/usr/bin/env bash
# Optional compiler reproduction only. Does not run propagation or ROS.
set -Ee -o pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_core="$task_root/build_source/gaden_core"
task_runtime="$task_root/native_runtime"
mkdir -p "$task_root/rebuilt_tools"
task_includes=(-I"$task_core/include" -I"$task_core/third_party/DDA/include"
  -I"$task_core/third_party/DDA/third_party/glm"
  -I"$task_core/third_party/yaml-cpp/include" -I"$task_core/third_party/libbsc")
task_links=(-L"$task_runtime" -Wl,-rpath,'$ORIGIN/../native_runtime'
  -Wl,--gc-sections -lfmt -lyaml-cpp -lz -lbsc)
task_base_sources=("$task_core/src/Simulation.cpp" "$task_core/src/Environment.cpp"
  "$task_core/src/WindSequence.cpp" "$task_core/src/GasSource.cpp")
task_common=(-std=c++20 -O2 -DGADEN_ROS=0 -DGPU_ACCELERATION=0
  -include bits/stdc++.h -ffunction-sections -fdata-sections)
g++ "${task_common[@]}" -fopenmp -I"$task_root/build_source/override" \
  "${task_includes[@]}" "$task_root/code/physics.cpp" "${task_base_sources[@]}" \
  "$task_core/src/PlaybackSimulation.cpp" "$task_core/src/RunningSimulation.cpp" \
  "${task_links[@]}" -o "$task_root/rebuilt_tools/physics"
g++ "${task_common[@]}" "${task_includes[@]}" \
  "$task_root/build_source/headless_saved_query.cpp" "${task_base_sources[@]}" \
  "$task_core/src/PlaybackSimulation.cpp" "${task_links[@]}" \
  -o "$task_root/rebuilt_tools/headless_saved_query"
g++ "${task_common[@]}" "${task_includes[@]}" "$task_root/code/kernel.cpp" \
  "${task_base_sources[@]}" "${task_links[@]}" -o "$task_root/rebuilt_tools/kernel"
task_frozen="$task_root/build_source/frozen_source_snapshot"
g++ -std=gnu++17 -O3 -DNDEBUG -include bits/stdc++.h \
  -I"$task_root/build_source/compatibility_headers" -I"$task_frozen/src" \
  -I"$task_frozen/third_party/DDA/include" -I"$task_frozen/third_party/xxHash/include" \
  "$task_root/event_control/native_observer.cpp" \
  "$task_frozen/src/gsl_server/algorithms/Common/Utils/NQAQuadtree.cpp" \
  -o "$task_root/rebuilt_tools/native_observer"
printf '%s\n' 'TOOLS_REBUILT_NO_PHYSICAL_OR_ROS_RUN'
