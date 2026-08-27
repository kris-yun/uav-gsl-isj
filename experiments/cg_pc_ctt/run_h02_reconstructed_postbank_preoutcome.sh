#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

BANK_ROOT=${H02_RECONSTRUCTED_ROOT:-/home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_20260827_r1}
CONTEXT_MANIFEST=${H02_CONTEXT_MANIFEST:-/tmp/h02_reconstructed_v1_20260827/H02_RECONSTRUCTED_CONTEXT_MANIFEST.csv}
VERIFY_JSON=${H02_VERIFY_JSON:-$BANK_ROOT/VERIFY.json}
OUT=${H02_PREOUTCOME_OUT:-/home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_PREOUTCOME_20260827}

[[ -d "$BANK_ROOT/banks" ]] || { echo "missing bank root: $BANK_ROOT" >&2; exit 2; }
[[ -f "$CONTEXT_MANIFEST" ]] || { echo "missing context manifest: $CONTEXT_MANIFEST" >&2; exit 2; }
[[ -f "$VERIFY_JSON" ]] || { echo "missing VERIFY.json: $VERIFY_JSON (set H02_VERIFY_JSON)" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refuse overwrite: $OUT" >&2; exit 2; }
mkdir -p "$OUT"

python3 "$HERE/qualify_h02_reconstructed_analysis_contract.py" \
  "$CONTEXT_MANIFEST" "$VERIFY_JSON" \
  --out-csv "$OUT/H02_RECONSTRUCTED_ANALYSIS_MANIFEST.csv" \
  --out-json "$OUT/H02_RECONSTRUCTED_ANALYSIS_CONTRACT.json"

python3 "$HERE/materialize_h02_reconstructed_ctt_tensor.py" \
  "$BANK_ROOT" "$OUT/H02_RECONSTRUCTED_ANALYSIS_MANIFEST.csv" \
  --out-dir "$OUT/tensors"

python3 "$HERE/audit_h02_reconstructed_transport_resolution.py" \
  "$OUT/tensors" \
  --out "$OUT/H02_TRANSPORT_RESOLUTION_AUDIT.json"

python3 "$HERE/discover_h02_observation_event_support.py" \
  "$OUT/H02_RECONSTRUCTED_ANALYSIS_MANIFEST.csv" \
  --out "$OUT/H02_EVENT_SUPPORT_DISCOVERY.json"

sha256sum \
  "$OUT/H02_RECONSTRUCTED_ANALYSIS_MANIFEST.csv" \
  "$OUT/H02_RECONSTRUCTED_ANALYSIS_CONTRACT.json" \
  "$OUT/tensors/MANIFEST.json" \
  "$OUT/H02_TRANSPORT_RESOLUTION_AUDIT.json" \
  "$OUT/H02_EVENT_SUPPORT_DISCOVERY.json" \
  > "$OUT/SHA256SUMS.txt"

echo "H02_RECONSTRUCTED_POSTBANK_PREOUTCOME=PASS"
echo "OUT=$OUT"
