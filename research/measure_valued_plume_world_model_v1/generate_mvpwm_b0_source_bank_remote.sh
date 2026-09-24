#!/usr/bin/env bash
set -Eeuo pipefail

# MVPWM B0 source-intervention bank.
# Offline GADEN only. No ROS, PMFS, planner or closed loop.

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/mvpwm_source_bank_b0_20260924}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"

BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
OCC="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
W1="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
W2="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

SIM_TIME=300.0
SEED_A=2026092301
EXPECTED_FRAMES=566
ITERS=(100 150 200 250 300 350 400 450 500 550)

[[ -x "${BINARY}" ]] || { echo "missing binary ${BINARY}" >&2; exit 2; }
[[ -x "${EXTRACTOR}" ]] || { echo "missing extractor ${EXTRACTOR}" >&2; exit 2; }
[[ -f "${OCC}" ]] || { echo "missing occupancy" >&2; exit 2; }
[[ -f "${W1}/wind_iteration_0" && -f "${W2}/wind_iteration_0" ]] || { echo "missing wind" >&2; exit 2; }
[[ ! -e "${OUT_ROOT}" ]] || { echo "refuse overwrite ${OUT_ROOT}" >&2; exit 3; }

mkdir -p "${OUT_ROOT}/development" "${OUT_ROOT}/sealed_raw"

BIN_SHA="$(sha256sum "${BINARY}" | awk '{print $1}')"
OCC_SHA="$(sha256sum "${OCC}" | awk '{print $1}')"
W1_SHA="$(sha256sum "${W1}/wind_iteration_0" | awk '{print $1}')"
W2_SHA="$(sha256sum "${W2}/wind_iteration_0" | awk '{print $1}')"

cat > "${OUT_ROOT}/bank_contract.tsv" <<EOF
house	House02
purpose	MVPWM_B0_unseen_source_intervention_gate
sim_time_s	${SIM_TIME}
time_step_s	0.1
results_time_step_s	0.5
seed_A	${SEED_A}
binary_sha256	${BIN_SHA}
occupancy_sha256	${OCC_SHA}
wind_W1_iteration0_sha256	${W1_SHA}
wind_W2_iteration0_sha256	${W2_SHA}
holdout	U3,U4
development	S1,S2,U1,U2
EOF

run_one() {
  local root="$1" sid="$2" sx="$3" sy="$4" wid="$5" wdir="$6"
  local cell="${sid}_${wid}_A" out="${root}/${cell}"
  mkdir -p "${out}"
  /usr/bin/time -v -o "${out}/time.txt" env GADEN_RNG_SEED="${SEED_A}" "${BINARY}" --ros-args \
    -p verbose:=false -p wait_preprocessing:=false \
    -p sim_time:="${SIM_TIME}" -p time_step:=0.1 \
    -p num_filaments_sec:=7 -p variable_rate:=true -p filament_stop_steps:=0 \
    -p ppm_filament_center:=10.0 -p filament_initial_std:=10.0 \
    -p filament_growth_gamma:=15.0 -p filament_noise_std:=0.01 \
    -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
    -p concentration_unit_choice:=1 -p occupancy3D_data:="${OCC}" \
    -p fixed_frame:=map -p wind_data:="${wdir}" -p wind_time_step:=1.0 \
    -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
    -p source_position_x:="${sx}" -p source_position_y:="${sy}" -p source_position_z:=0.20 \
    -p save_results:=1 -p results_time_step:=0.5 -p results_min_time:=0.0 \
    -p writeConcentrations:=false -p results_location:="${out}/realization" \
    >"${out}/generation.log" 2>&1
  grep -q 'Filament simulator finished correctly!' "${out}/generation.log"
  local n
  n="$(find "${out}/realization" -maxdepth 1 -name 'iteration_*' -type f | wc -l)"
  [[ "${n}" -eq "${EXPECTED_FRAMES}" ]] || { echo "${cell}: ${n} frames" >&2; exit 4; }
  cat > "${out}/manifest.tsv" <<EOF
source_id	${sid}
source_xyz_m	${sx},${sy},0.20
wind_id	${wid}
seed	${SEED_A}
frames	${n}
binary_sha256	${BIN_SHA}
occupancy_sha256	${OCC_SHA}
wind_iteration0_sha256	$( [[ "${wid}" == W1 ]] && echo "${W1_SHA}" || echo "${W2_SHA}" )
EOF
}

extract_one() {
  local out="$1"
  local raw="${out}/realization" sp="${out}/spatial"
  [[ ! -e "${sp}" ]] || { echo "refuse overwrite ${sp}" >&2; exit 5; }
  mkdir -p "${sp}"
  [[ -e "${raw}/OccupancyGrid3D.csv" ]] || ln -s "${OCC}" "${raw}/OccupancyGrid3D.csv"
  "${EXTRACTOR}" "${raw}" "${raw}" "${sp}/concentration.npy" "${sp}/metadata.json" \
    -5.39273 -7.45088 0.1 1 0.20 83 119 "${ITERS[@]}" >"${sp}/extract.log" 2>&1
  sha256sum "${sp}/concentration.npy" "${sp}/metadata.json" > "${sp}/SHA256SUMS"
}

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

# Development sources: strongest historical confounders.
run_one "${OUT_ROOT}/development" U1 -5.042730000 0.699120000 W1 "${W1}"
run_one "${OUT_ROOT}/development" U1 -5.042730000 0.699120000 W2 "${W2}"
run_one "${OUT_ROOT}/development" U2 -3.542730000 2.299120000 W1 "${W1}"
run_one "${OUT_ROOT}/development" U2 -3.542730000 2.299120000 W2 "${W2}"
for d in "${OUT_ROOT}/development"/*; do extract_one "${d}"; done

# Holdouts: generate but do not export concentration slices.
run_one "${OUT_ROOT}/sealed_raw" U3 -4.642730000 4.199120000 W1 "${W1}"
run_one "${OUT_ROOT}/sealed_raw" U3 -4.642730000 4.199120000 W2 "${W2}"
run_one "${OUT_ROOT}/sealed_raw" U4 1.257270000 0.099120000 W1 "${W1}"
run_one "${OUT_ROOT}/sealed_raw" U4 1.257270000 0.099120000 W2 "${W2}"

tar -C "${OUT_ROOT}" -czf "${OUT_ROOT}/SEALED_U3_U4_RAW.tar.gz" sealed_raw
sha256sum "${OUT_ROOT}/SEALED_U3_U4_RAW.tar.gz" > "${OUT_ROOT}/SEALED_U3_U4_RAW.sha256"
rm -rf "${OUT_ROOT}/sealed_raw"

find "${OUT_ROOT}/development" -name manifest.tsv -print0 | sort -z | xargs -0 sha256sum > "${OUT_ROOT}/DEVELOPMENT_MANIFEST_SHA256SUMS"
printf 'MVPWM_B0_GENERATION_DONE\n'
