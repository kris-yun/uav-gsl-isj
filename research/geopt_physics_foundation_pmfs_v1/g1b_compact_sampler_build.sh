#!/usr/bin/env bash
set -Ee -o pipefail
PREFIX=/home/zyc/hcmc_gaden_seed_build_20260922
SRC=/tmp/m6_g1b_compact_sampler_20260923.cpp
OUT=/tmp/m6_g1b_compact_sampler_20260923
source /opt/ros/humble/setup.bash
g++ -O3 -std=gnu++20 -DGADEN_ROS=1 \
  -isystem /opt/ros/humble/include/rclcpp \
  -isystem "$PREFIX/install/gaden_common/include" \
  -isystem "$PREFIX/install/gaden_common/third_party/DDA/include" \
  -isystem "$PREFIX/install/gaden_common/third_party/DDA/third_party/glm" \
  -isystem "$PREFIX/install/gaden_common/third_party/libbsc" \
  "$SRC" -o "$OUT" \
  -Wl,-rpath,/opt/ros/humble/lib:"$PREFIX/install/gaden_common/lib" \
  "$PREFIX/install/gaden_common/lib/libgaden.so" /usr/lib/x86_64-linux-gnu/libfmt.so \
  /opt/ros/humble/lib/librclcpp.so /opt/ros/humble/lib/librcl.so \
  /opt/ros/humble/lib/librmw_implementation.so /opt/ros/humble/lib/libament_index_cpp.so \
  /opt/ros/humble/lib/librcl_logging_spdlog.so /opt/ros/humble/lib/librcl_logging_interface.so \
  /opt/ros/humble/lib/librmw.so /opt/ros/humble/lib/librcutils.so -ldl
echo "BUILT $OUT"
