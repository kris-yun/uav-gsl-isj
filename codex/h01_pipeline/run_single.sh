#!/usr/bin/env bash
set -Ee -o pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOT="${TNQC_SINGLE_ROOT:?must name a new single-case output root}"
test "$(git -C "$REPO" branch --show-current)" = codex/tnqc-v5-300s-offline-20260921
test ! -e "$ROOT"
mkdir -p "$ROOT/build_source" "$ROOT/log"
git -C "$REPO" rev-parse HEAD > "$ROOT/git_sha.txt"
git -C "$REPO" rev-parse HEAD:ros2_package > "$ROOT/ros2_tree_sha.txt"
git -C "$REPO" archive HEAD ros2_package | tar -x -C "$ROOT/build_source"
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /dev/shm/house1_msgs_install/setup.bash
set -u
cmake -S "$ROOT/build_source/ros2_package" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF -DCMAKE_INSTALL_PREFIX="$ROOT/install/gsl_server" > "$ROOT/log/configure.log" 2>&1
cmake --build "$ROOT/build" -- -j1 -l1 > "$ROOT/log/build.log" 2>&1
cmake --install "$ROOT/build" > "$ROOT/log/install.log" 2>&1
python3 "$REPO/codex/h01_pipeline/prepare_runtime.py" "$ROOT/runtime_overlay"
export TNQC_RUNTIME_PYTHONPATH="$ROOT/runtime_overlay"
export TNQC_H01_SUPERVISOR="$REPO/codex/h01_pipeline/supervise.py"
export HOUSE=House01 SEED=0 ARM=off TNQC_MODE=off PFDI_MODE=off
export RUN_ROOT="$ROOT/native" PFDI_INSTALL_ROOT="$ROOT" DOMAIN_ID=222
export LAUNCH_FILE="$REPO/codex/h01_pipeline/vgr_h01_native_300s.launch.py"
export STEPS_SOURCE_UPDATE=3 TIMEOUT_SEC=300.0 SIM_STOP_AT_S=300.0 OUTER_DEADLINE_SEC=900 TARGET_SOURCE_UPDATES=0 TARGET_ACCEPTED_UPDATES=0
export RUN_CONTRACT=TNQC_H01_SINGLE_PIPELINE_PENDING
export ROS_DOMAIN_ID="$DOMAIN_ID"
export PS4='+ wall=${EPOCHREALTIME} shell=${BASHPID} line=${LINENO}: '
sha256sum "$ROOT/install/gsl_server/lib/gsl_server/gsl_actionserver_node" "$ROOT/install/gsl_server/lib/gsl_server/tnqc_expected_value_native" "$LAUNCH_FILE" > "$ROOT/binary_launch_sha256.txt"
date --iso-8601=ns > "$ROOT/start_wall.txt"
set +e
bash -x "$REPO/reference/run_meaci_case_20260824.sh" > "$ROOT/log/runner.log" 2>&1
rc=$?
set -e
date --iso-8601=ns > "$ROOT/end_wall.txt"
printf '%s\n' "$rc" > "$ROOT/runner_exit_code.txt"
CASE="$RUN_ROOT/House01_seed0_off_off"
grep -F 'RESULT IS:' "$CASE/launch.log" > "$ROOT/terminal.txt"
python3 "$REPO/codex/h01_pipeline/support_audit.py" "$CASE" > "$ROOT/support_audit.json"
printf 'SINGLE_NATIVE_FINISHED_REPLAY_NOT_YET_RUN\n'
