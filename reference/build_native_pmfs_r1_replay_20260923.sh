#!/usr/bin/env bash
set -Ee -o pipefail

# Add an offline-only executable to the isolated package; the official PMFS
# library sources and the old ROS workspace are not edited.
ROOT="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
PKG="${ROOT}/src/gsl_server"
TOOL="${ROOT}/native_pmfs_r1_forward_replay.cpp"
[[ -f "${TOOL}" && -f "${PKG}/CMakeLists.txt" ]] || exit 64
mkdir -p "${PKG}/src/native_recovery_tools"
cp "${TOOL}" "${PKG}/src/native_recovery_tools/native_pmfs_r1_forward_replay.cpp"
if ! grep -Fq 'add_executable(native_pmfs_r1_forward_replay' "${PKG}/CMakeLists.txt"; then
  cat >>"${PKG}/CMakeLists.txt" <<'CMAKE'

# Native baseline recovery R1: source-blind offline replay tool only.
add_executable(native_pmfs_r1_forward_replay src/native_recovery_tools/native_pmfs_r1_forward_replay.cpp)
ament_target_dependencies(native_pmfs_r1_forward_replay ${COMMON_AMENT_DEPENDENCIES} gmrf_msgs ${CONDITIONAL_GADEN_MSGS})
target_link_libraries(native_pmfs_r1_forward_replay PMFS GSL_common ${OpenCV_LIBS} OpenMP::OpenMP_CXX fmt)
install(TARGETS native_pmfs_r1_forward_replay DESTINATION lib/${PROJECT_NAME})
CMAKE
fi
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
cd "${ROOT}"
export CMAKE_BUILD_PARALLEL_LEVEL=1 MAKEFLAGS=-j1
colcon --log-base "${ROOT}/log_r1" build --base-paths "${ROOT}/src" --packages-select gsl_server \
  --build-base "${ROOT}/build" --install-base "${ROOT}/install" \
  --executor sequential --parallel-workers 1 --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DPFDI_LOW_MEMORY_BUILD=ON
BIN="${ROOT}/install/gsl_server/lib/gsl_server/native_pmfs_r1_forward_replay"
[[ -x "${BIN}" ]] || exit 65
sha256sum "${BIN}" "${TOOL}" "${PKG}/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
