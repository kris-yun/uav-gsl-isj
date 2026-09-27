#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ROOT=/home/zyc/aod_house03_f1_full624_20260927
while ! test -f "$ROOT/CANDIDATE_BANK_AUDIT.json"; do
  if ! kill -0 "$(cat "$ROOT/candidate.pid")" 2>/dev/null; then
    echo 'Candidate process ended without completion audit'; exit 1
  fi
  sleep 20
done
python3 "$ROOT/execution/freeze_candidate_templates_vm.py"
