#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:?set REPO_ROOT to isolated uav-gsl-isj fast-track worktree}"
BUILD_ROOT="${BUILD_ROOT:?set BUILD_ROOT to a fresh build workspace}"
PREP_AUDIT_ROOT="${PREP_AUDIT_ROOT:-${BUILD_ROOT}/ctpi_prepare_audit}"
GADEN_OVERLAY_ROOT="${CTPI_GADEN_OVERLAY_ROOT:-/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install}"
DEP_OVERLAY_ROOT="${CTPI_DEP_OVERLAY_ROOT:-${BUILD_ROOT}/ctpi_dependency_overlay}"

[[ -d "${REPO_ROOT}/.git" || -f "${REPO_ROOT}/.git" ]] || { echo "CTPI_PREP_NOT_GIT_WORKTREE=${REPO_ROOT}" >&2; exit 2; }
[[ ! -e "${BUILD_ROOT}" ]] || { echo "CTPI_PREP_REFUSE_EXISTING_BUILD_ROOT=${BUILD_ROOT}" >&2; exit 70; }
mkdir -p "${BUILD_ROOT}" "${PREP_AUDIT_ROOT}"

python3 "${REPO_ROOT}/tools/materialize_ctpi_m3_fasttrack_vm_files.py" --repo-root "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/apply_ctpi_m3_fasttrack_runtime_patch.py" --repo-root "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/ctpi_m3_fasttrack_preflight.py" --repo-root "${REPO_ROOT}" --output "${PREP_AUDIT_ROOT}/SOURCE_PREFLIGHT.json"

# Phase-1 V5 autonomous environment recovery. Do not source the known-broken
# aggregate /home/zyc/ros2_ws/install/setup.bash. Rebuild the two incomplete
# non-scientific message packages in an isolated overlay, qualify the exact
# historical GADEN install read-only, then construct selective prefixes.
[[ -d "${GADEN_OVERLAY_ROOT}" ]] || { echo "CTPI_PREP_GADEN_CANDIDATE_MISSING=${GADEN_OVERLAY_ROOT}" >&2; exit 41; }
REPO_ROOT="${REPO_ROOT}" CTPI_DEP_OVERLAY_ROOT="${DEP_OVERLAY_ROOT}" \
  bash "${REPO_ROOT}/closed_loop/ctpi/build_ctpi_vm_dependency_overlay_20260903.sh"
CUSTOM_MSG_INSTALL="${DEP_OVERLAY_ROOT}/install"
# Provisional loader path is used only so ldd can test candidate ELF closure.
export LD_LIBRARY_PATH="${GADEN_OVERLAY_ROOT}/gaden_player/lib:${GADEN_OVERLAY_ROOT}/gaden_common/lib:${GADEN_OVERLAY_ROOT}/gaden_msgs/lib:${CUSTOM_MSG_INSTALL}/olfaction_msgs/lib:${CUSTOM_MSG_INSTALL}/gsl_actions/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/opt/ros/humble/lib:${LD_LIBRARY_PATH:-}"
ENV_REPORT="${PREP_AUDIT_ROOT}/VM_DEPENDENCY_QUALIFICATION.json"
ENV_SH="${PREP_AUDIT_ROOT}/CTPI_VM_ENV.sh"
python3 "${REPO_ROOT}/tools/ctpi_vm_dependency_qualifier.py" \
  --candidate-root "${GADEN_OVERLAY_ROOT}" \
  --custom-overlay-root "${CUSTOM_MSG_INSTALL}" \
  --repo-head "$(git -C "${REPO_ROOT}" rev-parse HEAD)" \
  --output "${ENV_REPORT}" \
  --env-sh "${ENV_SH}"
[[ -s "${ENV_SH}" ]] || { echo "CTPI_PREP_ENV_SH_MISSING=${ENV_SH}" >&2; exit 42; }

source /opt/ros/humble/setup.bash
# shellcheck disable=SC1090
source "${ENV_SH}"

# Preserve the historical runner path without copying or rebuilding GADEN.
# Only an absent path or an existing symlink to the exact qualified root is legal.
COMPAT_GADEN=/dev/shm/house2_gaden_install
if [[ -L "${COMPAT_GADEN}" ]]; then
  [[ "$(readlink -f "${COMPAT_GADEN}")" == "$(readlink -f "${GADEN_OVERLAY_ROOT}")" ]] || {
    echo "CTPI_PREP_GADEN_COMPAT_WRONG_TARGET=${COMPAT_GADEN}" >&2; exit 43; }
