#!/usr/bin/env bash
set -Eeuo pipefail

# C0.5 stage-3 generator.  This is an offline GADEN data step only: it does
# not start ROS, PMFS, a planner, or a closed loop.  The benchmark's exact
# S1/W1/seedA output is promoted into the bank so that no extra stochastic
# realization is consumed.

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/c0_5_real_gaden_bank_20260923}"
COST_ROOT="${COST_ROOT:-/home/zyc/c0_5_cost_benchmark_20260923}"

BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
OCCUPANCY="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
W1="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
W2="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

SIM_TIME="300.0"
EXPECTED_FRAMES=566
SEED_A="2026092301"
SEED_B="2026092302"
BINARY_SHA="$(sha256sum "${BINARY}" | awk '{print $1}')"
OCCUPANCY_SHA="$(sha256sum "${OCCUPANCY}" | awk '{print $1}')"
W1_SHA="$(sha256sum "${W1}/wind_iteration_0" | awk '{print $1}')"
W2_SHA="$(sha256sum "${W2}/wind_iteration_0" | awk '{print $1}')"

[[ -x "${BINARY}" ]] || { echo "missing generator binary: ${BINARY}" >&2; exit 2; }
[[ -f "${OCCUPANCY}" ]] || { echo "missing occupancy: ${OCCUPANCY}" >&2; exit 2; }
[[ -f "${W1}/wind_iteration_0" && -f "${W2}/wind_iteration_0" ]] || {
  echo "missing canonical wind field" >&2; exit 2;
}
[[ ! -e "${OUT_ROOT}" ]] || { echo "refuse overwrite: ${OUT_ROOT}" >&2; exit 3; }
[[ -d "${COST_ROOT}/t300p0/realization" ]] || {
  echo "benchmark realization unavailable for exact S1_W1_A promotion" >&2; exit 4;
}

mkdir -p "${OUT_ROOT}"

cat > "${OUT_ROOT}/bank_contract.tsv" <<EOF
house	House02
occupancy	${OCCUPANCY}
occupancy_sha256	${OCCUPANCY_SHA}
wind_W1	${W1}
wind_W1_iteration0_sha256	${W1_SHA}
wind_W2	${W2}
wind_W2_iteration0_sha256	${W2_SHA}
binary	${BINARY}
binary_sha256	${BINARY_SHA}
sim_time_s	${SIM_TIME}
time_step_s	0.1
results_time_step_s	0.5
num_filaments_sec	7
variable_rate	true
filament_stop_steps	0
ppm_filament_center	10.0
filament_initial_std	10.0
filament_growth_gamma	15.0
filament_noise_std	0.01
gas_type	10
temperature	298.0
pressure	1.0
concentration_unit_choice	1
allow_looping	true
loop_from_step	1
loop_to_step	10
writeConcentrations	false
source_z_m	0.20
seed_A	${SEED_A}
seed_B	${SEED_B}
expected_iteration_files	${EXPECTED_FRAMES}
EOF

write_manifest() {
  local cell="$1" source_id="$2" wind_id="$3" seed="$4" out="$5" promoted="$6"
  local count bytes
  count="$(find "${out}/realization" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
  bytes="$(du -sb "${out}/realization" | awk '{print $1}')"
  [[ "${count}" -eq "${EXPECTED_FRAMES}" ]] || {
    echo "${cell}: expected ${EXPECTED_FRAMES} iteration files, got ${count}" >&2; exit 5;
  }
  cat > "${out}/manifest.tsv" <<EOF
cell	${cell}
house	House02
source_id	${source_id}
source_xyz_m	$(case "${source_id}" in S1) echo '-2.242730141,-2.200880051,0.20';; S2) echo '-4.342730045,2.899120331,0.20';; esac)
wind_id	${wind_id}
wind_dir	$(case "${wind_id}" in W1) echo "${W1}";; W2) echo "${W2}";; esac)
wind_iteration0_sha256	$(case "${wind_id}" in W1) echo "${W1_SHA}";; W2) echo "${W2_SHA}";; esac)
occupancy_sha256	${OCCUPANCY_SHA}
gaden_rng_seed	${seed}
binary_sha256	${BINARY_SHA}
simulation_duration_s	${SIM_TIME}
iteration_files	${count}
realization_bytes	${bytes}
promoted_from_cost_benchmark	${promoted}
EOF
  sha256sum "${out}/manifest.tsv" > "${out}/manifest.sha256"
}

