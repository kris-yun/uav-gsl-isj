#!/usr/bin/env bash
set -Eeuo pipefail
CODE=/home/zyc/pmfs_evidence_pseudoreplication_20260926/code
BASE=/home/zyc/pmfs_evidence_pseudoreplication_20260926
export PYTHONDONTWRITEBYTECODE=1
python3 "$CODE/prepare_source_blind_inputs.py"
for NAME in result deterministic_repeat; do
  python3 "$CODE/score_frozen_r1_maps.py" \
    --snapshot-dir "$BASE/inputs" \
    --c-scores "$BASE/inputs/C_candidate_scores.csv" \
    --maps-dir "$BASE/inputs/maps" \
    --historical-manifest "$BASE/inputs/r1_scores_frozen_manifest.json" \
    --out "$BASE/$NAME"
done
for NAME in candidate_scores.csv event_support_audit.json native_parity.json SCORES_SHA256.txt; do
  cmp "$BASE/result/$NAME" "$BASE/deterministic_repeat/$NAME"
done
echo SOURCE_BLIND_DETERMINISTIC_REPEAT_PASS
