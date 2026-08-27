#!/usr/bin/env bash
set -Eeuo pipefail

# Materialize H02_RECONSTRUCTED_CHALLENGE_V1 only. This never reads or recreates
# the lost historical hard-28. Override paths explicitly if the VM layout differs.

binary=${CTT_BUILDER:-/home/zyc/ctt_v13_build_20260826/build/gsl_server/ctt_trace_bank_builder}
carriers=${H02_CARRIER_MANIFEST:-/tmp/h02_reconstructed_v1_20260827/carrier_manifest.csv}
manifest=${H02_CONTEXT_MANIFEST:-/tmp/h02_reconstructed_v1_20260827/H02_RECONSTRUCTED_CONTEXT_MANIFEST.csv}
root=${H02_RECONSTRUCTED_ROOT:-/home/zyc/H02_RECONSTRUCTED_CHALLENGE_V1_20260827_r1}
expected_binary=31d81e18e41319769751d328adca04f92232fda7967ed86ae6a205026a3f99b4
expected_carriers=06dd0f91bc837a2e0bb698f11ce802045ac42f3957ff222e5e7c61488bc3fcc4

[[ "$(sha256sum "$binary" | awk '{print $1}')" == "$expected_binary" ]]
[[ "$(sha256sum "$carriers" | awk '{print $1}')" == "$expected_carriers" ]]
[[ -f "$manifest" ]]
[[ ! -e "$root" ]]
mkdir -p "$root/tasks" "$root/logs" "$root/banks"

set +u
source /opt/ros/humble/setup.bash
source /dev/shm/house1_msgs_install/setup.bash
source /home/zyc/ros2_ws/install/gmrf_msgs/share/gmrf_msgs/local_setup.bash
set -u

tail -n +2 "$manifest" > "$root/tasks/all.tsv"
awk -F, 'NR % 4 == 1 {print > "'"$root"'/tasks/task_0.tsv"} NR % 4 == 2 {print > "'"$root"'/tasks/task_1.tsv"} NR % 4 == 3 {print > "'"$root"'/tasks/task_2.tsv"} NR % 4 == 0 {print > "'"$root"'/tasks/task_3.tsv"}' "$root/tasks/all.tsv"

worker() {
  local task_file="$1"
  export OMP_NUM_THREADS=1
  while IFS=, read -r case_id context_dir run_uuid seed update rest; do
    [[ -n "$case_id" ]] || continue
    local context_bank out
    context_bank="$(dirname "$context_dir")"
    out="$root/banks/${case_id}_seed${seed}_u$(printf '%04d' "$update")"
    [[ ! -e "$out" ]] || { echo "DUPLICATE_OUTPUT $out" >&2; return 1; }
    "$binary" "$context_bank" "$carriers" "$out" "$update" 0 >"$root/logs/${case_id}.stdout" 2>"$root/logs/${case_id}.stderr"
    [[ "$(find "$out/records" -type f -name '*.cttbin' | wc -l)" -eq 1608 ]] || { echo "RECORD_COUNT_FAIL $case_id" >&2; return 1; }
    grep -q '"source_truth_used": false' "$out/ctt_trace_bank_contract.json"
    grep -q '"method_seed": 20260818' "$out/ctt_trace_bank_contract.json"
    grep -q '"transport_substream": 6077111455669390931' "$out/ctt_trace_bank_contract.json"
    grep -q '"transport_members": 8' "$out/ctt_trace_bank_contract.json"
    grep -q '"timesteps": 200' "$out/ctt_trace_bank_contract.json"
    grep -q '"delta_time": 0.2' "$out/ctt_trace_bank_contract.json"
    grep -q '"noise_standard_deviation": 0.5' "$out/ctt_trace_bank_contract.json"
  done < "$task_file"
}

worker "$root/tasks/task_0.tsv" & p0=$!
worker "$root/tasks/task_1.tsv" & p1=$!
worker "$root/tasks/task_2.tsv" & p2=$!
worker "$root/tasks/task_3.tsv" & p3=$!
wait "$p0" "$p1" "$p2" "$p3"

expected_contexts=$(( $(wc -l < "$manifest") - 1 ))
expected_records=$(( expected_contexts * 201 * 8 ))
[[ "$(find "$root/banks" -type f -name '*.cttbin' | wc -l)" -eq "$expected_records" ]]
sha256sum "$manifest" "$carriers" "$binary" > "$root/freeze_input_sha256.txt"
echo "H02_RECONSTRUCTED_CHALLENGE_V1_BANK_REBUILD=PASS contexts=$expected_contexts records=$expected_records"