promote_s1_w1_a() {
  local out="${OUT_ROOT}/S1_W1_A"
  mkdir -p "${out}"
  cp -a "${COST_ROOT}/t300p0/realization" "${out}/realization"
  ln -s "${OCCUPANCY}" "${out}/OccupancyGrid3D.csv"
  write_manifest "S1_W1_A" "S1" "W1" "${SEED_A}" "${out}" "true"
}

run_one() {
  local cell="$1" source_id="$2" sx="$3" sy="$4" wind_id="$5" wind_dir="$6" seed="$7"
  local out="${OUT_ROOT}/${cell}"
  mkdir -p "${out}"
  ln -s "${OCCUPANCY}" "${out}/OccupancyGrid3D.csv"
  set +e
  /usr/bin/time -v -o "${out}/time.txt" env GADEN_RNG_SEED="${seed}" "${BINARY}" --ros-args \
    -p verbose:=false \
    -p wait_preprocessing:=false \
    -p sim_time:="${SIM_TIME}" \
    -p time_step:=0.1 \
    -p num_filaments_sec:=7 \
    -p variable_rate:=true \
    -p filament_stop_steps:=0 \
    -p ppm_filament_center:=10.0 \
    -p filament_initial_std:=10.0 \
    -p filament_growth_gamma:=15.0 \
    -p filament_noise_std:=0.01 \
    -p gas_type:=10 \
    -p temperature:=298.0 \
    -p pressure:=1.0 \
    -p concentration_unit_choice:=1 \
    -p occupancy3D_data:="${OCCUPANCY}" \
    -p fixed_frame:=map \
    -p wind_data:="${wind_dir}" \
    -p wind_time_step:=1.0 \
    -p allow_looping:=true \
    -p loop_from_step:=1 \
    -p loop_to_step:=10 \
    -p source_position_x:="${sx}" \
    -p source_position_y:="${sy}" \
    -p source_position_z:=0.20 \
    -p save_results:=1 \
    -p results_time_step:=0.5 \
    -p results_min_time:=0.0 \
    -p writeConcentrations:=false \
    -p results_location:="${out}/realization" \
    >"${out}/generation.log" 2>&1
  local rc=$?
  set -e
  [[ "${rc}" -eq 0 ]] || { echo "${cell}: generator exit ${rc}" >&2; exit 6; }
  grep -q 'Filament simulator finished correctly!' "${out}/generation.log" || {
    echo "${cell}: completion marker missing" >&2; exit 7;
  }
  write_manifest "${cell}" "${source_id}" "${wind_id}" "${seed}" "${out}" "false"
}

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

promote_s1_w1_a
run_one S1_W1_B S1 -2.242730141 -2.200880051 W1 "${W1}" "${SEED_B}"
run_one S1_W2_A S1 -2.242730141 -2.200880051 W2 "${W2}" "${SEED_A}"
run_one S1_W2_B S1 -2.242730141 -2.200880051 W2 "${W2}" "${SEED_B}"
run_one S2_W1_A S2 -4.342730045 2.899120331 W1 "${W1}" "${SEED_A}"
run_one S2_W1_B S2 -4.342730045 2.899120331 W1 "${W1}" "${SEED_B}"
run_one S2_W2_A S2 -4.342730045 2.899120331 W2 "${W2}" "${SEED_A}"
run_one S2_W2_B S2 -4.342730045 2.899120331 W2 "${W2}" "${SEED_B}"

find "${OUT_ROOT}" -mindepth 2 -maxdepth 2 -name manifest.tsv -print0 | sort -z | xargs -0 sha256sum > "${OUT_ROOT}/MANIFEST_SHA256SUMS"
printf 'C0_5_REAL_GADEN_BANK_GENERATION_DONE\n'
