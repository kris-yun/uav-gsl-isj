#!/usr/bin/env bash
set -Ee -o pipefail

# Run on the VM after staging official PMFS into a fresh package directory.
ROOT="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
PKG="${ROOT}/src/gsl_server"
[[ -f "${PKG}/package.xml" ]] || { echo "missing isolated gsl_server package" >&2; exit 64; }
grep -Fq 'set(USE_GADEN ON)' "${PKG}/CMakeLists.txt" || { echo "USE_GADEN not enabled" >&2; exit 65; }
[[ -f "${PKG}/src/gsl_server/algorithms/PMFS/PMFSLib.cpp" ]] || exit 66
grep -Fq 'NATIVE_RECOVERY_WIND_PATH=GADEN_GROUND_TRUTH' \
  "${PKG}/src/gsl_server/algorithms/PMFS/PMFSLib.cpp" || exit 67

source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
cd "${ROOT}"
export CMAKE_BUILD_PARALLEL_LEVEL=1
export MAKEFLAGS=-j1
colcon --log-base "${ROOT}/log" build --base-paths "${ROOT}/src" --packages-select gsl_server \
  --build-base "${ROOT}/build" --install-base "${ROOT}/install" \
  --executor sequential --parallel-workers 1 --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DPFDI_LOW_MEMORY_BUILD=ON

BIN="${ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
[[ -x "${BIN}" ]] || { echo "missing recovery binary" >&2; exit 68; }
if ! grep -R -l -- '-DUSE_GADEN' "${ROOT}/build/gsl_server/CMakeFiles" >/dev/null 2>&1; then
  echo "USE_GADEN compile definition absent from build files" >&2
  exit 69
fi
echo "NATIVE_RECOVERY_BUILD_PASS binary=${BIN}"
sha256sum "${BIN}" "${PKG}/src/gsl_server/algorithms/PMFS/PMFSLib.cpp" \
  "${PKG}/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp" "${PKG}/CMakeLists.txt"
