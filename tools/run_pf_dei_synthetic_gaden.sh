#!/usr/bin/env bash
set -euo pipefail

closure_root=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828
params="$closure_root/pf_dei_synthetic_gaden_params.yaml"
result_root="$closure_root/synthetic_native"
log="$closure_root/synthetic_native_converted.log"

set +u
source /opt/ros/humble/setup.bash
source "$closure_root/gaden_install/setup.bash"
set -u

if [[ -e "$result_root" ]]; then
    echo "PF_DEI_SYNTHETIC_RESULT_ALREADY_EXISTS=$result_root" >&2
    exit 5
fi

mkdir -p "$result_root"
timeout 180 ros2 run gaden_filament_simulator filament_simulator \
    --ros-args --params-file "$params" 2>&1 | tee "$log"

find "$result_root" -type f -printf '%p %s\n' | sort
