#!/usr/bin/env bash
set -euo pipefail

: "${RUN_ROOT:?Set RUN_ROOT to the directory containing the six accepted run directories}"
: "${REPLAY_BIN:?Set REPLAY_BIN to the built native_candidate_replay executable}"
OUT_ROOT="${OUT_ROOT:-$PWD/_staging/TPT_FIRST_PASSAGE_LAYER1_20260923}"
mkdir -p "$OUT_ROOT"

python3 -m py_compile   reference/verify_native_candidate_trace.py   reference/tpt_first_passage_screen.py   reference/aggregate_tpt_first_passage_layer1.py

cases=(
  "H01_R2026092201:-0.40:-2.90"
  "H01_R2026092202:-0.40:-2.90"
  "H02_R2026092211:0.00:-1.00"
  "H02_R2026092212:0.00:-1.00"
  "H03_R2026092221:-0.45:1.90"
  "H03_R2026092222:-0.45:1.90"
)

for spec in "${cases[@]}"; do
  IFS=: read -r run truth_x truth_y <<<"$spec"
  run_dir="$RUN_ROOT/$run"
  out="$OUT_ROOT/$run"
  trace="$out/trace"
  mkdir -p "$out"
  rm -rf "$trace"

  test -f "$run_dir/runtime_manifest.json"
  test -f "$run_dir/context_bank/source_update_timing.csv"
  test -f "$run_dir/context_bank/source_update_0001/candidate_manifest.csv"

  "$REPLAY_BIN" "$run_dir" "$out/parity_1.csv" 1
  "$REPLAY_BIN" "$run_dir" "$out/parity_10.csv" 10
  "$REPLAY_BIN" "$run_dir" "$out/parity_all.csv" all
  "$REPLAY_BIN" "$run_dir" "$out/parity_trace_all.csv" all "$trace"

  python3 reference/verify_native_candidate_trace.py     "$trace" "$out/parity_trace_all.csv" "$out/trace_manifest.json"

  python3 reference/tpt_first_passage_screen.py     --run-dir "$run_dir"     --trace-csv "$trace/occupied_cells.csv"     --candidate-csv-out "$out/tpt_candidate_scores.csv"     --json-out "$out/tpt_first_passage.json"     --truth-x "$truth_x" --truth-y "$truth_y"

  # Retain the full transition/position trace outside Git history for later
  # reactive-flux analysis, while also producing a compact occupancy artifact.
  if command -v zstd >/dev/null 2>&1; then
    zstd -q -f -19 "$trace/occupied_cells.csv" -o "$out/occupied_cells.csv.zst"
  fi
  (
    cd "$out"
    sha256sum parity_1.csv parity_10.csv parity_all.csv parity_trace_all.csv       trace_manifest.json tpt_candidate_scores.csv tpt_first_passage.json       > SHA256SUMS.txt
  )

done

set +e
python3 reference/aggregate_tpt_first_passage_layer1.py   "$OUT_ROOT" --json-out "$OUT_ROOT/tpt_layer1_aggregate.json"
rc=$?
set -e

echo "TPT_LAYER1_AGGREGATE_RC=$rc"
echo "OUT_ROOT=$OUT_ROOT"
exit "$rc"
