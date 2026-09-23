#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${TPT_REPLAY_BUILD_ROOT:-/dev/shm/tpt_first_passage_replay_build}"
RUN_ROOT="${RUN_ROOT:-$ROOT_DIR/evidence/hcmc_v1/independent_raw_native_20260922_verified}"
OUT_ROOT="${OUT_ROOT:-$ROOT_DIR/_staging/TPT_FIRST_PASSAGE_LAYER1_20260923}"

python3 -m py_compile   "$ROOT_DIR/reference/verify_native_candidate_trace.py"   "$ROOT_DIR/reference/tpt_first_passage_screen.py"   "$ROOT_DIR/reference/aggregate_tpt_first_passage_layer1.py"

bash -n "$ROOT_DIR/reference/run_tpt_first_passage_layer1_20260923.sh"

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT/src"
cp -a "$ROOT_DIR/ros2_package" "$BUILD_ROOT/src/gsl_server"

set +u
source /opt/ros/humble/setup.bash
for setup in   /home/zyc/ros2_ws/install/setup.bash   /dev/shm/house1_msgs_install/setup.bash   /dev/shm/house2_gaden_install/setup.bash   /dev/shm/house2_gaden_install/gaden_msgs/share/gaden_msgs/local_setup.bash   /dev/shm/house2_gaden_install/gaden_common/share/gaden_common/local_setup.bash
do
  if [[ -f "$setup" ]]; then
    source "$setup"
  fi
done
set -u

cd "$BUILD_ROOT"
colcon build   --packages-select gsl_server   --cmake-args     -DCMAKE_BUILD_TYPE=Release     -DPFDI_LOW_MEMORY_BUILD=ON     -DBUILD_TESTING=OFF

REPLAY_BIN="$BUILD_ROOT/build/gsl_server/native_candidate_replay"
[[ -x "$REPLAY_BIN" ]] || {
  echo "missing native_candidate_replay after build: $REPLAY_BIN" >&2
  find "$BUILD_ROOT" -maxdepth 5 -type f -name 'native_candidate_replay*' -print >&2 || true
  exit 71
}

mkdir -p "$OUT_ROOT"
cat > "$OUT_ROOT/build_provenance.json" <<EOF
{
  "contract": "TPT_FIRST_PASSAGE_MULTIRUN_REPLAY_BUILD_V1",
  "source_head": "$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || printf UNKNOWN)",
  "compiler": "$(g++ --version | head -n 1)",
  "build_type": "Release",
  "replay_binary": "$REPLAY_BIN",
  "replay_binary_sha256": "$(sha256sum "$REPLAY_BIN" | awk '{print $1}')",
  "run_root": "$RUN_ROOT"
}
EOF

cd "$ROOT_DIR"
RUN_ROOT="$RUN_ROOT" REPLAY_BIN="$REPLAY_BIN" OUT_ROOT="$OUT_ROOT"   bash reference/run_tpt_first_passage_layer1_20260923.sh
