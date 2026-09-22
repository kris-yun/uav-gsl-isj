#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${HCMC_R2_BUILD_ROOT:-/dev/shm/hcmc_v1_r2_runtime_build}"
R2_REFERENCE_COMMIT="b24da77fd24bd5ea2cbb33caf856f80b9d7670e4"

# The HCMC branch intentionally ports only the already-qualified R2 terminal
# lifecycle patch.  No PMFS, HCMC, likelihood, planner, or endpoint formula is
# changed by this build wrapper.
changed="$(git -C "${ROOT_DIR}" diff --name-only 6afc592a5b43093efad7a4bda0c48c0cbb8a7cec -- ros2_package)"
expected=$'ros2_package/src/gsl_server/algorithms/Common/Algorithm.cpp\nros2_package/src/gsl_server/algorithms/Common/Algorithm.hpp\nros2_package/src/gsl_server/gsl_server.cpp'
[[ "${changed}" == "${expected}" ]] || {
  echo "unexpected ros2_package changes:" >&2
  printf '%s\n' "${changed}" >&2
  exit 73
}

rm -rf "${BUILD_ROOT}"
mkdir -p "${BUILD_ROOT}/src"
cp -a "${ROOT_DIR}/ros2_package" "${BUILD_ROOT}/src/gsl_server"

set +u
source /opt/ros/humble/setup.bash
for setup in \
  /home/zyc/ros2_ws/install/setup.bash \
  /dev/shm/house1_msgs_install/setup.bash \
  /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
do
  [[ -f "${setup}" ]] && source "${setup}"
done
set -u
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_msgs/lib:${LD_LIBRARY_PATH:-}"

cd "${BUILD_ROOT}"
colcon build --packages-select gsl_server --executor sequential --cmake-args \
  -DCMAKE_BUILD_TYPE=Release -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF

algorithm="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
endpoint="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/tnqc_expected_value_native"
[[ -x "${algorithm}" && -x "${endpoint}" ]] || { echo "missing R2 build outputs" >&2; exit 74; }
cat > "${BUILD_ROOT}/hcmc_v1_r2_build_provenance.json" <<EOF
{
  "contract": "HCMC_V1_R2_EXECUTION_RUNTIME_V1",
  "source_head": "$(git -C "${ROOT_DIR}" rev-parse HEAD)",
  "r2_reference_commit": "${R2_REFERENCE_COMMIT}",
  "ros2_package_worktree_diff_sha256": "$(git -C "${ROOT_DIR}" diff --binary 6afc592a5b43093efad7a4bda0c48c0cbb8a7cec -- ros2_package | sha256sum | awk '{print $1}')",
  "algorithm_sha256": "$(sha256sum "${algorithm}" | awk '{print $1}')",
  "linked_native_endpoint_sha256": "$(sha256sum "${endpoint}" | awk '{print $1}')",
  "compiler": "$(g++ --version | head -n 1)",
  "scientific_change": false,
  "execution_change": "native PMFS FinalizeTimeBudget emits frozen RESULT IS at 300 s"
}
EOF
echo "HCMC_V1_R2_RUNTIME_BUILD_PASS algorithm=$(sha256sum "${algorithm}" | awk '{print $1}') endpoint=$(sha256sum "${endpoint}" | awk '{print $1}')"
