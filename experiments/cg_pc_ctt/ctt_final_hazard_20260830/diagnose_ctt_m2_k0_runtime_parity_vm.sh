#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
set -u

native=/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream
environment=/home/zyc/rmfe_cl_env/H01/OccupancyGrid3D.csv
wind=/home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_00_train
schedules=/home/zyc/PF_DEI_V3_TRAJECTORIES_20260828_R1/H01/reserved
old=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R2_FORMAL_PERSISTED/context_00/member_00/quadtree_0_0_2_2.bin
out=/home/zyc/CTT_M2_K0_RUNTIME_PARITY_DIAGNOSTIC_20260831
test ! -e "$out"
mkdir -p "$out"

run_one() {
  local threads=$1
  local seeded_workers=$2
  local target="$out/omp${threads}_workerseed${seeded_workers}.bin"
  if [[ "$seeded_workers" == 1 ]]; then
    GADEN_RNG_SEED=101 OMP_NUM_THREADS="$threads" OMP_DYNAMIC=FALSE \
      "$native" "$environment" "$wind" \
      -7.100000381469727 -7.430000305175781 -0.569 101 0.2 "$target" \
      "$schedules/trajectory_seed_4001.csv" \
      "$schedules/trajectory_seed_4002.csv" \
      "$schedules/trajectory_seed_4003.csv" \
      "$schedules/trajectory_seed_4004.csv" \
      "$schedules/trajectory_seed_4005.csv" >/dev/null
  else
    env -u GADEN_RNG_SEED OMP_NUM_THREADS="$threads" OMP_DYNAMIC=FALSE \
      "$native" "$environment" "$wind" \
      -7.100000381469727 -7.430000305175781 -0.569 101 0.2 "$target" \
      "$schedules/trajectory_seed_4001.csv" \
      "$schedules/trajectory_seed_4002.csv" \
      "$schedules/trajectory_seed_4003.csv" \
      "$schedules/trajectory_seed_4004.csv" \
      "$schedules/trajectory_seed_4005.csv" >/dev/null
  fi
  local old_hash new_hash
  old_hash=$(sha256sum "$old" | cut -d' ' -f1)
  new_hash=$(sha256sum "$target" | cut -d' ' -f1)
  printf 'OMP=%s WORKER_SEED=%s MATCH=%s HASH=%s\n' \
    "$threads" "$seeded_workers" "$([[ "$old_hash" == "$new_hash" ]] && echo true || echo false)" "$new_hash"
}

for threads in 1 2 3 4 6 8 12; do run_one "$threads" 0; done
for threads in 1 2 3 4 6 8 12; do run_one "$threads" 1; done
sha256sum "$old"
