#!/usr/bin/env bash
set -euo pipefail

closure_root=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828
converter=/home/zyc/rmfe_wind_converter_install_v4/rmfe_wind_converter/lib/rmfe_wind_converter/rmfe_wind_converter
occupancy=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv
wind_prefix=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/wind_simulations/3,5-1_fast/3,5-1_fast
output_dir="$closure_root/converted_wind_house02"

set +u
source /opt/ros/humble/setup.bash
set -u
export LD_LIBRARY_PATH="$closure_root/gaden_install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

if [[ -e "$output_dir" ]]; then
    echo "PF_DEI_CONVERTER_OUTPUT_ALREADY_EXISTS=$output_dir" >&2
    exit 5
fi

"$converter" "$occupancy" "$wind_prefix" "$output_dir" \
    | tee "$closure_root/wind_conversion.log"

find "$output_dir" -maxdepth 2 -type f -printf '%p %s\n' | sort
sha256sum "$output_dir"/* | sort > "$closure_root/converted_wind_house02.sha256"
cat "$closure_root/converted_wind_house02.sha256"
