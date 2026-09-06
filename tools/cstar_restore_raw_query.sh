#!/usr/bin/env bash
# Rebuild only the archived query helper into the isolated CSTAR tools directory.
set -e -o pipefail
REPO_ROOT=/home/zyc/CSTAR_ENV_ALIGN_20260906
source "$REPO_ROOT/tools/cstar_environment_vm_dependencies.sh"
test ! -e "$REPO_ROOT/tools/house1_raw_query"
COMMON="$CSTAR_GADEN/gaden_common"
g++ -std=c++20 -O2 \
  /home/zyc/scaoi_pmfs_active_sensing_20260818/reference/house1_oracle/house1_raw_query.cpp \
  -I"$COMMON/include" -I"$COMMON/third_party/DDA/include" \
  -I"$COMMON/third_party/DDA/third_party/glm" -I"$COMMON/third_party/libbsc" \
  -L"$COMMON/lib" -Wl,-rpath,"$COMMON/lib" -lgaden -lfmt \
  -o "$REPO_ROOT/tools/house1_raw_query"
sha256sum "$REPO_ROOT/tools/house1_raw_query" \
  /home/zyc/scaoi_pmfs_active_sensing_20260818/reference/house1_oracle/house1_raw_query.cpp
