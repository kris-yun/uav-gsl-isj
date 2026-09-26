#!/usr/bin/env bash
set -Ee -o pipefail
ROOT="$(git rev-parse --show-toplevel)"
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -u
BIN=/home/zyc/persistent_source_pmfs_build_20260926/persistent_source_r1_replay
INPUT=/home/zyc/persistent_source_r1_source_blind_20260926
OUTPUT=/home/zyc/persistent_source_pmfs_r1_20260926
REPEAT=/home/zyc/persistent_source_pmfs_r1_repeat_20260926
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
"$BIN" "$INPUT" "$OUTPUT"
(
  cd "$OUTPUT"
  sha256sum candidate_summary.csv scores_long.csv persistent_source_samples.csv source_blind_audit.txt \
    "$BIN" "$ROOT/ros2_package/tools/persistent_source_r1_replay.cpp" \
    > SCORES_SHA256.txt
  sha256sum -c SCORES_SHA256.txt
)
"$BIN" "$INPUT" "$REPEAT"
cmp "$OUTPUT/candidate_summary.csv" "$REPEAT/candidate_summary.csv"
cmp "$OUTPUT/scores_long.csv" "$REPEAT/scores_long.csv"
cmp "$OUTPUT/persistent_source_samples.csv" "$REPEAT/persistent_source_samples.csv"
cmp "$OUTPUT/source_blind_audit.txt" "$REPEAT/source_blind_audit.txt"
echo DETERMINISTIC_REPEAT_PASS
