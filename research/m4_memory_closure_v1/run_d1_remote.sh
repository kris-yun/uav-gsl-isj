#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED="research/m4-memory-closure-v1"
[[ "$(git -C "${ROOT}" branch --show-current)" == "${EXPECTED}" ]] || {
  echo "Expected branch ${EXPECTED}" >&2; exit 2;
}

python3 "${ROOT}/research/m4_memory_closure_v1/m4_memory_closure_d1.py" \
  --repo-root "${ROOT}" \
  --dynamic-wind "${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02" \
  --d0-out "${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923" \
  --output-dir "${ROOT}/evidence/m4_memory_closure_v1/d1_reproduction"

cat "${ROOT}/evidence/m4_memory_closure_v1/d1_reproduction/d1_result.json"
