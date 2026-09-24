#!/usr/bin/env bash
set -Eeuo pipefail

# Mori–Zwanzig Gate M0 dense-history generation + frozen Markov-vs-memory test.
# OFFLINE ONLY. No PMFS/ROS navigation/closed loop.
# Resume-safe: valid compact .npz histories plus sidecars are skipped.

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH_EXPECTED="research/mori-zwanzig-source-memory-v1"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
[[ "${BRANCH}" == "${BRANCH_EXPECTED}" ]] || {
  echo "Expected branch ${BRANCH_EXPECTED}; got ${BRANCH}" >&2
  exit 2
}

RESEARCH="${ROOT}/research/mori_zwanzig_source_memory_v1"
BIGREEN_RESEARCH="${ROOT}/research/causal_biorthogonal_green_v1"
EVIDENCE="${ROOT}/evidence/mori_zwanzig_source_memory_v1"
CANDIDATE_MANIFEST="${ROOT}/evidence/hcmc_v1/independent_raw_native_20260922_verified/H02_R2026092212/context_bank/source_update_0001/candidate_manifest.csv"
PROBE_JSON="${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json"

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/mz_m0_dense_history_20260924}"
TMP_ROOT="${TMP_ROOT:-/home/zyc/mz_m0_tmp_20260924}"

BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"
OCCUPANCY="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
W2="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

EXPECTED_BINARY_SHA="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W2_ITER1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
EXPECTED_EXTRACTOR_SHA="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"

SEEDS=(2026092403 2026092404 2026092405)
SIM_TIME="300.0"
RESULT_DT="0.5"

mkdir -p "${EVIDENCE}" "${OUT_ROOT}" "${TMP_ROOT}" "${OUT_ROOT}/parent_bank"

sha_check() {
  local path="$1" expected="$2" label="$3"
  [[ -e "${path}" ]] || { echo "missing ${label}: ${path}" >&2; exit 3; }
  local actual
  actual="$(sha256sum "${path}" | awk '{print $1}')"
  [[ "${actual}" == "${expected}" ]] || {
    echo "${label} hash drift: expected ${expected}, got ${actual}" >&2
    exit 4
  }
}

[[ -x "${BINARY}" ]] || { echo "missing GADEN binary: ${BINARY}" >&2; exit 3; }
[[ -x "${EXTRACTOR}" ]] || { echo "missing extractor: ${EXTRACTOR}" >&2; exit 3; }
sha_check "${BINARY}" "${EXPECTED_BINARY_SHA}" "GADEN binary"
sha_check "${OCCUPANCY}" "${EXPECTED_OCC_SHA}" "House02 occupancy"
sha_check "${W2}/wind_iteration_1" "${EXPECTED_W2_ITER1_SHA}" "House02 W2 iteration 1"
sha_check "${EXTRACTOR}" "${EXPECTED_EXTRACTOR_SHA}" "spatial extractor"

for i in $(seq 1 10); do
  [[ -f "${W2}/wind_iteration_${i}" ]] || {
    echo "missing W2 wind_iteration_${i}" >&2
    exit 5
  }
done

{
  echo "branch=${BRANCH}"
  echo "head=$(git -C "${ROOT}" rev-parse HEAD)"
  echo "W2_PATH=${W2}"
  sha256sum "${W2}"/wind_iteration_{1..10}
  echo "occupancy=$(sha256sum "${OCCUPANCY}")"
  echo "binary=$(sha256sum "${BINARY}")"
  echo "extractor=$(sha256sum "${EXTRACTOR}")"
} > "${EVIDENCE}/MZ_M0_WIND_AND_BINARY_AUDIT_20260924.txt"

python3 -m py_compile   "${BIGREEN_RESEARCH}/prepare_gate1a_bank.py"   "${RESEARCH}/select_mz_m0_sources.py"   "${RESEARCH}/extract_mz_m0_dense_history.py"   "${RESEARCH}/evaluate_mz_m0.py"

prepare_banks() {
  local dest="$1"
  mkdir -p "${dest}/parent_bank"
  python3 "${BIGREEN_RESEARCH}/prepare_gate1a_bank.py"     --candidate-manifest "${CANDIDATE_MANIFEST}"     --occupancy "${OCCUPANCY}"     --probe-json "${PROBE_JSON}"     --out "${dest}/parent_bank" >/dev/null

  python3 "${RESEARCH}/select_mz_m0_sources.py"     --source-bank "${dest}/parent_bank/source_bank.tsv"     --out-tsv "${dest}/m0_source_bank.tsv"     --out-json "${dest}/m0_source_selection.json" >/dev/null
}

