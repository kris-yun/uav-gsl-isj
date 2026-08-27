#!/usr/bin/env bash
set -Eeuo pipefail

# LEGACY / OPTIONAL DIAGNOSTIC ONLY.
#
# This script was created while H02 post-bank pre-outcome qualification was
# still a prerequisite for closed-loop authorization. That requirement was
# superseded by the frozen V3-ORR direct-closed-loop decision on 2026-08-27.
#
# DO NOT run this script as a prerequisite for V3-ORR integration or the
# confirmatory 3-House x 10-seed OFF/ON matrix.
#
# It remains available only for optional archival/diagnostic materialization.
# Explicit opt-in prevents stale instructions from accidentally consuming VM
# time before the closed-loop matrix.

if [[ "${ALLOW_LEGACY_PREOUTCOME_DIAGNOSTIC:-0}" != "1" ]]; then
  cat >&2 <<'EOF'
STOP: run_h02_reconstructed_postbank_preoutcome.sh is no longer a closed-loop prerequisite.
Current path:
  1. run V3 selftests;
  2. integrate pfdiMode=v3_orr using ObservationResolvedV3.hpp at the existing rawProbabilities branch point;
  3. compile isolated binary;
  4. infrastructure smoke only (House02 seed=314159; do not tune on localization outcome);
  5. freeze git/binary/launch SHA;
  6. run House01/02/03 x seeds 0..9 x OFF/ON, 300 s, STEPS_SOURCE_UPDATE=3.
Read: docs/CODEX_V3_ORR_INTEGRATE_AND_RUN_20260827.md

To run this old materialization solely for archival diagnostics, set:
  ALLOW_LEGACY_PREOUTCOME_DIAGNOSTIC=1
EOF
  exit 3
fi

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

echo "H02_RECONSTRUCTED_POSTBANK_PREOUTCOME=PASS_OPTIONAL_DIAGNOSTIC"
echo "OUT=$OUT"
