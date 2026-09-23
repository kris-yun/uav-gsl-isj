#!/usr/bin/env bash
set -Ee -o pipefail

# Build an A/B offline replay against an isolated snapshot of the frozen R2
# PMFS sources. Never edit the old ROS workspace, runner, data or bank.
BASE="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
REFERENCE=/home/zyc/native_candidate_replay_build_20260923/src/gsl_server
ROOT="${BASE}/r2_reference_build"
PKG="${ROOT}/src/gsl_server"
TOOL="${BASE}/native_pmfs_r1_forward_replay.cpp"
[[ -f "${TOOL}" && -d "${REFERENCE}" ]] || exit 64
mkdir -p "${ROOT}/src"
if [[ ! -d "${PKG}" ]]; then cp -a "${REFERENCE}" "${PKG}"; fi
[[ "$(sha256sum "${PKG}/src/gsl_server/algorithms/PMFS/PMFSLib.cpp" | cut -d' ' -f1)" == 2e55858ca3f71cc1c6c00f9642ae3c7c3498fcbb2154ae1d88a07cc44b3213b8 ]] || exit 65
[[ "$(sha256sum "${PKG}/src/gsl_server/algorithms/PMFS/PMFS.cpp" | cut -d' ' -f1)" == 6b022d2d0e59be696c85e2672ddf43240dcf47320d150252c926e26dc1cc171d ]] || exit 65
[[ "$(sha256sum "${PKG}/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp" | cut -d' ' -f1)" == d8b7c3d8a3799192719cbbf3abbcc1d421d0acfe3b23f3e8822f5cd3474c30ed ]] || exit 66
[[ "$(sha256sum "${PKG}/src/gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp" | cut -d' ' -f1)" == 26824c31c6b2fea2d801b0d248217077bdd9c65877c52f2389fa4652b1b4c1a2 ]] || exit 67
mkdir -p "${PKG}/tools"
cp "${TOOL}" "${PKG}/tools/native_pmfs_r1_r2_forward_replay.cpp"
if ! grep -Fq 'add_executable(native_pmfs_r1_r2_forward_replay' "${PKG}/CMakeLists.txt"; then
  cat >>"${PKG}/CMakeLists.txt" <<'CMAKE'

# Source-blind recovery R1 A/B replay using frozen R2 PMFS source semantics.
add_executable(native_pmfs_r1_r2_forward_replay tools/native_pmfs_r1_r2_forward_replay.cpp)
target_compile_definitions(native_pmfs_r1_r2_forward_replay PRIVATE R1_R2_REFERENCE_SOURCE=1)
ament_target_dependencies(native_pmfs_r1_r2_forward_replay ${COMMON_AMENT_DEPENDENCIES} gmrf_msgs ${CONDITIONAL_GADEN_MSGS})
target_link_libraries(native_pmfs_r1_r2_forward_replay PMFS GSL_common ${OpenCV_LIBS} OpenMP::OpenMP_CXX fmt)
install(TARGETS native_pmfs_r1_r2_forward_replay DESTINATION lib/${PROJECT_NAME})
CMAKE
fi
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
cd "${ROOT}"
export CMAKE_BUILD_PARALLEL_LEVEL=1 MAKEFLAGS=-j1
colcon --log-base "${ROOT}/log" build --base-paths "${ROOT}/src" --packages-select gsl_server \
  --build-base "${ROOT}/build" --install-base "${ROOT}/install" \
  --executor sequential --parallel-workers 1 --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DPFDI_LOW_MEMORY_BUILD=ON
BIN="${ROOT}/install/gsl_server/lib/gsl_server/native_pmfs_r1_r2_forward_replay"
[[ -x "${BIN}" ]] || exit 68
sha256sum "${BIN}" "${TOOL}" "${PKG}/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
