#!/usr/bin/env bash
set -euo pipefail

SOURCE_BUILD=/dev/shm/cstar_pmfs_core_m1_seq_build_20260908
TARGET_BUILD=/dev/shm/cstar_pmfs_core_m1_stop_build_20260908

test -d "$SOURCE_BUILD/src/gsl_server"
test -f "$SOURCE_BUILD/deps/install/setup.bash"
test ! -e "$TARGET_BUILD"
mkdir -p "$TARGET_BUILD/src"
cp -a "$SOURCE_BUILD/src/gsl_server" "$TARGET_BUILD/src/gsl_server"
ln -s "$SOURCE_BUILD/deps" "$TARGET_BUILD/deps"
printf '%s\n' "CSTAR_CORE_M1_STOP_VM_PREPARE=PASS" "TARGET_BUILD=$TARGET_BUILD"
