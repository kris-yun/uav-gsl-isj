#!/usr/bin/env bash
set -Eeuo pipefail

# One-shot House02 DEVELOPMENT run for M4-v3.
# This does not launch ROS, PMFS, GADEN plume generation, or a closed loop.
# It only exports the already-existing canonical dynamic winds and runs the
# preregistered D0 train/evaluate split.

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH="$(git -C "${ROOT}" branch --show-current)"
EXPECTED_BRANCH="research/m4-v3-interventional-evolution-propagator"
[[ "${BRANCH}" == "${EXPECTED_BRANCH}" ]] || {
  echo "Refuse D0 on branch '${BRANCH}'; expected '${EXPECTED_BRANCH}'" >&2
  exit 2
}

EVIDENCE="${ROOT}/evidence/causal_compositional_plume_world_model_v1"
RESEARCH="${ROOT}/research/causal_compositional_plume_world_model_v1"
BANK="${EVIDENCE}/c0_5_real_gaden_bank"
DYNAMIC="${EVIDENCE}/m4_v3_dynamic_wind_house02"
OUT="${EVIDENCE}/m4_v3_d0_house02_20260923"

CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OCC="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
W1="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
W2="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

for p in "${OCC}" "${W1}/wind_iteration_1" "${W2}/wind_iteration_1"; do
  [[ -e "${p}" ]] || { echo "missing frozen input: ${p}" >&2; exit 3; }
done

if [[ ! -d "${DYNAMIC}" ]]; then
  python "${RESEARCH}/export_m4_v3_dynamic_wind_sequence.py"     "${OCC}" "${W1}" "${W2}" "${DYNAMIC}"     --sensor-z 0.20 --wind-iteration-dt 1.0 --loop-from 1 --loop-to 10     | tee "${EVIDENCE}/M4_V3_DYNAMIC_WIND_EXPORT_20260923.log"
else
  echo "Using existing dynamic-wind export: ${DYNAMIC}"
fi

[[ -f "${DYNAMIC}/wind_sequence_manifest.json" ]] || {
  echo "dynamic wind manifest missing" >&2; exit 4;
}
[[ ! -e "${OUT}" ]] || {
  echo "Refuse to overwrite D0 output: ${OUT}" >&2
  exit 5
}

MODEL="${RESEARCH}/m4_v3_interventional_evolution.py"
D0="${RESEARCH}/m4_v3_d0_house02.py"

python "${D0}" train   --bank "${BANK}"   --dynamic-wind "${DYNAMIC}"   --model-script "${MODEL}"   --out "${OUT}"   | tee "${EVIDENCE}/M4_V3_D0_TRAIN_20260923.log"

python "${D0}" evaluate   --bank "${BANK}"   --dynamic-wind "${DYNAMIC}"   --model-script "${MODEL}"   --out "${OUT}"   | tee "${EVIDENCE}/M4_V3_D0_EVALUATE_20260923.log"

{
  sha256sum "${DYNAMIC}/wind_W1_sequence_z0p20.npy"
  sha256sum "${DYNAMIC}/wind_W2_sequence_z0p20.npy"
  sha256sum "${DYNAMIC}/wind_sequence_manifest.json"
  sha256sum "${OUT}/train_manifest.json"
  sha256sum "${OUT}/m4v3_seed1729.pt"
  sha256sum "${OUT}/m4v3_seed2718.pt"
  sha256sum "${OUT}/d0_result.json"
} > "${EVIDENCE}/M4_V3_D0_SHA256SUMS_20260923.txt"

cat "${OUT}/d0_result.json"
