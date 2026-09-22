#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-smoke}"
BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
DATA_ROOT="${DATA_ROOT:-/home/zyc/hcmc_v1_independent_data_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
LIBBSC_DIR="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc"

[[ -x "${BINARY}" ]] || { echo "missing generator binary: ${BINARY}" >&2; exit 2; }
mkdir -p "${DATA_ROOT}"

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${LIBBSC_DIR}:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

declare -A CONFIG SOURCE_X SOURCE_Y SOURCE_Z WIND_DIR
CONFIG[House01]="2,4-1_fast"; SOURCE_X[House01]="-0.40"; SOURCE_Y[House01]="-2.90"; SOURCE_Z[House01]="-0.30"
CONFIG[House02]="3,5-1_fast"; SOURCE_X[House02]="0.00"; SOURCE_Y[House02]="-1.00"; SOURCE_Z[House02]="0.20"
CONFIG[House03]="1-2,5_fast"; SOURCE_X[House03]="-0.45"; SOURCE_Y[House03]="1.90"; SOURCE_Z[House03]="-0.10"
WIND_DIR[House01]="${CANONICAL_ROOT}/House01/gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/wind"
WIND_DIR[House02]="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
WIND_DIR[House03]="${CANONICAL_ROOT}/House03/gas_simulations/1-2,5_fast/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10/wind"

generate_one() {
  local house="$1" seed="$2" label="$3" sim_time="$4" output="$5"
  local scenario_root="${CANONICAL_ROOT}/${house}"
  local config="${CONFIG[${house}]}"
  local final_dir="${output}/FilamentSimulation_gasType_10_sourcePosition_${SOURCE_X[${house}]}_${SOURCE_Y[${house}]}_${SOURCE_Z[${house}]}"
  [[ -f "${scenario_root}/OccupancyGrid3D.csv" ]] || { echo "missing occupancy for ${house}" >&2; return 2; }
  [[ -f "${WIND_DIR[${house}]}/wind_iteration_0" ]] || { echo "missing canonical realization wind for ${house}" >&2; return 2; }
  local adopt_completed="false"
  if [[ -e "${final_dir}" ]]; then
    if [[ "${ADOPT_COMPLETED:-0}" == "1" ]] && grep -Fq "Filament simulator finished correctly" "${output}/generation.log"; then
      adopt_completed="true"
      echo "GENERATION_ADOPT_COMPLETED house=${house} seed=${seed} output=${final_dir}"
    else
      echo "refuse overwrite: ${final_dir}" >&2
      return 3
    fi
  else
    mkdir -p "${final_dir}"
  fi
  local log="${output}/generation.log"
  if [[ "${adopt_completed}" != "true" ]]; then
    echo "GENERATION_START house=${house} seed=${seed} label=${label} sim_time=${sim_time} output=${final_dir}"
    GADEN_RNG_SEED="${seed}" "${BINARY}" --ros-args \
    -p verbose:=false -p wait_preprocessing:=false \
    -p sim_time:="${sim_time}" -p time_step:=0.1 \
    -p num_filaments_sec:=7 -p variable_rate:=true -p filament_stop_steps:=0 \
    -p ppm_filament_center:=10.0 -p filament_initial_std:=10.0 \
    -p filament_growth_gamma:=15.0 -p filament_noise_std:=0.01 \
    -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
    -p concentration_unit_choice:=1 \
    -p occupancy3D_data:="${scenario_root}/OccupancyGrid3D.csv" -p fixed_frame:=map \
    -p wind_data:="${WIND_DIR[${house}]}" \
    -p wind_time_step:=1.0 -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
    -p source_position_x:="${SOURCE_X[${house}]}" \
    -p source_position_y:="${SOURCE_Y[${house}]}" \
    -p source_position_z:="${SOURCE_Z[${house}]}" \
    -p save_results:=1 -p results_time_step:=0.5 -p results_min_time:=0.0 \
    -p writeConcentrations:=false -p results_location:="${final_dir}" \
      >"${log}" 2>&1
  fi
  local count
  count="$(find "${final_dir}" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
  if [[ "${sim_time}" == "1000.0" && "${count}" -lt "1501" ]]; then
    echo "formal frame-count insufficient: house=${house} seed=${seed} count=${count}" >&2
    return 4
  fi
  {
    echo "case_id=${label}"
    echo "house=${house}"
    echo "plume_seed=${seed}"
    echo "sim_time_s=${sim_time}"
    echo "iteration_file_count=${count}"
    echo "generator_sha256=$(sha256sum "${BINARY}" | awk '{print $1}')"
    echo "occupancy_sha256=$(sha256sum "${scenario_root}/OccupancyGrid3D.csv" | awk '{print $1}')"
    echo "wind_directory=${WIND_DIR[${house}]}"
    find "${final_dir}" -maxdepth 1 -type f -name 'iteration_*' -printf '%f\n' | LC_ALL=C sort | while IFS= read -r name; do sha256sum "${final_dir}/${name}"; done
  } > "${output}/generation_manifest.txt"
  echo "GENERATION_PASS house=${house} seed=${seed} count=${count}"
}

