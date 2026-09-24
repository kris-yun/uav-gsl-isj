#!/usr/bin/env bash
set -Eeuo pipefail

# Exact-physics Gate 1A for the Causal Biorthogonal Source-to-Sensor line.
#
# This is OFFLINE ONLY. It never starts PMFS, navigation, ROS actions, or a
# closed loop. It streams exact frozen-GADEN source hypotheses, extracts the
# frozen 30x10 probe vector, deletes raw realizations, and finally ranks all
# arbitrary source-grid positions against independent S2-W2 A/B targets.
#
# Resume-safe: completed prediction .npy files are validated and skipped.

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH_EXPECTED="research/causal-biorthogonal-green-v1"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
[[ "${BRANCH}" == "${BRANCH_EXPECTED}" ]] || {
  echo "Expected branch ${BRANCH_EXPECTED}; got ${BRANCH}" >&2
  exit 2
}

RESEARCH="${ROOT}/research/causal_biorthogonal_green_v1"
EVIDENCE="${ROOT}/evidence/causal_biorthogonal_green_v1"
CANDIDATE_MANIFEST="${ROOT}/evidence/hcmc_v1/independent_raw_native_20260922_verified/H02_R2026092212/context_bank/source_update_0001/candidate_manifest.csv"
PROBE_JSON="${ROOT}/evidence/causal_compositional_plume_world_model_v1/m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json"

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
TARGET_ROOT="${TARGET_ROOT:-/home/zyc/c0_5_real_gaden_bank_20260923}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
TMP_ROOT="${TMP_ROOT:-/home/zyc/bigreen_gate1a_tmp_20260924}"

BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"
OCCUPANCY="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
W2="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

EXPECTED_BINARY_SHA="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W2_ITER1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
EXPECTED_EXTRACTOR_SHA="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"

PREDICTION_SEEDS=(2026092401 2026092402)
ITERS=(100 150 200 250 300 350 400 450 500 550)
SIM_TIME="300.0"

mkdir -p "${EVIDENCE}" "${OUT_ROOT}" "${TMP_ROOT}"

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

[[ -f "${TARGET_ROOT}/S2_W2_A/spatial/concentration.npy" ]] || {
  echo "missing target S2_W2_A spatial field under ${TARGET_ROOT}" >&2; exit 5;
}
[[ -f "${TARGET_ROOT}/S2_W2_B/spatial/concentration.npy" ]] || {
  echo "missing target S2_W2_B spatial field under ${TARGET_ROOT}" >&2; exit 5;
}

python3 -m py_compile   "${RESEARCH}/prepare_gate1a_bank.py"   "${RESEARCH}/extract_gate1a_probe_vector.py"   "${RESEARCH}/rank_gate1a_exact_forward.py"

# Freeze/verify source bank. If resuming, rebuild in a temporary directory and
# require byte equality so a changed candidate manifest cannot silently mix
# with previous predictions.
if [[ ! -f "${OUT_ROOT}/gate1a_contract.json" || ! -f "${OUT_ROOT}/source_bank.tsv" ]]; then
  python3 "${RESEARCH}/prepare_gate1a_bank.py"     --candidate-manifest "${CANDIDATE_MANIFEST}"     --occupancy "${OCCUPANCY}"     --probe-json "${PROBE_JSON}"     --out "${OUT_ROOT}"
else
  VERIFY_DIR="${TMP_ROOT}/verify_bank_$$"
  rm -rf "${VERIFY_DIR}"
  mkdir -p "${VERIFY_DIR}"
  python3 "${RESEARCH}/prepare_gate1a_bank.py"     --candidate-manifest "${CANDIDATE_MANIFEST}"     --occupancy "${OCCUPANCY}"     --probe-json "${PROBE_JSON}"     --out "${VERIFY_DIR}" >/dev/null
  cmp -s "${VERIFY_DIR}/source_bank.tsv" "${OUT_ROOT}/source_bank.tsv" || {
    echo "source_bank.tsv drift on resume" >&2; exit 6;
  }
  cmp -s "${VERIFY_DIR}/gate1a_contract.json" "${OUT_ROOT}/gate1a_contract.json" || {
    echo "gate1a_contract.json drift on resume" >&2; exit 6;
  }
  rm -rf "${VERIFY_DIR}"
fi

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

valid_prediction() {
  local p="$1"
  [[ -f "${p}" ]] || return 1
  python3 - "${p}" <<'PY' >/dev/null 2>&1
import sys, numpy as np
p=sys.argv[1]
a=np.load(p,allow_pickle=False)
assert a.shape==(300,)
assert np.isfinite(a).all()
assert (a>=0).all()
PY
}

