#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED="research/source-lineage-lagrangian-v2"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
[[ "${BRANCH}" == "${EXPECTED}" ]] || {
  echo "Expected branch ${EXPECTED}; got ${BRANCH}" >&2
  exit 2
}

RAW_BANK="${RAW_BANK:-/home/zyc/c0_5_real_gaden_bank_20260923}"
CACHE="${CACHE:-/home/zyc/sll_v2_lineage_bank_20260924}"
EVIDENCE="${ROOT}/evidence/source_lineage_lagrangian_v2"
RESEARCH="${ROOT}/research/source_lineage_lagrangian_v2"

[[ -f "${RAW_BANK}/bank_contract.tsv" ]] || {
  echo "Missing raw bank: ${RAW_BANK}" >&2; exit 3;
}
[[ ! -e "${CACHE}" ]] || {
  echo "Refuse to overwrite lineage cache: ${CACHE}" >&2; exit 4;
}
mkdir -p "${EVIDENCE}"

python3 -m py_compile   "${RESEARCH}/export_gaden_filaments.py"   "${RESEARCH}/reconstruct_filament_lineage.py"   "${RESEARCH}/export_gaden_wind_3d.py"   "${RESEARCH}/export_house02_lineage_bank.py"   "${RESEARCH}/l1_filament_transition_audit.py"

python3 "${RESEARCH}/test_export_gaden_filaments.py"

python3 "${RESEARCH}/export_house02_lineage_bank.py"   --bank-root "${RAW_BANK}"   --repo-root "${ROOT}"   --out "${CACHE}"   | tee "${EVIDENCE}/SLL_V2_EXPORT_20260924.log"

OCCUPANCY="$(awk -F '\t' '$1=="occupancy"{print $2}' "${RAW_BANK}/bank_contract.tsv")"
RESULT="${EVIDENCE}/SLL_V2_L1_RESULT_20260924.json"

python3 "${RESEARCH}/l1_filament_transition_audit.py"   --lineage-root "${CACHE}"   --wind-root "${CACHE}/wind3d"   --occupancy "${OCCUPANCY}"   --out "${RESULT}"   --max-pairs-per-cell 8000   --sensor-z 0.20   | tee "${EVIDENCE}/SLL_V2_L1_20260924.log"

{
  git -C "${ROOT}" rev-parse HEAD
  sha256sum     "${RESEARCH}/export_gaden_filaments.py"     "${RESEARCH}/reconstruct_filament_lineage.py"     "${RESEARCH}/export_gaden_wind_3d.py"     "${RESEARCH}/l1_filament_transition_audit.py"     "${CACHE}/export_manifest.json"     "${RESULT}"     "${RESULT%.json}.model.npz"
} > "${EVIDENCE}/SLL_V2_L1_SHA256_20260924.txt"

cat "${RESULT}"
