#!/usr/bin/env bash
set -Eeuo pipefail

HOUSE="${HOUSE:?set HOUSE}"
SEED="${SEED:?set fresh SEED}"
ARM="${ARM:?set ARM=off or on}"
DOMAIN_ID="${DOMAIN_ID:?set unique DOMAIN_ID}"
[[ "$ARM" == off || "$ARM" == on ]]

freeze=/home/zyc/meaci_v12_m_freeze_20260825
binary="$freeze/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
runner="$freeze/run_meaci_case_20260824.sh"
launch="$freeze/launch/vgr_gsl_pmfs_pfdi.launch.py"
expected_binary=100ca267c1dc6f098f1080f669733bf7cf655d8a05ce8d5afe3ef9b9458a51ce
expected_runner=78404eff2fe205d01d62b0f4273f3b3568c73a7313c12aa47c6827d88b803484
expected_launch=0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9
run_root=/home/zyc/meaci_v12_generalization_20260825_r1
RUN_ROOT="$run_root"

[[ "$(sha256sum "$binary" | awk '{print $1}')" == "$expected_binary" ]]
[[ "$(sha256sum "$runner" | awk '{print $1}')" == "$expected_runner" ]]
[[ "$(sha256sum "$launch" | awk '{print $1}')" == "$expected_launch" ]]

if [[ "$ARM" == on ]]; then
  PFDI_MODE=rc_sd_tfei_v12
  bank="${freeze_bank_path:?set freeze_bank_path for ON arm}"
  expected_bank="${freeze_bank_sha256:?set freeze_bank_sha256 for ON arm}"
  [[ "$bank" = /* ]]
  [[ "$(sha256sum "$bank" | awk '{print $1}')" == "$expected_bank" ]]
  export PFDI_V12_RESPONSE_BANK_PATH="$bank"
else
  PFDI_MODE=off
  unset PFDI_V12_RESPONSE_BANK_PATH || true
fi
unset PFDI_V12_BUILD_RESPONSE_BANK || true

run_dir="$run_root/${HOUSE}_seed${SEED}_${ARM}_${PFDI_MODE}"
[[ ! -e "$run_dir" ]]
mkdir -p "$run_root"

export HOUSE SEED ARM RUN_ROOT PFDI_MODE DOMAIN_ID
export RUN_ID="V12_M_HELDOUT_${HOUSE}_S${SEED}_${ARM}"
export PFDI_INSTALL_ROOT="$freeze"
export RUN_CONTRACT=V12_M_HELDOUT_FRESH_SEED_FULL300_V1
export TIMEOUT_SEC=300.0 OUTER_DEADLINE_SEC=480
export TARGET_SOURCE_UPDATES=0 TARGET_ACCEPTED_UPDATES=0
export STEPS_SOURCE_UPDATE=3 TADM_REPLICAS=8
export POSTERIOR_GUIDANCE_WEIGHT=0 REALTIME_FACTOR=1.0
export EVALUATOR_SCRIPT=/nonexistent/v12_defer_truth_evaluation.py

"$runner"

test -s "$run_dir/run_status.json"
test -s "$run_dir/runtime_manifest.json"
python3 - "$run_dir" "$expected_binary" "$ARM" <<'PY'
import csv, json, pathlib, sys
run = pathlib.Path(sys.argv[1])
expected_binary, arm = sys.argv[2], sys.argv[3]
status = json.loads((run / "run_status.json").read_text())
manifest = json.loads((run / "runtime_manifest.json").read_text())
assert status["status"] == "time_budget_timeout", status
assert manifest["algorithm_sha256"] == expected_binary, manifest
assert manifest["contract"] == "V12_M_HELDOUT_FRESH_SEED_FULL300_V1", manifest
assert manifest["timeout_sec"] == "300.0", manifest
assert manifest["target_source_updates"] == "0"
assert manifest["target_accepted_updates"] == "0"
updates = sorted((run / "context_bank").glob("source_update_*/source_posterior.csv"))
assert updates, "no complete source update posterior"
if arm == "on":
    contract = json.loads((run / "tadm" / "tadm_contract.json").read_text())
    assert contract["method"] == "V12-M-RC-SD-TFEI", contract
    rows = list(csv.DictReader((run / "tadm" / "v12_update_summary.csv").open()))
    assert rows and all(r["status"] == "PASS" for r in rows), rows
    bank_rows = list(csv.DictReader((run / "tadm" / "v12_response_bank_runtime.csv").open()))
    assert bank_rows and bank_rows[0]["loaded"] == "1" and bank_rows[0]["built"] == "0", bank_rows
print("V12_CASE_INTEGRITY_PASS", run)
PY