run_one() {
  local seed="$1" source_id="$2" sx="$3" sy="$4" sz="$5"
  local seed_root="${OUT_ROOT}/predictions/seed_${seed}"
  local log_root="${OUT_ROOT}/logs/seed_${seed}"
  local pred="${seed_root}/${source_id}.npy"
  local sidecar="${seed_root}/${source_id}.json"
  mkdir -p "${seed_root}" "${log_root}"

  if valid_prediction "${pred}" && [[ -f "${sidecar}" ]]; then
    printf 'SKIP %s seed=%s\n' "${source_id}" "${seed}"
    return 0
  fi

  local work="${TMP_ROOT}/${source_id}_${seed}"
  rm -rf "${work}"
  mkdir -p "${work}/realization" "${work}/spatial"
  ln -s "${OCCUPANCY}" "${work}/realization/OccupancyGrid3D.csv"

  local genlog="${log_root}/${source_id}.generation.log"
  set +e
  env GADEN_RNG_SEED="${seed}" "${BINARY}" --ros-args     -p verbose:=false     -p wait_preprocessing:=false     -p sim_time:="${SIM_TIME}"     -p time_step:=0.1     -p num_filaments_sec:=7     -p variable_rate:=true     -p filament_stop_steps:=0     -p ppm_filament_center:=10.0     -p filament_initial_std:=10.0     -p filament_growth_gamma:=15.0     -p filament_noise_std:=0.01     -p gas_type:=10     -p temperature:=298.0     -p pressure:=1.0     -p concentration_unit_choice:=1     -p occupancy3D_data:="${OCCUPANCY}"     -p fixed_frame:=map     -p wind_data:="${W2}"     -p wind_time_step:=1.0     -p allow_looping:=true     -p loop_from_step:=1     -p loop_to_step:=10     -p source_position_x:="${sx}"     -p source_position_y:="${sy}"     -p source_position_z:="${sz}"     -p save_results:=1     -p results_time_step:=0.5     -p results_min_time:=0.0     -p writeConcentrations:=false     -p results_location:="${work}/realization"     >"${genlog}" 2>&1
  local rc=$?
  set -e
  [[ "${rc}" -eq 0 ]] || {
    echo "${source_id} seed=${seed}: GADEN exit ${rc}" >&2; exit 20;
  }
  grep -q 'Filament simulator finished correctly!' "${genlog}" || {
    echo "${source_id} seed=${seed}: completion marker missing" >&2; exit 21;
  }

  local frame_count
  frame_count="$(find "${work}/realization" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
  [[ "${frame_count}" -eq 566 ]] || {
    echo "${source_id} seed=${seed}: expected 566 frames, got ${frame_count}" >&2; exit 22;
  }

  "${EXTRACTOR}"     "${work}/realization" "${work}/realization"     "${work}/spatial/concentration.npy" "${work}/spatial/metadata.json"     "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${ITERS[@]}"     >"${log_root}/${source_id}.extract.log" 2>&1

  python3 "${RESEARCH}/extract_gate1a_probe_vector.py"     --concentration "${work}/spatial/concentration.npy"     --contract "${OUT_ROOT}/gate1a_contract.json"     --out "${pred}" >/dev/null

  valid_prediction "${pred}" || {
    echo "${source_id} seed=${seed}: invalid prediction vector" >&2; exit 23;
  }

  local pred_sha gen_sha ext_sha
  pred_sha="$(sha256sum "${pred}" | awk '{print $1}')"
  gen_sha="$(sha256sum "${genlog}" | awk '{print $1}')"
  ext_sha="$(sha256sum "${log_root}/${source_id}.extract.log" | awk '{print $1}')"
  cat > "${sidecar}" <<EOF
{
  "source_id": "${source_id}",
  "source_xyz_m": [${sx}, ${sy}, ${sz}],
  "prediction_seed": ${seed},
  "prediction_sha256": "${pred_sha}",
  "generation_log_sha256": "${gen_sha}",
  "extract_log_sha256": "${ext_sha}",
  "frame_count": ${frame_count}
}
EOF
  rm -rf "${work}"
  printf 'DONE %s seed=%s\n' "${source_id}" "${seed}"
}

# Sequential by default because the frozen GADEN binary already uses many CPU
# threads. The loop is intentionally resume-safe.
for seed in "${PREDICTION_SEEDS[@]}"; do
  while IFS=$'\t' read -r source_id pmfs_i pmfs_j x_m y_m z_m gix giy giz parent_count parent_ids; do
    [[ "${source_id}" == "source_id" ]] && continue
    run_one "${seed}" "${source_id}" "${x_m}" "${y_m}" "${z_m}"
  done < "${OUT_ROOT}/source_bank.tsv"
done

RESULT="${EVIDENCE}/GATE1A_EXACT_FORWARD_RESULT_20260924.json"
set +e
python3 "${RESEARCH}/rank_gate1a_exact_forward.py"   --contract "${OUT_ROOT}/gate1a_contract.json"   --target-root "${TARGET_ROOT}"   --prediction-root "${OUT_ROOT}/predictions"   --out "${RESULT}"   | tee "${EVIDENCE}/GATE1A_EXACT_FORWARD_20260924.log"
rank_rc=${PIPESTATUS[0]}
set -e

{
  git -C "${ROOT}" rev-parse HEAD
  sha256sum     "${RESEARCH}/prepare_gate1a_bank.py"     "${RESEARCH}/extract_gate1a_probe_vector.py"     "${RESEARCH}/rank_gate1a_exact_forward.py"     "${ROOT}/research/causal_biorthogonal_green_v1/run_gate1a_exact_forward_vm.sh"     "${OUT_ROOT}/source_bank.tsv"     "${OUT_ROOT}/gate1a_contract.json"     "${RESULT}"
} > "${EVIDENCE}/GATE1A_SHA256_20260924.txt"

cat "${RESULT}"
exit "${rank_rc}"
