#!/usr/bin/env bash
set -Eeuo pipefail

PHASE_ROOT="${PHASE_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_PHASE0_20260902}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_CONFIRM_20260902_R1}"
MANIFEST="$PHASE_ROOT/SOURCE_INTERVENTION_WORLD_MANIFEST.json"
RUNTIME="$PHASE_ROOT/GENERATOR_RUNTIME_IDENTITY.json"
AUTHORIZATION="$PHASE_ROOT/CAL_FREEZE_AUTHORIZATION.json"
PREGEN_REPORT="$PHASE_ROOT/PREGEN_AUDIT_REPORT.json"
SELECTION="$PHASE_ROOT/CONTROLLED_SOURCE_SELECTION.json"
FORECAST_CODE="$PHASE_ROOT/ctpi_m2_source_intervention_forecast.py"
CAL_TABLE="$PHASE_ROOT/M2_CALIBRATION_TABLE.json"
CAL_REPORT="$PHASE_ROOT/CAL_FIT_REPORT.json"
CAL_RECORDS_CSV="$PHASE_ROOT/CAL_RECORDS.csv"
CAL_RECORDS_NPZ="$PHASE_ROOT/CAL_RECORDS.npz"
CAL_BATCH_MARKER="$PHASE_ROOT/CAL_BATCH_PASS"
MATERIALIZER="$PHASE_ROOT/ctpi_m2_materialize_world.py"
WRAPPER="$PHASE_ROOT/run_ctpi_m2_world_vm.sh"

for path in "$MANIFEST" "$RUNTIME" "$AUTHORIZATION" "$PREGEN_REPORT" "$SELECTION" \
  "$FORECAST_CODE" "$CAL_TABLE" "$CAL_REPORT" "$CAL_RECORDS_CSV" \
  "$CAL_RECORDS_NPZ" "$CAL_BATCH_MARKER" "$MATERIALIZER" "$WRAPPER"; do
  test -f "$path" || { echo "CTPI_M2_CONFIRM_INPUT_MISSING=$path" >&2; exit 2; }
done
python3 - "$AUTHORIZATION" "$PREGEN_REPORT" "$MANIFEST" "$SELECTION" \
  "$FORECAST_CODE" "$CAL_TABLE" "$CAL_REPORT" "$CAL_RECORDS_CSV" \
  "$CAL_RECORDS_NPZ" "$CAL_BATCH_MARKER" <<'PY'
import hashlib,json,re,sys

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

(authorization_path,pregen_path,manifest_path,selection_path,forecast_path,
 table_path,cal_report_path,cal_csv_path,cal_npz_path,cal_marker_path)=sys.argv[1:]
d=json.load(open(authorization_path))
if d.get("contract")!="CTPI_M2_SOURCE_INTERVENTION_CONFIRM_AUTHORIZATION_V1":
    raise SystemExit("CTPI_M2_CONFIRM_AUTHORIZATION_CONTRACT")
if d.get("CTPI_M2_SOURCE_INTERVENTION_PREGEN")!="PASS" or d.get("M2_CAL_FREEZE")!="PASS":
    raise SystemExit("CTPI_M2_CONFIRM_NOT_AUTHORIZED")
if d.get("confirm_generated_or_opened_before_freeze") is not False or d.get("formula_tuning_on_confirm_allowed") is not False:
    raise SystemExit("CTPI_M2_CONFIRM_FREEZE_BOUNDARY")
if not re.fullmatch(r"[0-9a-f]{40}",str(d.get("calibration_artifact_commit",""))):
    raise SystemExit("CTPI_M2_CONFIRM_CAL_COMMIT")
expected={
    pregen_path:"pregen_audit_report_sha256",
    manifest_path:"world_manifest_sha256",
    selection_path:"source_selection_sha256",
    forecast_path:"forecast_code_sha256",
    table_path:"m2_table_sha256",
    cal_report_path:"cal_fit_report_sha256",
    cal_csv_path:"cal_records_csv_sha256",
    cal_npz_path:"cal_records_npz_sha256",
}
for path,key in expected.items():
    if sha(path)!=d.get(key):
        raise SystemExit(f"CTPI_M2_CONFIRM_FROZEN_HASH:{key}")
pregen=json.load(open(pregen_path))
if not pregen.get("pass") or pregen.get("verdict")!="CTPI_M2_SOURCE_INTERVENTION_PREGEN=PASS":
    raise SystemExit("CTPI_M2_CONFIRM_PREGEN_REPORT")
cal=json.load(open(cal_report_path))
if not cal.get("pass") or cal.get("verdict")!="CTPI_M2_SOURCE_INTERVENTION_CAL_FREEZE=PASS":
    raise SystemExit("CTPI_M2_CONFIRM_CAL_REPORT")
if open(cal_marker_path,encoding="utf-8").read().strip()!=d.get("cal_batch_marker"):
    raise SystemExit("CTPI_M2_CONFIRM_CAL_BATCH_MARKER")
print("CTPI_M2_CONFIRM_FROZEN_INPUTS=PASS")
PY
test ! -e "$OUTPUT_ROOT" || { echo "CTPI_M2_CONFIRM_REFUSE_STALE_ROOT=$OUTPUT_ROOT" >&2; exit 3; }
mkdir "$OUTPUT_ROOT"

mapfile -t WORLD_IDS < <(python3 - "$MANIFEST" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ids=[r["world_id"] for r in d["formal_worlds"] if r["set"]=="M2_CONFIRM"]
if len(ids)!=30 or len(set(ids))!=30:
    raise SystemExit("CTPI_M2_CONFIRM_WORLD_ID_CONTRACT")
print("\n".join(ids))
PY
)

printf 'CTPI_M2_CONFIRM_BATCH_START=30\n'
for index in "${!WORLD_IDS[@]}"; do
  world_id="${WORLD_IDS[$index]}"
  ordinal=$((index + 1))
  printf 'CTPI_M2_CONFIRM_WORLD_START=%d/30:%s\n' "$ordinal" "$world_id"
  "$WRAPPER" "$MATERIALIZER" \
    --world-manifest "$MANIFEST" \
    --runtime-report "$RUNTIME" \
    --authorization "$AUTHORIZATION" \
    --world-id "$world_id" \
    --output "$OUTPUT_ROOT/$world_id" \
    >"$OUTPUT_ROOT/${world_id}.log" 2>&1
  test -f "$OUTPUT_ROOT/$world_id/PASS"
  printf 'CTPI_M2_CONFIRM_WORLD_PASS=%d/30:%s\n' "$ordinal" "$world_id"
done

printf 'CTPI_M2_CONFIRM_BATCH=PASS worlds=30\n' | tee "$OUTPUT_ROOT/CONFIRM_BATCH_PASS"
