#!/usr/bin/env bash
set -eo pipefail

OUT_ROOT=${1:?output root}
ROUTE_ROOT=${2:?local route root on VM}
SENSOR_ROOT=${3:?sensor probe root on VM}
SIM_BIN=/home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/lib/gaden_filament_simulator/filament_simulator
ENV_BASE=/mnt/hgfs/workspace/GADEN_files/scenarios
RAW_BASE=/mnt/hgfs/workspace/GADEN_files/scenarios
HELPER=/home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
PY=/usr/bin/python3

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/setup.bash
set -u
export LD_LIBRARY_PATH=/home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/gaden_common/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/lib:/home/zyc/ros2_ws/install/gaden_common/lib:${LD_LIBRARY_PATH:-}
export GADEN_RNG_SEED=1234
SIM_TIME_S=${SIM_TIME_S:-60.1}
EXPECTED_FRAMES=${EXPECTED_FRAMES:-601}
CASE_FILTER=${CASE_FILTER:-}

mkdir -p "$OUT_ROOT"

run_case() {
  local id=$1 house=$2 sim=$3 sx=$4 sy=$5 sz=$6
  if [ -n "$CASE_FILTER" ] && [ "$id" != "$CASE_FILTER" ]; then return 0; fi
  local work="/dev/shm/cstar_current_${id}"
  local input="$work/input"
  local output="$work/output"
  local raw_wind
  rm -rf "$work"
  mkdir -p "$input" "$output"
  raw_wind=$(find "$RAW_BASE/$house/gas_simulations/$sim" -maxdepth 4 -type d -name wind | sort | head -1)
  test -n "$raw_wind"
  test "$(find "$raw_wind" -maxdepth 1 -type f -name 'wind_iteration_*' | wc -l)" -eq 11
  for f in "$raw_wind"/wind_iteration_*; do
    local n=${f##*_}
    cp "$f" "$input/wind_iteration_${n}.csv_gaden"
  done
  timeout 180s "$SIM_BIN" --ros-args \
    -p sim_time:="$SIM_TIME_S" -p time_step:=0.1 -p num_filaments_sec:=7 \
    -p variable_rate:=true -p filament_stop_steps:=0 -p ppm_filament_center:=10.0 \
    -p filament_initial_std:=10.0 -p filament_growth_gamma:=15.0 \
    -p filament_noise_std:=0.01 -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
    -p concentration_unit_choice:=1 -p occupancy3D_data:="$ENV_BASE/$house/OccupancyGrid3D.csv" \
    -p wind_data:="$input/wind_iteration" -p wind_time_step:=1.0 \
    -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
    -p source_position_x:="$sx" -p source_position_y:="$sy" -p source_position_z:="$sz" \
    -p save_results:=1 -p results_time_step:=0.0 -p results_min_time:=0.0 \
    -p writeConcentrations:=false -p results_location:="$output" \
    >"$work/sim.log" 2>&1
  test "$(find "$output" -maxdepth 1 -type f -name 'iteration_*' | wc -l)" -ge "$EXPECTED_FRAMES"
  "$PY" /dev/shm/cstar_extract_current_runtime_history.py \
    --env-root "$ENV_BASE/$house" --gas-results "$output" \
    --route "$ROUTE_ROOT/$house/history_route.csv" --helper "$HELPER" \
    --sensor-module "$SENSOR_ROOT/$house/sensor_model.py" \
    --sensor-manifest "$SENSOR_ROOT/$house/sensor_manifest.json" --raw-dt 0.1 \
    --output "$OUT_ROOT/$id/measured_history.jsonl"
  cp "$work/sim.log" "$OUT_ROOT/$id/sim.log"
  sha256sum "$OUT_ROOT/$id/measured_history.jsonl" | tee "$OUT_ROOT/$id/HISTORY_SHA256"
  rm -rf "$work"
}

run_case H01_SA_fast House01 '1,3-2,4_fast' -0.6 1.95 0.4
run_case H01_SA_slow House01 '1,3-2,4_slow' -0.6 1.95 0.4
run_case H01_SB_fast House01 '1,3-2,4_fast' -0.4 -2.9 -0.3
run_case H01_SB_slow House01 '1,3-2,4_slow' -0.4 -2.9 -0.3
run_case H02_SA_fast House02 '3,5-1_fast' 0.0 -1.0 0.2
run_case H02_SA_slow House02 '3,5-1_slow' 0.0 -1.0 0.2
run_case H02_SB_fast House02 '3,5-1_fast' 1.0 -2.3 -0.1
run_case H02_SB_slow House02 '3,5-1_slow' 1.0 -2.3 -0.1
run_case H03_SA_fast House03 '1-2,5_fast' -0.45 1.9 -0.1
run_case H03_SA_slow House03 '1-2,5_slow' -0.45 1.9 -0.1
run_case H03_SB_fast House03 '1-2,5_fast' 8.2 5.0 -0.2
run_case H03_SB_slow House03 '1-2,5_slow' 8.2 5.0 -0.2

echo CSTAR_CURRENT_RUNTIME_DATASET=PASS
