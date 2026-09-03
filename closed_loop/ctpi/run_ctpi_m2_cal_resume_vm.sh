#!/usr/bin/env bash
set -Eeuo pipefail

PHASE_ROOT="${PHASE_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_PHASE0_20260902}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_CAL_20260902_R1}"
MANIFEST="$PHASE_ROOT/SOURCE_INTERVENTION_WORLD_MANIFEST.json"
RUNTIME="$PHASE_ROOT/GENERATOR_RUNTIME_IDENTITY.json"
AUTHORIZATION="$PHASE_ROOT/PREGEN_AUDIT_REPORT.json"
MATERIALIZER="$PHASE_ROOT/ctpi_m2_materialize_world.py"
WRAPPER="$PHASE_ROOT/run_ctpi_m2_world_vm.sh"

test -d "$OUTPUT_ROOT"
test ! -e "$OUTPUT_ROOT/CAL_BATCH_PASS"

# Reuse is allowed only after every existing world is cryptographically linked
# to the frozen manifests and has a clean PASS audit.  This is recovery from an
# SSH stdout disconnect, not stale status reuse or a scientific rerun.
MISSING_FILE="$OUTPUT_ROOT/VALIDATED_RESUME_MISSING.txt"
test ! -e "$MISSING_FILE"
python3 - "$MANIFEST" "$RUNTIME" "$OUTPUT_ROOT" >"$MISSING_FILE" <<'PY'
import hashlib,json,sys
from pathlib import Path
manifest_path,runtime_path,root=map(Path,sys.argv[1:])
manifest=json.load(open(manifest_path)); expected=[r["world_id"] for r in manifest["formal_worlds"] if r["set"]=="M2_CAL"]
mh=hashlib.sha256(manifest_path.read_bytes()).hexdigest(); rh=hashlib.sha256(runtime_path.read_bytes()).hexdigest()
if len(expected)!=30 or len(set(expected))!=30: raise SystemExit("CTPI_M2_CAL_RESUME_EXPECTED_IDS")
for world_id in expected:
    d=root/world_id
    if not d.exists(): print(world_id); continue
    if not (d/"PASS").is_file() or (d/"FAIL").exists(): raise SystemExit(f"CTPI_M2_CAL_RESUME_INVALID_STATUS:{world_id}")
    a=json.load(open(d/"WORLD_AUDIT.json"))
    checks=[a.get("pass"),a.get("world_id")==world_id,a.get("world_manifest_sha256")==mh,
            a.get("runtime_report_sha256")==rh,a.get("bank_unchanged"),
            a.get("physical_samples")==1500,a.get("forward_sensor_samples")==1502,
            a.get("completed_stop_events")==15,a.get("visible_stop_counts")==[3,6,9,12,15],
            a.get("native_invocation_count")==1]
    if not all(checks): raise SystemExit(f"CTPI_M2_CAL_RESUME_AUDIT:{world_id}")
PY
mapfile -t MISSING_IDS <"$MISSING_FILE"

printf 'CTPI_M2_CAL_VALIDATED_RESUME_MISSING=%d\n' "${#MISSING_IDS[@]}"
for index in "${!MISSING_IDS[@]}"; do
  world_id="${MISSING_IDS[$index]}"
  printf 'CTPI_M2_CAL_RESUME_WORLD_START=%d/%d:%s\n' "$((index + 1))" "${#MISSING_IDS[@]}" "$world_id"
  "$WRAPPER" "$MATERIALIZER" \
    --world-manifest "$MANIFEST" --runtime-report "$RUNTIME" \
    --authorization "$AUTHORIZATION" --world-id "$world_id" \
    --output "$OUTPUT_ROOT/$world_id" >"$OUTPUT_ROOT/${world_id}.log" 2>&1
  test -f "$OUTPUT_ROOT/$world_id/PASS"
  printf 'CTPI_M2_CAL_RESUME_WORLD_PASS=%s\n' "$world_id"
done

python3 - "$MANIFEST" "$OUTPUT_ROOT" <<'PY'
import json,sys
from pathlib import Path
m=json.load(open(sys.argv[1]));root=Path(sys.argv[2]);ids=[r["world_id"] for r in m["formal_worlds"] if r["set"]=="M2_CAL"]
if len(ids)!=30 or any(not (root/i/"PASS").is_file() or (root/i/"FAIL").exists() for i in ids):
    raise SystemExit("CTPI_M2_CAL_RESUME_FINAL_COUNT")
PY
printf 'CTPI_M2_CAL_BATCH=PASS worlds=30\n' | tee "$OUTPUT_ROOT/CAL_BATCH_PASS"
