#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=4
export OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
set -u

code=/home/zyc/CTT_M2_PROSPECTIVE_GATE_CODE_20260831_R6
formal=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R2_FORMAL_PERSISTED
placement=/home/zyc/PF_DEI_V3_STREAM_BUILD/src/frozen_region_placement_manifest.json
contexts=/home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_manifest.json
native=/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream
native_source=/home/zyc/PF_DEI_V3_STREAM_BUILD/src/pf_dei_v3_native_multistream.cpp
rng_hook=/home/zyc/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core/src/RngHook.cpp
rng_math=/home/zyc/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp
running_sim=/home/zyc/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp
environment=/home/zyc/rmfe_cl_env/H01/OccupancyGrid3D.csv
schedules=/home/zyc/PF_DEI_V3_TRAJECTORIES_20260828_R1
bank=${CTT_M2_BANK_OUT:-/home/zyc/CTT_M2_FIXED_U_PROSPECTIVE_K_BANK_20260831_R3}
evidence=${CTT_M2_EVIDENCE_OUT:-/home/zyc/CTT_M2_FIXED_U_PROSPECTIVE_K_EVIDENCE_20260831_R5}
generation_null=$code/CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V2.json
evaluation_null=$code/CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V3.json
evaluation_addendum=$code/CTT_M2_FIXED_U_PROSPECTIVE_K_EVALUATION_REPAIR_FREEZE_20260831.json

cd "$code"
sha256sum -c CTT_M2_PROSPECTIVE_GATE_CODE_SHA256SUMS.txt
python3 -m py_compile ./*.py
python3 - <<'PY'
import json
from pathlib import Path

for name in (
    "CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V2.json",
    "CTT_M2_FIXED_U_PROSPECTIVE_K_NULL_MAPS_V3.json",
    "CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PREREGISTRATION_20260831.json",
    "CTT_M2_PROSPECTIVE_SEED_PROVENANCE_20260831.json",
    "CTT_M2_FIXED_U_PROSPECTIVE_K_EVALUATION_REPAIR_FREEZE_20260831.json",
):
    with Path(name).open("r", encoding="utf-8") as handle:
        json.load(handle)
print("CTT_M2_FROZEN_JSON_PARSE_CONTRACT=PASS")
PY
python3 freeze_ctt_m2_fixed_u_transport_null_maps.py --selftest
python3 freeze_ctt_m2_fixed_u_transport_null_maps_v3.py --selftest
python3 materialize_ctt_h01_fixed_u_transport_gate.py --selftest
python3 evaluate_ctt_h01_fixed_u_transport_gate.py --selftest

test "$(sha256sum "$native" | cut -d' ' -f1)" = ad0772d994875d009a1e8720928a9f40db56c20f6bf83a03b309049696a7ead4
test "$(sha256sum "$native_source" | cut -d' ' -f1)" = 7a1570637eac1ca97758baddd05e7762b47fcd2e12afd77239698bd1132b01b4
test "$(sha256sum "$rng_hook" | cut -d' ' -f1)" = 826fbe242e152a09d03bc50849f6b882b58b0b3fc41a6b3e595c3811b20a9131
test "$(sha256sum "$rng_math" | cut -d' ' -f1)" = 374ec0ed56cbd38ff5bc017ad668a831c8da5c19e34b5b81186e4e8a5eee4c05
test "$(sha256sum "$running_sim" | cut -d' ' -f1)" = b699492b816980b583301e025cdbd04d5b9adedff90b9419593b2160a091ae2a

if [[ "${PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo CTT_M2_PROSPECTIVE_GATE_PREFLIGHT=PASS
  exit 0
fi

python3 materialize_ctt_h01_fixed_u_transport_gate.py \
  --formal-bank "$formal" \
  --placement-manifest "$placement" \
  --context-manifest "$contexts" \
  --preregistration "$code/CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PREREGISTRATION_20260831.json" \
  --null-maps "$generation_null" \
  --seed-provenance "$code/CTT_M2_PROSPECTIVE_SEED_PROVENANCE_20260831.json" \
  --native-binary "$native" \
  --native-source "$native_source" \
  --rng-hook-source "$rng_hook" \
  --rng-math-source "$rng_math" \
  --running-simulation-source "$running_sim" \
  --environment "$environment" \
  --schedule-root "$schedules" \
  --output-root "$bank" \
  --workers "${CTT_M2_WORKERS:-3}"

python3 evaluate_ctt_h01_fixed_u_transport_gate.py \
  --formal-bank "$formal" \
  --fixed-bank "$bank" \
  --placement-manifest "$placement" \
  --preregistration "$code/CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PREREGISTRATION_20260831.json" \
  --null-maps "$evaluation_null" \
  --evaluation-addendum "$evaluation_addendum" \
  --schedule-root "$schedules" \
  --output "$evidence"

echo CTT_M2_PROSPECTIVE_GATE_TERMINAL="$(cat "$evidence/VERDICT.txt")"
