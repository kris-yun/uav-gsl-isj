#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=/dev/shm/cstar_joint_development_20260908
RUN_ROOT=${CSTAR_CORE_RUN_ROOT:-/mnt/hgfs/workspace/CSTAR_CORE_M1H_H01_SEED4_20260909_R3}
BUILD_ROOT=/dev/shm/cstar_pmfs_core_m1_invariant_build_20260909
ENV_PREFLIGHT=$REPO_ROOT/evidence/cstar_joint_environment_20260908/PREFLIGHT.json
GEOMETRY_MANIFEST=$REPO_ROOT/evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json
QUALIFIED_HELPER=/home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
VGR_BRIDGE_SOURCE_ROOT=/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5
GIT_COMMIT=a633673

test ! -e "$RUN_ROOT"
test -x "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
mkdir -p "$RUN_ROOT"
sha256sum "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" > "$RUN_ROOT/ALGORITHM_SHA256.txt"

for ARM in A0 M1H; do
  HOUSE=H01 SEED=4 SENSOR_SEED=12 ARM="$ARM" RUN_ROOT="$RUN_ROOT" REPO_ROOT="$REPO_ROOT" \
    PFDI_INSTALL_ROOT="$BUILD_ROOT" VGR_BRIDGE_SOURCE_ROOT="$VGR_BRIDGE_SOURCE_ROOT" \
    INTEGRITY_REPORT="$ENV_PREFLIGHT" ENV_PREFLIGHT="$ENV_PREFLIGHT" \
    GEOMETRY_MANIFEST="$GEOMETRY_MANIFEST" QUALIFIED_HELPER="$QUALIFIED_HELPER" \
    STEPS_SOURCE_UPDATE=1 MAX_WARMUP_ITERATIONS=3 MIN_WARMUP_ITERATIONS=1 \
    DOMAIN_ID=222 TIMEOUT_SEC=240.0 METHOD=CTPI_G2_M1_M2 METHOD_FAMILY=ctpi_two_module \
    GIT_COMMIT="$GIT_COMMIT" \
    bash "$REPO_ROOT/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
done

printf '%s\n' "CSTAR_CORE_M1H_H01_SEED4_COMPLETE"
