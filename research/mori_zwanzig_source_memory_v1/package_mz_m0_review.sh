#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH_EXPECTED="research/mori-zwanzig-source-memory-v1"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
[[ "${BRANCH}" == "${BRANCH_EXPECTED}" ]] || {
  echo "Expected branch ${BRANCH_EXPECTED}; got ${BRANCH}" >&2
  exit 2
}

RESEARCH="${ROOT}/research/mori_zwanzig_source_memory_v1"
EVIDENCE="${ROOT}/evidence/mori_zwanzig_source_memory_v1"
OUT_ROOT="${OUT_ROOT:-/home/zyc/mz_m0_dense_history_20260924}"
PACKAGE_ROOT="${PACKAGE_ROOT:-/home/zyc/MZ_M0_REVIEW_20260924}"
ARCHIVE="${ARCHIVE:-/home/zyc/MZ_M0_REVIEW_20260924.tar.gz}"

RESULT="${EVIDENCE}/MZ_M0_RESULT_20260924.json"
DETAIL="${EVIDENCE}/MZ_M0_ALL_TESTS_20260924.csv"

for p in   "${RESULT}"   "${DETAIL}"   "${OUT_ROOT}/m0_source_bank.tsv"   "${OUT_ROOT}/m0_source_selection.json"   "${OUT_ROOT}/parent_bank/gate1a_contract.json"; do
  [[ -f "${p}" ]] || { echo "missing required file: ${p}" >&2; exit 3; }
done

python3 - "${RESULT}" "${OUT_ROOT}" <<'PY'
import json, sys
from pathlib import Path
import numpy as np
result=Path(sys.argv[1])
root=Path(sys.argv[2])
j=json.loads(result.read_text())
assert int(j["source_count"]) == 180
assert j["decision"] in {
    "MZ_M0_PASS_MEMORY_IS_LOAD_BEARING",
    "MZ_M0_FAIL_STOP_MEMORY_MAINLINE",
}
for seed in (2026092403,2026092404,2026092405):
    files=sorted((root/"histories"/f"seed_{seed}").glob("pmfs_*.npz"))
    assert len(files)==180, (seed,len(files))
    for p in files:
        with np.load(p,allow_pickle=False) as z:
            x=z["probe_ppm"]; t=z["time_s"]; it=z["iteration_index"]
        assert x.ndim==2 and x.shape[1]==30 and x.shape[0]>=500, (p,x.shape)
        assert t.shape==(x.shape[0],) and it.shape==(x.shape[0],)
        assert np.isfinite(x).all() and (x>=0).all()
print("PACKAGE_PREFLIGHT_PASS")
PY

rm -rf "${PACKAGE_ROOT}"
mkdir -p   "${PACKAGE_ROOT}/repo/research"   "${PACKAGE_ROOT}/repo/evidence"   "${PACKAGE_ROOT}/frozen_inputs"   "${PACKAGE_ROOT}/histories"   "${PACKAGE_ROOT}/provenance"

cp -a "${RESEARCH}/." "${PACKAGE_ROOT}/repo/research/"
cp -a "${EVIDENCE}/." "${PACKAGE_ROOT}/repo/evidence/"
cp -a "${ROOT}/CODEX_MZ_M0_HANDOFF_20260924.md" "${PACKAGE_ROOT}/repo/" 2>/dev/null || true

cp -a "${OUT_ROOT}/m0_source_bank.tsv" "${PACKAGE_ROOT}/frozen_inputs/"
cp -a "${OUT_ROOT}/m0_source_selection.json" "${PACKAGE_ROOT}/frozen_inputs/"
cp -a "${OUT_ROOT}/parent_bank/source_bank.tsv" "${PACKAGE_ROOT}/frozen_inputs/parent_630_source_bank.tsv"
cp -a "${OUT_ROOT}/parent_bank/gate1a_contract.json" "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json"   "${PACKAGE_ROOT}/frozen_inputs/"

for seed in 2026092403 2026092404 2026092405; do
  mkdir -p "${PACKAGE_ROOT}/histories/seed_${seed}"
  cp -a "${OUT_ROOT}/histories/seed_${seed}/."     "${PACKAGE_ROOT}/histories/seed_${seed}/"
done

{
  echo "branch=${BRANCH}"
  echo "head=$(git -C "${ROOT}" rev-parse HEAD)"
  echo "status_begin"
  git -C "${ROOT}" status --short
  echo "status_end"
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${PACKAGE_ROOT}/provenance/git_state.txt"

(
  cd "${PACKAGE_ROOT}"
  find . -type f ! -name SHA256SUMS.txt -print0     | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)

rm -f "${ARCHIVE}"
tar -C "$(dirname "${PACKAGE_ROOT}")" -czf "${ARCHIVE}" "$(basename "${PACKAGE_ROOT}")"

ARCHIVE_SHA="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
ARCHIVE_BYTES="$(stat -c '%s' "${ARCHIVE}")"

printf '%s\n' "MZ_M0_REVIEW_PACKAGE_READY"
printf 'archive=%s\n' "${ARCHIVE}"
printf 'bytes=%s\n' "${ARCHIVE_BYTES}"
printf 'sha256=%s\n' "${ARCHIVE_SHA}"
printf 'head=%s\n' "$(git -C "${ROOT}" rev-parse HEAD)"
