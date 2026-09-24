#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
GADEN_CORE="${GADEN_CORE:-/home/zyc/gaden_ws/src/gaden_core}"
SRC="${ROOT}/research/generative_lagrangian_filament_world_model_v1/m5_export_filament_frames.cpp"
OUT="${ROOT}/.m5_l1_bin"
CXX="${CXX:-g++}"

[[ -d "${GADEN_CORE}" ]] || { echo "GADEN_CORE not found: ${GADEN_CORE}" >&2; exit 2; }
LIB="$(find "${GADEN_CORE}" -type f -name 'libgaden.so' | head -n1 || true)"
[[ -n "${LIB}" ]] || { echo "libgaden.so not found under ${GADEN_CORE}; build gaden_core first" >&2; exit 3; }
LIBDIR="$(dirname "${LIB}")"

"${CXX}" -std=c++20 -O2 \
  -I"${GADEN_CORE}/include" \
  -I"${GADEN_CORE}/third_party/DDA/include" \
  -I"${GADEN_CORE}/third_party/DDA/third_party/glm" \
  -I"${GADEN_CORE}/third_party/libbsc" \
  "${SRC}" "${LIB}" \
  -Wl,-rpath,"${LIBDIR}" \
  -o "${OUT}"

echo "${OUT}"
