#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=/dev/shm/cstar_joint_development_20260908
RUN_ROOT=${CSTAR_CORE_RUN_ROOT:-/mnt/hgfs/workspace/CSTAR_CORE_M1_ENSEMBLE_H02H03_SEED9_20260908_R1}
BUILD_ROOT=/dev/shm/cstar_pmfs_core_m1_ensemble_build_20260908
ENV_PREFLIGHT=$REPO_ROOT/evidence/cstar_joint_environment_20260908/PREFLIGHT.json
GEOMETRY_MANIFEST=$REPO_ROOT/evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json
QUALIFIED_HELPER=/home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
VGR_BRIDGE_SOURCE_ROOT=/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5

test ! -e "$RUN_ROOT"
test -f "$ENV_PREFLIGHT"
test -f "$GEOMETRY_MANIFEST"
test -x "$QUALIFIED_HELPER"
test -x "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
mkdir -p "$RUN_ROOT"
sha256sum "$BUILD_ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" > "$RUN_ROOT/ALGORITHM_SHA256.txt"

for HOUSE in H02 H03; do
  for ARM in A0 M1E; do
    HOUSE="$HOUSE" SEED=9 SENSOR_SEED=12 ARM="$ARM" RUN_ROOT="$RUN_ROOT" REPO_ROOT="$REPO_ROOT" \
      PFDI_INSTALL_ROOT="$BUILD_ROOT" VGR_BRIDGE_SOURCE_ROOT="$VGR_BRIDGE_SOURCE_ROOT" \
      INTEGRITY_REPORT="$ENV_PREFLIGHT" ENV_PREFLIGHT="$ENV_PREFLIGHT" \
      GEOMETRY_MANIFEST="$GEOMETRY_MANIFEST" QUALIFIED_HELPER="$QUALIFIED_HELPER" \
      STEPS_SOURCE_UPDATE=3 MAX_WARMUP_ITERATIONS=3 MIN_WARMUP_ITERATIONS=1 \
      DOMAIN_ID=233 TIMEOUT_SEC=240.0 METHOD=CTPI_G2_M1_M2 METHOD_FAMILY=ctpi_two_module \
      GIT_COMMIT=a88b290579157b3a44b2d9a47bec024b6365324f \
      bash "$REPO_ROOT/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
  done
done

printf '%s\n' "CSTAR_CORE_M1_ENSEMBLE_H02H03_SEED9_COMPLETE"
