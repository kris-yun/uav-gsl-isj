#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:?set REPO_ROOT to isolated uav-gsl-isj fast-track worktree}"
BUILD_ROOT="${BUILD_ROOT:?set BUILD_ROOT to a fresh build workspace}"
PREP_AUDIT_ROOT="${PREP_AUDIT_ROOT:-${BUILD_ROOT}/ctpi_prepare_audit}"

[[ -d "${REPO_ROOT}/.git" || -f "${REPO_ROOT}/.git" ]] || { echo "CTPI_PREP_NOT_GIT_WORKTREE=${REPO_ROOT}" >&2; exit 2; }
[[ ! -e "${BUILD_ROOT}" ]] || { echo "CTPI_PREP_REFUSE_EXISTING_BUILD_ROOT=${BUILD_ROOT}" >&2; exit 70; }
mkdir -p "${BUILD_ROOT}" "${PREP_AUDIT_ROOT}"

python3 "${REPO_ROOT}/tools/materialize_ctpi_m3_fasttrack_vm_files.py" --repo-root "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/apply_ctpi_m3_fasttrack_runtime_patch.py" --repo-root "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/ctpi_m3_fasttrack_preflight.py" --repo-root "${REPO_ROOT}" --output "${PREP_AUDIT_ROOT}/SOURCE_PREFLIGHT.json"

source /opt/ros/humble/setup.bash
[[ -f /home/zyc/ros2_ws/install/setup.bash ]] && source /home/zyc/ros2_ws/install/setup.bash
[[ -f /dev/shm/house1_msgs_install/setup.bash ]] && source /dev/shm/house1_msgs_install/setup.bash
for setup in \
  /dev/shm/house2_gaden_install/gaden_msgs/share/gaden_msgs/local_setup.bash \
  /dev/shm/house2_gaden_install/gaden_common/share/gaden_common/local_setup.bash \
  /dev/shm/house2_gaden_install/gaden_player/share/gaden_player/local_setup.bash; do
  [[ -f "${setup}" ]] && source "${setup}"
done

mkdir -p "${BUILD_ROOT}/src"
cp -a "${REPO_ROOT}/ros2_package" "${BUILD_ROOT}/src/gsl_server"
(
  cd "${BUILD_ROOT}"
  colcon build --packages-select gsl_server --cmake-args -DCMAKE_BUILD_TYPE=Release \
    2>&1 | tee "${PREP_AUDIT_ROOT}/colcon_build.log"
)

BINARY="${BUILD_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
[[ -x "${BINARY}" ]] || { echo "CTPI_PREP_BINARY_MISSING=${BINARY}" >&2; exit 3; }
BINARY_SHA="$(sha256sum "${BINARY}" | awk '{print $1}')"
strings "${BINARY}" | grep -q 'ctpi_f10' || { echo "CTPI_PREP_BINARY_MISSING_F10_SYMBOL" >&2; exit 4; }
strings "${BINARY}" | grep -q 'ctpi_f11' || { echo "CTPI_PREP_BINARY_MISSING_F11_SYMBOL" >&2; exit 4; }

cat >"${PREP_AUDIT_ROOT}/BUILD_PASS.json" <<EOF
{
  "contract": "CTPI_M3_FASTTRACK_VM_BUILD_V0",
  "repo_head": "$(git -C "${REPO_ROOT}" rev-parse HEAD)",
  "binary": "${BINARY}",
  "binary_sha256": "${BINARY_SHA}",
  "build_root": "${BUILD_ROOT}",
  "status": "CTPI_M3_FASTTRACK_VM_BUILD=PASS"
}
EOF

echo "CTPI_M3_FASTTRACK_VM_BUILD=PASS"
echo "PFDI_INSTALL_ROOT=${BUILD_ROOT}"