elif [[ -e "${COMPAT_GADEN}" ]]; then
  echo "CTPI_PREP_GADEN_COMPAT_REFUSE_EXISTING_NONLINK=${COMPAT_GADEN}" >&2; exit 43
else
  ln -s "${GADEN_OVERLAY_ROOT}" "${COMPAT_GADEN}"
fi

mkdir -p "${BUILD_ROOT}/src"
cp -a "${REPO_ROOT}/ros2_package" "${BUILD_ROOT}/src/gsl_server"
export CMAKE_BUILD_PARALLEL_LEVEL="${CTPI_CMAKE_BUILD_PARALLEL_LEVEL:-1}"
export MAKEFLAGS="${CTPI_MAKEFLAGS:--j1}"
(
  cd "${BUILD_ROOT}"
  colcon build --packages-select gsl_server --cmake-args \
    -DCMAKE_BUILD_TYPE=Release \
    -DPFDI_LOW_MEMORY_BUILD=ON \
    -Dgaden_msgs_DIR="${GADEN_OVERLAY_ROOT}/gaden_msgs/share/gaden_msgs/cmake" \
    -Dolfaction_msgs_DIR="${olfaction_msgs_DIR}" \
    -Dgsl_actions_DIR="${gsl_actions_DIR}" \
    -Dgmrf_msgs_DIR="${gmrf_msgs_DIR}" \
    -Dspdlog_DIR="${spdlog_DIR}" \
    -Dfmt_DIR="${fmt_DIR}" \
    2>&1 | tee "${PREP_AUDIT_ROOT}/colcon_build.log"
)

BINARY="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
[[ -x "${BINARY}" ]] || { echo "CTPI_PREP_BINARY_MISSING=${BINARY}" >&2; exit 3; }
BINARY_SHA="$(sha256sum "${BINARY}" | awk '{print $1}')"
BINARY_STRINGS="${PREP_AUDIT_ROOT}/gsl_actionserver_node.strings.txt"
strings "${BINARY}" > "${BINARY_STRINGS}"
grep -Fqx 'ctpi_f10' "${BINARY_STRINGS}" || { echo "CTPI_PREP_BINARY_MISSING_F10_SYMBOL" >&2; exit 4; }
grep -Fqx 'ctpi_f11' "${BINARY_STRINGS}" || { echo "CTPI_PREP_BINARY_MISSING_F11_SYMBOL" >&2; exit 4; }

cat >"${PREP_AUDIT_ROOT}/BUILD_PASS.json" <<EOF
{
  "contract": "CTPI_M3_FASTTRACK_VM_BUILD_V1_ENV_QUALIFIED",
  "repo_head": "$(git -C "${REPO_ROOT}" rev-parse HEAD)",
  "binary": "${BINARY}",
  "binary_sha256": "${BINARY_SHA}",
  "binary_strings_sha256": "$(sha256sum "${BINARY_STRINGS}" | awk '{print $1}')",
  "build_root": "${BUILD_ROOT}",
  "gaden_overlay_root": "${GADEN_OVERLAY_ROOT}",
  "custom_message_overlay_root": "${CUSTOM_MSG_INSTALL}",
  "custom_message_overlay_manifest": "${DEP_OVERLAY_ROOT}/DEPENDENCY_OVERLAY_MANIFEST.json",
  "cmake_build_parallel_level": "${CMAKE_BUILD_PARALLEL_LEVEL}",
  "makeflags": "${MAKEFLAGS}",
  "pfdi_low_memory_build": true,
  "dependency_qualification": "${ENV_REPORT}",
  "runtime_env_sh": "${ENV_SH}",
  "status": "CTPI_M3_FASTTRACK_VM_BUILD=PASS"
}
EOF

echo "CTPI_M3_FASTTRACK_VM_BUILD=PASS"
echo "PFDI_INSTALL_ROOT=${BUILD_ROOT}"
echo "CTPI_RUNTIME_ENV_SH=${ENV_SH}"
