#!/usr/bin/env bash
set -Eeuo pipefail

code=/home/zyc/materialize_cpir_fullgrid_lookup.py
placement=/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/frozen_region_placement_manifest.json
native=/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream
historical=/home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827
root=/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1

test -f "$code"
test -f "$placement"
test -x "$native"
mkdir -p "$root/logs"

run_house() {
  local house="$1" env_file="$2" wind_dir="$3" observation="$4"
  python3 "$code" \
    --house "$house" \
    --cell-csv "$historical/House${house#H}/seed1/off/final_posterior.csv" \
    --placement-manifest "$placement" \
    --native-binary "$native" \
    --environment "$env_file" \
    --wind-dir "$wind_dir" \
    --observation-realization "$observation" \
    --output "$root/$house" \
    --workers 1 \
    >"$root/logs/$house.log" 2>&1
}

run_house H01 \
  /home/zyc/rmfe_cl_env/H01/OccupancyGrid3D.csv \
  /home/zyc/rmfe_cl_env/H01/wind \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House01/gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/iteration_0 &
p1=$!

run_house H02 \
  /home/zyc/H02_ACIT_TRANSPORT_MISMATCH_AUDIT_WORK/assets/House02/OccupancyGrid3D.csv \
  /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/converted_wind_house02 \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/iteration_0 &
p2=$!

run_house H03 \
  /home/zyc/rmfe_cl_env/H03/OccupancyGrid3D.csv \
  /home/zyc/rmfe_cl_env/H03/wind \
  /mnt/hgfs/workspace/GADEN_files/scenarios/House03/gas_simulations/1-2,5_fast/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10/iteration_0 &
p3=$!

printf 'CPIR_LOOKUP_PIDS=%s,%s,%s\n' "$p1" "$p2" "$p3"
wait "$p1"
wait "$p2"
wait "$p3"

for house in H01 H02 H03; do
  test -f "$root/$house/bank_summary.json"
  test ! -e "$root/$house/IN_PROGRESS"
done
printf 'CPIR_CROSSHOUSE_LOOKUP=PASS\n'
