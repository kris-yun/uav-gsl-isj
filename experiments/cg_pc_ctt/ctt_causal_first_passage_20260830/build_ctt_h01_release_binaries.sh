#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD/install/setup.bash
set -u

export GADEN_BSC_LIB=/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc

source_root=/home/zyc/PF_DEI_V3_STREAM_BUILD/src
build_root=/home/zyc/CTT_H01_RELEASE_BUILD_20260830

mkdir -p "$build_root/src"
cp "$source_root/CMakeLists.txt" "$build_root/src/CMakeLists.txt"
cp "$source_root/pf_dei_v3_native_stream.cpp" "$build_root/src/"
cp "$source_root/pf_dei_v3_native_multistream.cpp" "$build_root/src/"
cp "$source_root/pf_dei_v3_native_wind_multistream.cpp" "$build_root/src/"

cmake -S "$build_root/src" -B "$build_root/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$build_root/install"
cmake --build "$build_root/build" --parallel 4
cmake --install "$build_root/build"

sha256sum \
  "$source_root/pf_dei_v3_native_multistream.cpp" \
  "$source_root/pf_dei_v3_native_wind_multistream.cpp" \
  "$build_root/install/bin/pf_dei_v3_native_multistream" \
  "$build_root/install/bin/pf_dei_v3_native_wind_multistream" \
  > "$build_root/RELEASE_SHA256SUMS.txt"

grep '^CMAKE_BUILD_TYPE:STRING=Release$' "$build_root/build/CMakeCache.txt"
cat "$build_root/RELEASE_SHA256SUMS.txt"
echo CTT_H01_RELEASE_BUILD=PASS
