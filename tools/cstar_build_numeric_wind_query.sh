#!/usr/bin/env bash
# Build a new helper; preserve the historical executable and evidence untouched.
set -e -o pipefail
# Resolve this checkout, not a date-stamped VM directory. An explicit dependency
# setup may be supplied when moving hosts; the default is the frozen VM profile.
CSTAR_BUILD_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CSTAR_BUILD_ROOT"
source "${1:-$CSTAR_BUILD_ROOT/tools/cstar_environment_vm_dependencies.sh}"
test ! -e tools/cstar_numeric_wind_raw_query
COMMON="$CSTAR_GADEN/gaden_common"
g++ -std=c++20 -O2 tools/cstar_numeric_wind_raw_query.cpp \
  -I"$COMMON/include" -I"$COMMON/third_party/DDA/include" \
  -I"$COMMON/third_party/DDA/third_party/glm" -I"$COMMON/third_party/libbsc" \
  -L"$COMMON/lib" -Wl,-rpath,"$COMMON/lib" -lgaden -lfmt \
  -o tools/cstar_numeric_wind_raw_query
python3 -c 'import hashlib,json,pathlib; print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path("tools/cstar_numeric_wind_raw_query.cpp"),pathlib.Path("tools/cstar_numeric_wind_raw_query")]},indent=2))' > tools/cstar_numeric_wind_query_build.json
cat tools/cstar_numeric_wind_query_build.json