if [[ ! -f "${OUT_ROOT}/m0_source_bank.tsv" || ! -f "${OUT_ROOT}/m0_source_selection.json" || ! -f "${OUT_ROOT}/parent_bank/gate1a_contract.json" ]]; then
  prepare_banks "${OUT_ROOT}"
else
  VERIFY_DIR="${TMP_ROOT}/verify_bank_$$"
  rm -rf "${VERIFY_DIR}"
  mkdir -p "${VERIFY_DIR}"
  prepare_banks "${VERIFY_DIR}"
  for f in parent_bank/source_bank.tsv parent_bank/gate1a_contract.json m0_source_bank.tsv m0_source_selection.json; do
    cmp -s "${VERIFY_DIR}/${f}" "${OUT_ROOT}/${f}" || {
      echo "frozen bank drift on resume: ${f}" >&2
      exit 6
    }
  done
  rm -rf "${VERIFY_DIR}"
fi

[[ "$(tail -n +2 "${OUT_ROOT}/m0_source_bank.tsv" | wc -l)" -eq 180 ]] || {
  echo "M0 source count is not 180" >&2
  exit 7
}

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

valid_history() {
  local p="$1"
  [[ -f "${p}" ]] || return 1
  python3 - "${p}" <<'PY' >/dev/null 2>&1
import sys, numpy as np
with np.load(sys.argv[1],allow_pickle=False) as z:
    it=z["iteration_index"]
    t=z["time_s"]
    x=z["probe_ppm"]
assert x.ndim==2 and x.shape[1]==30 and x.shape[0]>=500
assert it.shape==(x.shape[0],) and t.shape==(x.shape[0],)
assert np.all(np.diff(it)>0) and np.all(np.diff(t)>0)
assert np.isfinite(x).all() and (x>=0).all()
PY
}

run_one() {
  local seed="$1" source_id="$2" sx="$3" sy="$4" sz="$5"
  local seed_root="${OUT_ROOT}/histories/seed_${seed}"
  local log_root="${OUT_ROOT}/logs/seed_${seed}"
  local compact="${seed_root}/${source_id}.npz"
  local sidecar="${seed_root}/${source_id}.json"
  mkdir -p "${seed_root}" "${log_root}"

  if valid_history "${compact}" && [[ -f "${sidecar}" ]]; then
    printf 'SKIP %s seed=%s\n' "${source_id}" "${seed}"
    return 0
  fi

  local work="${TMP_ROOT}/${source_id}_${seed}"
  rm -rf "${work}"
  mkdir -p "${work}/realization" "${work}/spatial"
  ln -s "${OCCUPANCY}" "${work}/realization/OccupancyGrid3D.csv"

  local genlog="${log_root}/${source_id}.generation.log"
  set +e
  env GADEN_RNG_SEED="${seed}" "${BINARY}" --ros-args     -p verbose:=false     -p wait_preprocessing:=false     -p sim_time:="${SIM_TIME}"     -p time_step:=0.1     -p num_filaments_sec:=7     -p variable_rate:=true     -p filament_stop_steps:=0     -p ppm_filament_center:=10.0     -p filament_initial_std:=10.0     -p filament_growth_gamma:=15.0     -p filament_noise_std:=0.01     -p gas_type:=10     -p temperature:=298.0     -p pressure:=1.0     -p concentration_unit_choice:=1     -p occupancy3D_data:="${OCCUPANCY}"     -p fixed_frame:=map     -p wind_data:="${W2}"     -p wind_time_step:=1.0     -p allow_looping:=true     -p loop_from_step:=1     -p loop_to_step:=10     -p source_position_x:="${sx}"     -p source_position_y:="${sy}"     -p source_position_z:="${sz}"     -p save_results:=1     -p results_time_step:="${RESULT_DT}"     -p results_min_time:=0.0     -p writeConcentrations:=false     -p results_location:="${work}/realization"     >"${genlog}" 2>&1
  local rc=$?
  set -e
  [[ "${rc}" -eq 0 ]] || {
    echo "${source_id} seed=${seed}: GADEN exit ${rc}" >&2
    exit 20
  }
  grep -q 'Filament simulator finished correctly!' "${genlog}" || {
    echo "${source_id} seed=${seed}: completion marker missing" >&2
    exit 21
  }

  mapfile -t iterations < <(
    find "${work}/realization" -maxdepth 1 -type f -name 'iteration_*' -printf '%f\n'       | sed 's/^iteration_//' | sort -n
  )
  local frame_count="${#iterations[@]}"
  [[ "${frame_count}" -eq 566 ]] || {
    echo "${source_id} seed=${seed}: expected 566 frames, got ${frame_count}" >&2
    exit 22
  }
  printf '%s\n' "${iterations[@]}" > "${work}/iteration_list.txt"

  [[ -e "${work}/realization/OccupancyGrid3D.csv" ]] ||
    ln -s "${OCCUPANCY}" "${work}/realization/OccupancyGrid3D.csv"

  local extlog="${log_root}/${source_id}.extract.log"
  "${EXTRACTOR}"     "${work}/realization" "${work}/realization"     "${work}/spatial/concentration.npy" "${work}/spatial/metadata.json"     "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${iterations[@]}"     >"${extlog}" 2>&1

  python3 "${RESEARCH}/extract_mz_m0_dense_history.py"     --concentration "${work}/spatial/concentration.npy"     --gate1-contract "${OUT_ROOT}/parent_bank/gate1a_contract.json"     --iteration-list "${work}/iteration_list.txt"     --results-dt "${RESULT_DT}"     --out "${compact}" >/dev/null

  valid_history "${compact}" || {
    echo "${source_id} seed=${seed}: invalid dense history" >&2
    exit 23
  }

  local compact_sha gen_sha ext_sha
  compact_sha="$(sha256sum "${compact}" | awk '{print $1}')"
  gen_sha="$(sha256sum "${genlog}" | awk '{print $1}')"
  ext_sha="$(sha256sum "${extlog}" | awk '{print $1}')"
  cat > "${sidecar}" <<EOF
{
  "source_id": "${source_id}",
  "source_xyz_m": [${sx}, ${sy}, ${sz}],
  "rng_seed": ${seed},
  "wind_id": "W2",
  "wind_path": "${W2}",
  "compact_sha256": "${compact_sha}",
  "generation_log_sha256": "${gen_sha}",
  "extract_log_sha256": "${ext_sha}",
  "frame_count": ${frame_count},
  "results_time_step_s": ${RESULT_DT}
}
EOF
  rm -rf "${work}"
  printf 'DONE %s seed=%s frames=%s\n' "${source_id}" "${seed}" "${frame_count}"
}

