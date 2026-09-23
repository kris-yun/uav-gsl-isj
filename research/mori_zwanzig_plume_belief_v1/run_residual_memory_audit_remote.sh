#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED_BRANCH="research/mori-zwanzig-plume-belief-v1"
BRANCH="$(git -C "${ROOT}" branch --show-current)"

[[ "${BRANCH}" == "${EXPECTED_BRANCH}" ]] || {
  echo "Expected ${EXPECTED_BRANCH}; got ${BRANCH}" >&2
  exit 2
}

RESEARCH="${ROOT}/research/mori_zwanzig_plume_belief_v1"
EVIDENCE="${ROOT}/evidence/mori_zwanzig_plume_belief_v1"
DYNAMIC="${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
D0OUT="${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923"
OUT="${EVIDENCE}/MZ_PBD_RESIDUAL_MEMORY_AUDIT_20260923.json"

for p in \
  "${DYNAMIC}/wind_sequence_manifest.json" \
  "${DYNAMIC}/wind_W1_sequence_z0p20.npy" \
  "${DYNAMIC}/wind_W2_sequence_z0p20.npy" \
  "${D0OUT}/train_manifest.json" \
  "${D0OUT}/m4v3_seed1729.pt" \
  "${D0OUT}/m4v3_seed2718.pt"; do
  [[ -f "${p}" ]] || { echo "missing: ${p}" >&2; exit 3; }
done

[[ ! -e "${OUT}" ]] || {
  echo "Refuse to overwrite ${OUT}" >&2
  exit 4
}

mkdir -p "${EVIDENCE}"
PYTHON="${PYTHON:-python3}"
"${PYTHON}" "${RESEARCH}/mz_pbd_residual_memory_audit.py" \
  --repo-root "${ROOT}" \
  --dynamic-wind "${DYNAMIC}" \
  --d0-out "${D0OUT}" \
  --output "${OUT}" \
  | tee "${EVIDENCE}/MZ_PBD_RESIDUAL_MEMORY_AUDIT_20260923.log"

sha256sum \
  "${RESEARCH}/mz_pbd_residual_memory_audit.py" \
  "${OUT}" \
  > "${EVIDENCE}/MZ_PBD_RESIDUAL_MEMORY_AUDIT_SHA256_20260923.txt"

cat "${OUT}"
