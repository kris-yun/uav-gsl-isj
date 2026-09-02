#!/usr/bin/env bash
set -Eeuo pipefail

PHASE_ROOT="${PHASE_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_PHASE0_20260902}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/home/zyc/CTPI_M2_SOURCE_INTERVENTION_CAL_20260902_R1}"
MANIFEST="$PHASE_ROOT/SOURCE_INTERVENTION_WORLD_MANIFEST.json"
RUNTIME="$PHASE_ROOT/GENERATOR_RUNTIME_IDENTITY.json"
AUTHORIZATION="$PHASE_ROOT/PREGEN_AUDIT_REPORT.json"
MATERIALIZER="$PHASE_ROOT/ctpi_m2_materialize_world.py"
WRAPPER="$PHASE_ROOT/run_ctpi_m2_world_vm.sh"

for path in "$MANIFEST" "$RUNTIME" "$AUTHORIZATION" "$MATERIALIZER" "$WRAPPER"; do
  test -f "$path" || { echo "CTPI_M2_CAL_INPUT_MISSING=$path" >&2; exit 2; }
done
test ! -e "$OUTPUT_ROOT" || { echo "CTPI_M2_CAL_REFUSE_STALE_ROOT=$OUTPUT_ROOT" >&2; exit 3; }
mkdir "$OUTPUT_ROOT"

mapfile -t WORLD_IDS < <(python3 - "$MANIFEST" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ids=[r["world_id"] for r in d["formal_worlds"] if r["set"]=="M2_CAL"]
if len(ids)!=30 or len(set(ids))!=30:
    raise SystemExit("CTPI_M2_CAL_WORLD_ID_CONTRACT")
print("\n".join(ids))
PY
)

printf 'CTPI_M2_CAL_BATCH_START=30\n'
for index in "${!WORLD_IDS[@]}"; do
  world_id="${WORLD_IDS[$index]}"
  ordinal=$((index + 1))
  printf 'CTPI_M2_CAL_WORLD_START=%d/30:%s\n' "$ordinal" "$world_id"
  "$WRAPPER" "$MATERIALIZER" \
    --world-manifest "$MANIFEST" \
    --runtime-report "$RUNTIME" \
    --authorization "$AUTHORIZATION" \
    --world-id "$world_id" \
    --output "$OUTPUT_ROOT/$world_id" \
    >"$OUTPUT_ROOT/${world_id}.log" 2>&1
  test -f "$OUTPUT_ROOT/$world_id/PASS"
  printf 'CTPI_M2_CAL_WORLD_PASS=%d/30:%s\n' "$ordinal" "$world_id"
done

printf 'CTPI_M2_CAL_BATCH=PASS worlds=30\n' | tee "$OUTPUT_ROOT/CAL_BATCH_PASS"