case "${MODE}" in
  smoke)
    smoke_root="${DATA_ROOT}/smoke"
    generate_one House01 2026092291 same_a 3.0 "${smoke_root}/same_a"
    generate_one House01 2026092291 same_b 3.0 "${smoke_root}/same_b"
    generate_one House01 2026092292 different 3.0 "${smoke_root}/different"
    same_a="$(sha256sum "${smoke_root}/same_a/generation_manifest.txt" | awk '{print $1}')"
    # Compare only the generated iteration payloads, not case labels/paths.
    find "${smoke_root}/same_a" -type f -name 'iteration_*' -printf '%f\n' | LC_ALL=C sort | while IFS= read -r name; do sha256sum "${smoke_root}/same_a/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/${name}" | awk '{print $1}'; done > "${smoke_root}/same_a.payload.sha256"
    find "${smoke_root}/same_b" -type f -name 'iteration_*' -printf '%f\n' | LC_ALL=C sort | while IFS= read -r name; do sha256sum "${smoke_root}/same_b/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/${name}" | awk '{print $1}'; done > "${smoke_root}/same_b.payload.sha256"
    find "${smoke_root}/different" -type f -name 'iteration_*' -printf '%f\n' | LC_ALL=C sort | while IFS= read -r name; do sha256sum "${smoke_root}/different/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/${name}" | awk '{print $1}'; done > "${smoke_root}/different.payload.sha256"
    cmp -s "${smoke_root}/same_a.payload.sha256" "${smoke_root}/same_b.payload.sha256" || { echo "same-seed mismatch" >&2; exit 10; }
    if cmp -s "${smoke_root}/same_a.payload.sha256" "${smoke_root}/different.payload.sha256"; then
      echo "different-seed payloads unexpectedly identical" >&2; exit 11
    fi
    echo "HCMC_GADEN_SEED_SMOKE_PASS"
    ;;
  formal)
    generate_one House01 2026092201 H01_R2026092201 1000.0 "${DATA_ROOT}/H01_R2026092201"
    generate_one House01 2026092202 H01_R2026092202 1000.0 "${DATA_ROOT}/H01_R2026092202"
    generate_one House02 2026092211 H02_R2026092211 1000.0 "${DATA_ROOT}/H02_R2026092211"
    generate_one House02 2026092212 H02_R2026092212 1000.0 "${DATA_ROOT}/H02_R2026092212"
    generate_one House03 2026092221 H03_R2026092221 1000.0 "${DATA_ROOT}/H03_R2026092221"
    generate_one House03 2026092222 H03_R2026092222 1000.0 "${DATA_ROOT}/H03_R2026092222"
    echo "HCMC_GADEN_FORMAL_SIX_PASS"
    ;;
  *) echo "usage: $0 smoke|formal" >&2; exit 2 ;;
esac
