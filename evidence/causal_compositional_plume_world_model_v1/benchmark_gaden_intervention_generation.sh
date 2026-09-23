#!/usr/bin/env bash
set -Eeuo pipefail

# M4 C0-A generation-cost benchmark.
# Run on the user's GADEN VM. This script does NOT choose a source using truth.
#
# Required env:
#   BINARY
#   OCCUPANCY
#   WIND_DIR
#   OUT_ROOT
#
# Optional:
#   SOURCE_X SOURCE_Y SOURCE_Z
#   SEED

: "${BINARY:?set GADEN filament_simulator binary}"
: "${OCCUPANCY:?set OccupancyGrid3D.csv}"
: "${WIND_DIR:?set physical wind directory}"
: "${OUT_ROOT:?set output root}"

SOURCE_X="${SOURCE_X:-0.60}"
SOURCE_Y="${SOURCE_Y:-0.00}"
SOURCE_Z="${SOURCE_Z:-0.20}"
SEED="${SEED:-2026092391}"

mkdir -p "${OUT_ROOT}"

run_one() {
  local sim_time="$1"
  local tag="t${sim_time//./p}"
  local out="${OUT_ROOT}/${tag}"
  mkdir -p "${out}"

  local log="${out}/generation.log"
  local time_log="${out}/time.txt"

  /usr/bin/time -v -o "${time_log}"     env GADEN_RNG_SEED="${SEED}" "${BINARY}" --ros-args       -p verbose:=false       -p wait_preprocessing:=false       -p sim_time:="${sim_time}"       -p time_step:=0.1       -p num_filaments_sec:=7       -p variable_rate:=true       -p filament_stop_steps:=0       -p ppm_filament_center:=10.0       -p filament_initial_std:=10.0       -p filament_growth_gamma:=15.0       -p filament_noise_std:=0.01       -p gas_type:=10       -p temperature:=298.0       -p pressure:=1.0       -p concentration_unit_choice:=1       -p occupancy3D_data:="${OCCUPANCY}"       -p fixed_frame:=map       -p wind_data:="${WIND_DIR}"       -p wind_time_step:=1.0       -p allow_looping:=true       -p loop_from_step:=1       -p loop_to_step:=10       -p source_position_x:="${SOURCE_X}"       -p source_position_y:="${SOURCE_Y}"       -p source_position_z:="${SOURCE_Z}"       -p save_results:=1       -p results_time_step:=0.5       -p results_min_time:=0.0       -p writeConcentrations:=false       -p results_location:="${out}/realization"       >"${log}" 2>&1

  find "${out}/realization" -type f -name 'iteration_*' | wc -l > "${out}/iteration_count.txt"
  du -sb "${out}/realization" | awk '{print $1}' > "${out}/bytes.txt"

  {
    echo "sim_time=${sim_time}"
    echo "source=${SOURCE_X},${SOURCE_Y},${SOURCE_Z}"
    echo "seed=${SEED}"
    echo "wind_dir=${WIND_DIR}"
    echo "occupancy=${OCCUPANCY}"
    echo "binary_sha256=$(sha256sum "${BINARY}" | awk '{print $1}')"
    echo "wind0_sha256=$(sha256sum "${WIND_DIR}/wind_iteration_0" | awk '{print $1}')"
    echo "occupancy_sha256=$(sha256sum "${OCCUPANCY}" | awk '{print $1}')"
  } > "${out}/manifest.txt"
}

for t in 30.0 120.0 300.0; do
  run_one "$t"
done

echo "M4_C0_GENERATION_COST_BENCHMARK_DONE"
