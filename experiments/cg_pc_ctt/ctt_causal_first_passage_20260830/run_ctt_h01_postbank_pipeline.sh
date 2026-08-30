#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=4
export OMP_DYNAMIC=FALSE
set -u

code=/home/zyc/CTT_H01_WIND_M1_CODE_20260830
bank_tag=${CTT_H01_BANK_TAG:-R2}
volatile_bank=/dev/shm/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}
bank=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}_PERSISTED
evidence=/home/zyc/CTT_H01_WIND_M1_EVIDENCE_20260830_${bank_tag}
monitor=/home/zyc/CTT_H01_BANK_MONITOR_20260830_${bank_tag}

while [[ -f "$volatile_bank/IN_PROGRESS" ]]; do
  if ! pgrep -f 'materialize_ctt_h01_wind_bank.py.*CTT_H01_WIND_BANK_FULL_20260830_R1' >/dev/null; then
    echo CTT_H01_POSTBANK_ABORT_MATERIALIZER_NOT_RUNNING
    exit 20
  fi
  sleep 15
done

test -f "$volatile_bank/bank_summary.json"
test -f "$volatile_bank/FILE_SHA256.tsv"
test ! -e "$evidence"
test -f "$monitor/MONITOR_PASS.json"
test ! -f "$monitor/MONITOR_FAIL.json"

CTT_H01_BANK_TAG="$bank_tag" bash "$code/persist_ctt_h01_bank.sh"
test -f "$bank/bank_summary.json"
test -f "$bank/FILE_SHA256.tsv"

export CTT_H01_SMOKE_OUT=/dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_A
bash "$code/run_ctt_h01_bank_smoke.sh"

export CTT_H01_SMOKE_OUT=/dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_A_REPEAT
bash "$code/run_ctt_h01_bank_smoke.sh"

export CTT_H01_SMOKE_OUT=/dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_RELEASE
export CTT_H01_NATIVE_BINARY=/home/zyc/CTT_H01_RELEASE_BUILD_20260830/install/bin/pf_dei_v3_native_multistream
export CTT_H01_WIND_BINARY=/home/zyc/CTT_H01_RELEASE_BUILD_20260830/install/bin/pf_dei_v3_native_wind_multistream
bash "$code/run_ctt_h01_bank_smoke.sh"
unset CTT_H01_NATIVE_BINARY CTT_H01_WIND_BINARY

mkdir "$evidence"
cp "$code/CTT_H01_PREGENERATION_FREEZE_20260830.json" "$evidence/"
cp "$code/CTT_H01_PHYSICAL_MANIFEST_FREEZE_20260830.json" "$evidence/"

python3 "$code/audit_ctt_h01_wind_bank_g0.py" \
  --bank "$bank" \
  --placement-manifest /home/zyc/PF_DEI_V3_STREAM_BUILD/src/frozen_region_placement_manifest.json \
  --carrier-manifest /home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/carriers/H01_persistent_carriers.csv \
  --context-manifest /home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_manifest.json \
  --schedule-root /home/zyc/PF_DEI_V3_TRAJECTORIES_20260828_R1 \
  --smoke-a /dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_A \
  --smoke-b /dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_A_REPEAT \
  --release-smoke /dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_CPU12_OMP4_FORMAL_${bank_tag}_RELEASE \
  --pre-vcpu-reference /home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R1_PRE_VCPU_CHECKPOINT/context_00/member_00/quadtree_0_0_2_2.bin \
  --authoritative-sensor /home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/sensor_model.py \
  --output "$evidence/g0"

python3 "$code/train_eval_ctt_h01_wind_factorized_first_passage.py" \
  --bank "$bank" \
  --support /home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/carriers/H01_persistent_carriers.csv \
  --schedule-root /home/zyc/PF_DEI_V3_TRAJECTORIES_20260828_R1 \
  --output "$evidence/model"

echo CTT_H01_POSTBANK_PIPELINE=PASS
