#!/usr/bin/env bash
set -euo pipefail

SOURCE_RUNTIME=/dev/shm/cstar_joint_development_20260908
TARGET_RUNTIME=/dev/shm/cstar_core_m1_runtime_20260908
SOURCE_BUILD=/dev/shm/cstar_pmfs_cer_ratio_memberctx_build_20260908
TARGET_BUILD=/dev/shm/cstar_pmfs_core_m1_build_20260908

test -d "$SOURCE_RUNTIME"
test -d "$SOURCE_BUILD/src/gsl_server"
test -f "$SOURCE_BUILD/deps/install/setup.bash"
test ! -e "$TARGET_RUNTIME"
test ! -e "$TARGET_BUILD"

cp -a "$SOURCE_RUNTIME" "$TARGET_RUNTIME"
mkdir -p "$TARGET_BUILD/src"
cp -a "$SOURCE_BUILD/src/gsl_server" "$TARGET_BUILD/src/gsl_server"
ln -s "$SOURCE_BUILD/deps" "$TARGET_BUILD/deps"

printf '%s\n' \
  "CSTAR_CORE_M1_VM_PREPARE=PASS" \
  "TARGET_RUNTIME=$TARGET_RUNTIME" \
  "TARGET_BUILD=$TARGET_BUILD"
