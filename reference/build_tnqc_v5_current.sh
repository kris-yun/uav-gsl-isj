#!/usr/bin/env bash
set -Eeuo pipefail

# Clean pre-truth build for the TNQC V5 300-s gate.
#
# The same colcon invocation builds:
#   - gsl_actionserver_node
#   - tnqc_expected_value_native
# so the authoritative counterfactual endpoint calls the exact
# GSL::Utils::ExpectedValue implementation and toolchain used by PMFS.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_VERIFY="${MANIFEST_VERIFY:-${ROOT_DIR}/reference/verify_tnqc_v5_manifest.py}"
BUILD_ROOT="${TNQC_BUILD_ROOT:-/dev/shm/tnqc_v5_300s_build}"
MANIFEST_REL="evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json"

python3 "${MANIFEST_VERIFY}" --root "${ROOT_DIR}" --manifest "${MANIFEST_REL}"

# A dependency-free compile/run of the frozen TNQC score core catches header
# regressions before the heavier ROS build.
TNQC_CORE_TEST="${BUILD_ROOT}.tnqc_score_test"
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -UNDEBUG \
  -I"${ROOT_DIR}/ros2_package/src" \
  "${ROOT_DIR}/ros2_package/test/test_tnqc_score.cpp" \
  -o "${TNQC_CORE_TEST}"
"${TNQC_CORE_TEST}"
rm -f "${TNQC_CORE_TEST}"

rm -rf "${BUILD_ROOT}"
mkdir -p "${BUILD_ROOT}/src"
cp -a "${ROOT_DIR}/ros2_package" "${BUILD_ROOT}/src/gsl_server"

# Source the qualified VM dependency overlays when present. Infrastructure
# prefixes may differ, but method/source bytes are locked by the manifest.
set +u
source /opt/ros/humble/setup.bash
for setup in \
  /home/zyc/ros2_ws/install/setup.bash \
  /dev/shm/house1_msgs_install/setup.bash \
  /dev/shm/house2_gaden_install/setup.bash \
  /dev/shm/house2_gaden_install/gaden_msgs/share/gaden_msgs/local_setup.bash \
  /dev/shm/house2_gaden_install/gaden_common/share/gaden_common/local_setup.bash
do
  if [[ -f "${setup}" ]]; then
    source "${setup}"
  fi
done
set -u

cd "${BUILD_ROOT}"
colcon build \
  --packages-select gsl_server \
  --cmake-args \
    -DCMAKE_BUILD_TYPE=Release \
    -DPFDI_LOW_MEMORY_BUILD=ON \
    -DBUILD_TESTING=OFF

ALGORITHM_BINARY="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
ENDPOINT_BINARY="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/tnqc_expected_value_native"
[[ -x "${ALGORITHM_BINARY}" ]] || { echo "missing built PMFS binary: ${ALGORITHM_BINARY}" >&2; exit 71; }
[[ -x "${ENDPOINT_BINARY}" ]] || { echo "missing linked-native endpoint binary: ${ENDPOINT_BINARY}" >&2; exit 72; }

ALGORITHM_SHA256="$(sha256sum "${ALGORITHM_BINARY}" | awk '{print $1}')"
ENDPOINT_SHA256="$(sha256sum "${ENDPOINT_BINARY}" | awk '{print $1}')"
MANIFEST_SHA256="$(sha256sum "${ROOT_DIR}/${MANIFEST_REL}" | awk '{print $1}')"
SOURCE_HEAD="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || printf 'UNKNOWN')"
COMPILER="$(g++ --version | head -n 1)"

cat > "${BUILD_ROOT}/tnqc_build_provenance.json" <<EOF
{
  "contract": "TNQC_V5_CLEAN_VM_BUILD_V1",
  "source_head": "${SOURCE_HEAD}",
  "manifest": "${MANIFEST_REL}",
  "manifest_sha256": "${MANIFEST_SHA256}",
  "compiler": "${COMPILER}",
  "cmake_build_type": "Release",
  "pfdi_low_memory_build": true,
  "algorithm_binary": "${ALGORITHM_BINARY}",
  "algorithm_sha256": "${ALGORITHM_SHA256}",
  "endpoint_binary": "${ENDPOINT_BINARY}",
  "endpoint_sha256": "${ENDPOINT_SHA256}"
}
EOF

echo "TNQC_CLEAN_BUILD_PASS root=${BUILD_ROOT} algorithm_sha256=${ALGORITHM_SHA256} endpoint_sha256=${ENDPOINT_SHA256}"
