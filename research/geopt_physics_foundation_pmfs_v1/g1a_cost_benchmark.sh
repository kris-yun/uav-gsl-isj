#!/usr/bin/env bash
set -Ee -o pipefail
BUILD_ROOT=/home/zyc/hcmc_gaden_seed_build_20260922
BINARY="$BUILD_ROOT/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
LIBBSC_DIR="$BUILD_ROOT/build/gaden_common/third_party/gaden_core/third_party/libbsc"
CANONICAL_ROOT=/mnt/hgfs/workspace/GADEN_files/scenarios
HOUSE=House02
OCC="$CANONICAL_ROOT/House02/OccupancyGrid3D.csv"
WIND="$CANONICAL_ROOT/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
OUT_ROOT=/mnt/hgfs/workspace/M6_G1_STAGE1_COST_20260923
SOURCE_X=-1.942730188369751
SOURCE_Y=-1.300879955291748
SOURCE_Z=0.20
SEED=2026092311
mkdir -p "$OUT_ROOT"
[[ -x "$BINARY" && -f "$OCC" && -f "$WIND/wind_iteration_0" ]] || { echo COST_PRECHECK_FAIL; exit 2; }
set +u
source /opt/ros/humble/setup.bash
source "$BUILD_ROOT/install/setup.bash"
set -u
export LD_LIBRARY_PATH="$LIBBSC_DIR:$BUILD_ROOT/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
for SIM_TIME in 30.0 120.0 300.0; do
  LABEL="H02_newsource_train1_${SIM_TIME%.*}s"
  OUT="$OUT_ROOT/$LABEL"
  mkdir -p "$OUT"
  BEFORE=$(df -Pk / | tail -1 | awk '{print $4}')
  START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  set +e
  /usr/bin/time -v -o "$OUT/time_v.txt" env GADEN_RNG_SEED="$SEED" "$BINARY" --ros-args \
    -p verbose:=false -p wait_preprocessing:=false \
    -p sim_time:="$SIM_TIME" -p time_step:=0.1 \
    -p num_filaments_sec:=7 -p variable_rate:=true -p filament_stop_steps:=0 \
    -p ppm_filament_center:=10.0 -p filament_initial_std:=10.0 \
    -p filament_growth_gamma:=15.0 -p filament_noise_std:=0.01 \
    -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
    -p concentration_unit_choice:=1 \
    -p occupancy3D_data:="$OCC" -p fixed_frame:=map \
    -p wind_data:="$WIND" \
    -p wind_time_step:=1.0 -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
    -p source_position_x:="$SOURCE_X" \
    -p source_position_y:="$SOURCE_Y" \
    -p source_position_z:="$SOURCE_Z" \
    -p save_results:=0 -p results_time_step:=0.5 -p results_min_time:=0.0 \
    -p writeConcentrations:=false -p results_location:="$OUT/results" \
    >"$OUT/generation.log" 2>&1
  RC=$?
  set -e
  AFTER=$(df -Pk / | tail -1 | awk '{print $4}')
  END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  FRAMES=$(find "$OUT/results" -type f -name 'iteration_*' 2>/dev/null | wc -l)
  WIND_FILES=$(find "$OUT/results/wind" -type f 2>/dev/null | wc -l)
  BYTES=$(du -sb "$OUT" | awk '{print $1}')
  cat > "$OUT/result.env" <<EOF
case_id=$LABEL
house=$HOUSE
source_x=$SOURCE_X
source_y=$SOURCE_Y
source_z=$SOURCE_Z
plume_seed=$SEED
sim_time_s=$SIM_TIME
exit_code=$RC
start_utc=$START
end_utc=$END
root_free_kb_before=$BEFORE
root_free_kb_after=$AFTER
output_bytes=$BYTES
iteration_frame_count=$FRAMES
wind_file_count=$WIND_FILES
save_results=0
num_filaments_sec=7
nominal_releases=$(python3 -c "print(7*float('$SIM_TIME'))")
occupancy_sha256=$(sha256sum "$OCC" | awk '{print $1}')
wind0_sha256=$(sha256sum "$WIND/wind_iteration_0" | awk '{print $1}')
generator_sha256=$(sha256sum "$BINARY" | awk '{print $1}')
EOF
  if [[ "$RC" -ne 0 ]] || ! grep -Fq 'Filament simulator finished correctly' "$OUT/generation.log"; then
    echo "COST_CASE_FAIL $LABEL rc=$RC" >&2
    exit 10
  fi
  echo "COST_CASE_PASS $LABEL rc=$RC frames=$FRAMES bytes=$BYTES"
done
printf 'M6_G1A_COST_PASS\n'