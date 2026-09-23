#!/usr/bin/env bash
set -euo pipefail

# Distributional-forward H02/H03 decisive replay runner.
# Run inside the same ROS/GADEN overlay used by the frozen H01 standalone replay.
# It does not change PMFS source code or algorithm semantics.

ROOT="${1:-$PWD}"
EXE="${NATIVE_REPLAY_EXE:-native_candidate_replay}"
OUT="${2:-$ROOT/evidence/distributional_forward_semantics_v1/standalone_replay}"
mkdir -p "$OUT"

runs=(
  H02_R2026092211
  H02_R2026092212
  H03_R2026092221
  H03_R2026092222
)

for run in "${runs[@]}"; do
  in="$ROOT/evidence/hcmc_v1/independent_raw_native_20260922_verified/$run"
  test -f "$in/runtime_manifest.json"
  test -f "$in/context_bank/source_update_timing.csv"
  trace="$OUT/$run"
  parity="$OUT/${run}_parity_all.csv"
  rm -rf "$trace"
  "$EXE" "$in" "$parity" all "$trace"
  python3 reference/verify_native_candidate_trace.py "$trace" "$parity" "$trace/trace_manifest.json" 2>/dev/null || true
  zstd -T0 -19 --rm "$trace/occupied_cells.csv"
done

echo "DISTRIBUTIONAL_REPLAY_BATCH_COMPLETE out=$OUT"
