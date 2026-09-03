#!/usr/bin/env bash
set -Eeo pipefail
REPO_ROOT="${REPO_ROOT:?set REPO_ROOT}"
BANK_ROOT_BASE="${BANK_ROOT_BASE:-/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1}"
OUT_ROOT="${OUT_ROOT:?set a fresh OUT_ROOT for bank integrity reports}"
[[ ! -e "${OUT_ROOT}" ]] || { echo "CTPI_BANK_VERIFY_REFUSE_EXISTING_OUT_ROOT=${OUT_ROOT}" >&2; exit 70; }
mkdir -p "${OUT_ROOT}"
for HOUSE in H01 H02 H03; do
  python3 "${REPO_ROOT}/closed_loop/cpir/verify_cpir_bank.py" \
    --root "${BANK_ROOT_BASE}/${HOUSE}" --house "${HOUSE}" \
    --report "${OUT_ROOT}/${HOUSE}_CPIR_LOOKUP_INTEGRITY.json" \
    >"${OUT_ROOT}/${HOUSE}_verify_stdout.json"
  python3 - "${OUT_ROOT}/${HOUSE}_CPIR_LOOKUP_INTEGRITY.json" "${HOUSE}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('verdict')=='CPIR_LOOKUP_INTEGRITY_PASS' and p.get('house')==sys.argv[2]
print('CTPI_BANK_INTEGRITY_'+sys.argv[2]+'=PASS')
PY
done
echo "CTPI_FASTTRACK_ALL_BANKS_INTEGRITY=PASS"
