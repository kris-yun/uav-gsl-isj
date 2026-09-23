#!/usr/bin/env bash
set -Eeuo pipefail

# Fixed before looking at any model result. Ten post-warmup snapshots cover
# 50--275 s of the 300 s simulation at the simulator's 0.5 s save interval.
ROOT="${ROOT:-/home/zyc/c0_5_real_gaden_bank_20260923}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"
BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
MIN_X="-5.39273"
MIN_Y="-7.45088"
CELL="0.1"
COARSE="1"
FLIGHT_Z="0.20"
GX="83"
GY="119"
ITERS=(100 150 200 250 300 350 400 450 500 550)
CELLS=(S1_W1_A S1_W1_B S1_W2_A S1_W2_B S2_W1_A S2_W1_B S2_W2_A S2_W2_B)

[[ -x "${EXTRACTOR}" ]] || { echo "missing extractor: ${EXTRACTOR}" >&2; exit 2; }
set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
for cell_id in "${CELLS[@]}"; do
  raw="${ROOT}/${cell_id}/realization"
  out="${ROOT}/${cell_id}/spatial"
  [[ -d "${raw}" ]] || { echo "missing raw realization: ${raw}" >&2; exit 3; }
  [[ -e "${raw}/OccupancyGrid3D.csv" ]] || ln -s /mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv "${raw}/OccupancyGrid3D.csv"
  [[ ! -e "${out}" ]] || { echo "refuse overwrite: ${out}" >&2; exit 4; }
  mkdir -p "${out}"
  /usr/bin/time -v -o "${out}/extract_time.txt" "${EXTRACTOR}" \
    "${raw}" "${raw}" "${out}/concentration.npy" "${out}/metadata.json" \
    "${MIN_X}" "${MIN_Y}" "${CELL}" "${COARSE}" "${FLIGHT_Z}" "${GX}" "${GY}" "${ITERS[@]}" \
    >"${out}/extract.log" 2>&1
  sha256sum "${out}/concentration.npy" "${out}/metadata.json" "${out}/extract.log" > "${out}/SHA256SUMS"
done

cat > "${ROOT}/spatial_export_contract.tsv" <<EOF
extractor	${EXTRACTOR}
extractor_sha256	$(sha256sum "${EXTRACTOR}" | awk '{print $1}')
grid_min_xy_m	${MIN_X},${MIN_Y}
cell_m	${CELL}
coarse	${COARSE}
gx_gy	${GX},${GY}
flight_sensor_z_m	${FLIGHT_Z}
iteration_indices	$(IFS=,; echo "${ITERS[*]}")
simulation_time_s	50,75,100,125,150,175,200,225,250,275
obstacle_mask_source	/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv
sampling_method	GADEN core PlaybackSimulation::SampleConcentration
EOF
sha256sum "${ROOT}/spatial_export_contract.tsv" > "${ROOT}/spatial_export_contract.sha256"
printf 'C0_5_SPATIAL_EXPORT_DONE\n'
