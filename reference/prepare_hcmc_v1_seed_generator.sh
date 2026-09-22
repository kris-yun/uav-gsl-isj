#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_ROOT="${SOURCE_ROOT:-/home/zyc/ros2_ws/src/GADEN}"
WORK_ROOT="${WORK_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
PATCHED_HEADER="${PATCHED_HEADER:?set PATCHED_HEADER to transferred gaden_seed_only_MathUtils.hpp}"
RAW_QUERY_SOURCE="${RAW_QUERY_SOURCE:?set RAW_QUERY_SOURCE to transferred house1_raw_query.cpp}"
SRC_COPY="${WORK_ROOT}/src/GADEN"
BUILD_BASE="${WORK_ROOT}/build"
INSTALL_BASE="${WORK_ROOT}/install"
LOG_BASE="${WORK_ROOT}/log"
REL_HEADER="gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp"

[[ -d "${SOURCE_ROOT}" ]] || { echo "missing source root: ${SOURCE_ROOT}" >&2; exit 2; }
[[ -f "${PATCHED_HEADER}" ]] || { echo "missing patched header: ${PATCHED_HEADER}" >&2; exit 2; }

mkdir -p "${WORK_ROOT}"
if [[ ! -d "${SRC_COPY}" ]]; then
  mkdir -p "$(dirname "${SRC_COPY}")"
  cp -a "${SOURCE_ROOT}" "${SRC_COPY}"
fi
cp "${PATCHED_HEADER}" "${SRC_COPY}/${REL_HEADER}"

DIFF_FILE="${WORK_ROOT}/seed_only_source.diff"
set +e
diff -ru --exclude .git "${SOURCE_ROOT}" "${SRC_COPY}" > "${DIFF_FILE}"
diff_rc=$?
set -e
[[ ${diff_rc} -eq 1 ]] || { echo "unexpected diff exit ${diff_rc}" >&2; exit 3; }
changed_files="$(grep -c '^diff -ru ' "${DIFF_FILE}" || true)"
[[ "${changed_files}" == "1" ]] || {
  echo "seed-only source audit failed: changed_files=${changed_files}" >&2
  sed -n '1,160p' "${DIFF_FILE}" >&2
  exit 4
}
grep -Fq "${REL_HEADER}" "${DIFF_FILE}" || { echo "wrong changed file" >&2; exit 5; }

set +u
source /opt/ros/humble/setup.bash
set -u
rm -rf "${BUILD_BASE}" "${INSTALL_BASE}" "${LOG_BASE}"
colcon --log-base "${LOG_BASE}" build \
  --base-paths "${SRC_COPY}" \
  --build-base "${BUILD_BASE}" \
  --install-base "${INSTALL_BASE}" \
  --packages-select gaden_common \
  --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release

# gaden_common installs libgaden without installing its private libbsc shared
# object.  Expose the just-built private library during the dependent link;
# this is a build-path repair only and does not alter either source tree.
LIBBSC_DIR="${BUILD_BASE}/gaden_common/third_party/gaden_core/third_party/libbsc"
[[ -f "${LIBBSC_DIR}/libbsc.so" ]] || { echo "missing private libbsc" >&2; exit 6; }
export LIBRARY_PATH="${LIBBSC_DIR}:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${LIBBSC_DIR}:${INSTALL_BASE}/gaden_common/lib:${LD_LIBRARY_PATH:-}"
set +u
source "${INSTALL_BASE}/setup.bash"
set -u
colcon --log-base "${LOG_BASE}" build \
  --base-paths "${SRC_COPY}" \
  --build-base "${BUILD_BASE}" \
  --install-base "${INSTALL_BASE}" \
  --packages-select gaden_msgs gaden_player \
  --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release

set +u
source "${INSTALL_BASE}/setup.bash"
set -u
colcon --log-base "${LOG_BASE}" build \
  --base-paths "${SRC_COPY}" \
  --build-base "${BUILD_BASE}" \
  --install-base "${INSTALL_BASE}" \
  --packages-select gaden_filament_simulator \
  --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release

BINARY="${INSTALL_BASE}/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
LIBGADEN="${INSTALL_BASE}/gaden_common/lib/libgaden.so"
PLAYER="${INSTALL_BASE}/gaden_player/lib/gaden_player/player"
RAW_QUERY="${WORK_ROOT}/house1_raw_query"
[[ -x "${BINARY}" ]] || { echo "missing binary: ${BINARY}" >&2; exit 6; }
[[ -f "${LIBGADEN}" ]] || { echo "missing libgaden: ${LIBGADEN}" >&2; exit 6; }
[[ -x "${PLAYER}" ]] || { echo "missing player: ${PLAYER}" >&2; exit 6; }
c++ -std=c++20 -O2 -include vector -include array "${RAW_QUERY_SOURCE}" -o "${RAW_QUERY}" \
  -I"${INSTALL_BASE}/gaden_common/include" \
  -I"${SRC_COPY}/gaden_common/third_party/gaden_core/third_party/libbsc" \
  -I/opt/ros/humble/include/rclcpp -I/opt/ros/humble/include/rcutils \
  -I/opt/ros/humble/include/rcpputils -I/opt/ros/humble/include \
  -L"${INSTALL_BASE}/gaden_common/lib" -L"${LIBBSC_DIR}" \
  -Wl,-rpath,"${INSTALL_BASE}/gaden_common/lib" \
  -lgaden -lbsc -lfmt -lz -fopenmp
[[ -x "${RAW_QUERY}" ]] || { echo "missing raw query: ${RAW_QUERY}" >&2; exit 6; }

{
  echo "source_root=${SOURCE_ROOT}"
  echo "source_head=$(git -C "${SOURCE_ROOT}" rev-parse HEAD 2>/dev/null || echo UNVERSIONED)"
  sha256sum "${SOURCE_ROOT}/${REL_HEADER}" "${SRC_COPY}/${REL_HEADER}" "${BINARY}" "${LIBGADEN}" "${PLAYER}" "${RAW_QUERY}"
} > "${WORK_ROOT}/build_manifest.txt"
echo "HCMC_GADEN_SEED_ONLY_BUILD_PASS"
