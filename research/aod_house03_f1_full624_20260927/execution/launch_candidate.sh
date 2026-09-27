#!/usr/bin/env bash
set -Ee -o pipefail
ROOT=/home/zyc/aod_house03_f1_full624_20260927
test -f "$ROOT/BUILD_AND_ASSET_AUDIT.json"
if test -f "$ROOT/candidate.pid" && kill -0 "$(cat "$ROOT/candidate.pid")" 2>/dev/null; then
  echo 'Candidate batch already active'; exit 1
fi
nohup bash "$ROOT/execution/start_candidate_phase.sh" > "$ROOT/candidate_phase.log" 2>&1 < /dev/null &
echo "$!" > "$ROOT/candidate.pid"
cat "$ROOT/candidate.pid"