for seed in "${SEEDS[@]}"; do
  while IFS=$'\t' read -r source_id pmfs_i pmfs_j x_m y_m z_m gix giy giz parent_count parent_ids fps_order; do
    [[ "${source_id}" == "source_id" ]] && continue
    run_one "${seed}" "${source_id}" "${x_m}" "${y_m}" "${z_m}"
  done < "${OUT_ROOT}/m0_source_bank.tsv"
done

for seed in "${SEEDS[@]}"; do
  count="$(find "${OUT_ROOT}/histories/seed_${seed}" -maxdepth 1 -type f -name 'pmfs_*.npz' | wc -l)"
  [[ "${count}" -eq 180 ]] || {
    echo "seed ${seed}: expected 180 histories, got ${count}" >&2
    exit 30
  }
done

RESULT="${EVIDENCE}/MZ_M0_RESULT_20260924.json"
DETAIL="${EVIDENCE}/MZ_M0_ALL_TESTS_20260924.csv"
set +e
python3 "${RESEARCH}/evaluate_mz_m0.py"   --source-bank "${OUT_ROOT}/m0_source_bank.tsv"   --history-root "${OUT_ROOT}/histories"   --out-json "${RESULT}"   --out-csv "${DETAIL}"   | tee "${EVIDENCE}/MZ_M0_20260924.log"
eval_rc=${PIPESTATUS[0]}
set -e

{
  echo "head=$(git -C "${ROOT}" rev-parse HEAD)"
  sha256sum     "${RESEARCH}/select_mz_m0_sources.py"     "${RESEARCH}/extract_mz_m0_dense_history.py"     "${RESEARCH}/evaluate_mz_m0.py"     "${RESEARCH}/run_mz_m0_dense_history_vm.sh"     "${OUT_ROOT}/parent_bank/source_bank.tsv"     "${OUT_ROOT}/parent_bank/gate1a_contract.json"     "${OUT_ROOT}/m0_source_bank.tsv"     "${OUT_ROOT}/m0_source_selection.json"     "${RESULT}"     "${DETAIL}"
} > "${EVIDENCE}/MZ_M0_SHA256_20260924.txt"

(
  cd "${OUT_ROOT}"
  find histories -type f \( -name '*.npz' -o -name '*.json' \) -print0     | sort -z | xargs -0 sha256sum
) > "${EVIDENCE}/MZ_M0_HISTORY_SHA256_20260924.txt"

cat "${RESULT}"
exit "${eval_rc}"
