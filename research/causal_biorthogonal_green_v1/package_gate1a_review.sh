#!/usr/bin/env bash
set -Eeuo pipefail

# Build a compact, self-contained review package for independent Gate-1A audit.
# No raw 300-s filament realization is included. The package contains enough
# compact data to recompute every source score and truth rank independently.

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH_EXPECTED="research/causal-biorthogonal-green-v1"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
[[ "${BRANCH}" == "${BRANCH_EXPECTED}" ]] || {
  echo "Expected branch ${BRANCH_EXPECTED}; got ${BRANCH}" >&2
  exit 2
}

EVIDENCE="${ROOT}/evidence/causal_biorthogonal_green_v1"
RESEARCH="${ROOT}/research/causal_biorthogonal_green_v1"
OUT_ROOT="${OUT_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
TARGET_ROOT="${TARGET_ROOT:-/home/zyc/c0_5_real_gaden_bank_20260923}"
PACKAGE_ROOT="${PACKAGE_ROOT:-/home/zyc/BIGREEN_GATE1A_REVIEW_20260924}"
ARCHIVE="${ARCHIVE:-/home/zyc/BIGREEN_GATE1A_REVIEW_20260924.tar.gz}"

RESULT="${EVIDENCE}/GATE1A_EXACT_FORWARD_RESULT_20260924.json"
CONTRACT="${OUT_ROOT}/gate1a_contract.json"
SOURCE_BANK="${OUT_ROOT}/source_bank.tsv"

for p in "${RESULT}" "${CONTRACT}" "${SOURCE_BANK}"; do
  [[ -f "${p}" ]] || { echo "missing required file: ${p}" >&2; exit 3; }
done

python3 - "${RESULT}" "${OUT_ROOT}" <<'PY'
import json, sys
from pathlib import Path
import numpy as np

result=Path(sys.argv[1])
out=Path(sys.argv[2])
j=json.loads(result.read_text())
assert int(j["source_count"]) >= 143, j["source_count"]
for seed in (2026092401,2026092402):
    root=out/"predictions"/f"seed_{seed}"
    files=sorted(root.glob("pmfs_*.npy"))
    assert len(files)==int(j["source_count"]), (seed,len(files),j["source_count"])
    for p in files:
        a=np.load(p,allow_pickle=False)
        assert a.shape==(300,), (p,a.shape)
        assert np.isfinite(a).all(), p
        assert (a>=0).all(), p
print("PACKAGE_PREFLIGHT_PASS")
PY

rm -rf "${PACKAGE_ROOT}"
mkdir -p   "${PACKAGE_ROOT}/repo/evidence"   "${PACKAGE_ROOT}/repo/research"   "${PACKAGE_ROOT}/frozen_inputs"   "${PACKAGE_ROOT}/predictions"   "${PACKAGE_ROOT}/targets"   "${PACKAGE_ROOT}/provenance"

# Exact evidence produced by the run.
cp -a "${EVIDENCE}/." "${PACKAGE_ROOT}/repo/evidence/"

# Exact implementation used for the run.
cp -a "${RESEARCH}/." "${PACKAGE_ROOT}/repo/research/"
cp -a "${ROOT}/CODEX_GATE1A_HANDOFF_20260924.md" "${PACKAGE_ROOT}/repo/"
cp -a "${ROOT}/GATE1A_RUN_NOW_20260924.md" "${PACKAGE_ROOT}/repo/"

# Frozen source/probe contracts.
cp -a "${CONTRACT}" "${PACKAGE_ROOT}/frozen_inputs/"
cp -a "${SOURCE_BANK}" "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/hcmc_v1/independent_raw_native_20260922_verified/H02_R2026092212/context_bank/source_update_0001/candidate_manifest.csv"   "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json"   "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank/bank_contract.tsv"   "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank/spatial_export_contract.tsv"   "${PACKAGE_ROOT}/frozen_inputs/"
cp -a   "${ROOT}/evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank/geometry/context_metadata.json"   "${PACKAGE_ROOT}/frozen_inputs/"

# Compact exact forward predictions. Sidecars are included for provenance.
for seed in 2026092401 2026092402; do
  mkdir -p "${PACKAGE_ROOT}/predictions/seed_${seed}"
  cp -a "${OUT_ROOT}/predictions/seed_${seed}/."     "${PACKAGE_ROOT}/predictions/seed_${seed}/"
done

# Independent target A/B spatial fields and manifests. These are compact
# (~0.4 MB each) and allow independent score recomputation.
for cell in S2_W2_A S2_W2_B; do
  mkdir -p "${PACKAGE_ROOT}/targets/${cell}"
  cp -a "${TARGET_ROOT}/${cell}/spatial/concentration.npy"     "${PACKAGE_ROOT}/targets/${cell}/"
  cp -a "${TARGET_ROOT}/${cell}/spatial/metadata.json"     "${PACKAGE_ROOT}/targets/${cell}/"
  cp -a "${TARGET_ROOT}/${cell}/manifest.tsv"     "${PACKAGE_ROOT}/targets/${cell}/"
  [[ -f "${TARGET_ROOT}/${cell}/manifest.sha256" ]] &&     cp -a "${TARGET_ROOT}/${cell}/manifest.sha256"       "${PACKAGE_ROOT}/targets/${cell}/"
done

# Generation/extraction logs are useful for identifying an infrastructure-only
# failure, but are not required for rank recomputation.
if [[ -d "${OUT_ROOT}/logs" ]]; then
  cp -a "${OUT_ROOT}/logs" "${PACKAGE_ROOT}/provenance/"
fi

{
  echo "branch=${BRANCH}"
  echo "head=$(git -C "${ROOT}" rev-parse HEAD)"
  echo "status_begin"
  git -C "${ROOT}" status --short
  echo "status_end"
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${PACKAGE_ROOT}/provenance/git_state.txt"

# Machine-readable compact summary copied without interpretation.
python3 - "${RESULT}" > "${PACKAGE_ROOT}/provenance/result_summary.json" <<'PY'
import json, sys
j=json.load(open(sys.argv[1]))
o={
  "decision":j["decision"],
  "source_count":j["source_count"],
  "truth_source_id":j["truth_source_id"],
  "prediction_seeds":j["prediction_seeds"],
  "targets":{
    k:{
      "truth_primary_score":v["truth_primary_score"],
      "truth_primary_rank":v["truth_primary_rank"],
      "truth_log1p_rank_secondary":v["truth_log1p_rank_secondary"],
      "truth_per_prediction_seed_rank":v["truth_per_prediction_seed_rank"],
      "gate_pass":v["gate_pass"],
      "top10_primary":v["top10_primary"],
    }
    for k,v in j["targets"].items()
  }
}
print(json.dumps(o,indent=2,sort_keys=True))
PY

(
  cd "${PACKAGE_ROOT}"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)

rm -f "${ARCHIVE}"
tar -C "$(dirname "${PACKAGE_ROOT}")" -czf "${ARCHIVE}" "$(basename "${PACKAGE_ROOT}")"

ARCHIVE_SHA="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
ARCHIVE_BYTES="$(stat -c '%s' "${ARCHIVE}")"

printf '%s\n' "BIGREEN_GATE1A_REVIEW_PACKAGE_READY"
printf 'archive=%s\n' "${ARCHIVE}"
printf 'bytes=%s\n' "${ARCHIVE_BYTES}"
printf 'sha256=%s\n' "${ARCHIVE_SHA}"
printf 'head=%s\n' "$(git -C "${ROOT}" rev-parse HEAD)"
