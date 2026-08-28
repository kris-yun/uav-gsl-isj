#!/usr/bin/env bash
set -euo pipefail

root=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828
log="$root/ros_player.log"
pid=""

cleanup() {
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT

set +u
source /opt/ros/humble/setup.bash
source "$root/gaden_install/setup.bash"
set -u
export ROS_DOMAIN_ID=214
export LD_LIBRARY_PATH="$root/gaden_install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

ros2 run gaden_player player --ros-args \
    --params-file "$root/pf_dei_player_params.yaml" \
    -r __ns:=/pfdei >"$log" 2>&1 &
pid=$!

python3 "$root/pf_dei_ros_player_query.py" \
    "$root/pf_dei_synthetic_schedule.csv" "$root/ros_player_query.csv"

head -8 "$root/ros_player_query.csv"
