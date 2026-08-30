#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=${CTT_H01_OMP_NUM_THREADS:-4}
export OMP_DYNAMIC=FALSE
set -u

code=/home/zyc/CTT_H01_WIND_M1_CODE_20260830
out=${CTT_H01_SMOKE_OUT:-/dev/shm/CTT_H01_WIND_BANK_SMOKE_20260830_R1}
native_binary=${CTT_H01_NATIVE_BINARY:-/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream}
wind_binary=${CTT_H01_WIND_BINARY:-/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_wind_multistream}

python3 "$code/materialize_ctt_h01_wind_bank.py" \
  --placement-manifest /home/zyc/PF_DEI_V3_STREAM_BUILD/src/frozen_region_placement_manifest.json \
  --context-manifest /home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_manifest.json \
  --native-binary "$native_binary" \
  --wind-binary "$wind_binary" \
  --environment /home/zyc/rmfe_cl_env/H01/OccupancyGrid3D.csv \
  --schedule-root /home/zyc/PF_DEI_V3_TRAJECTORIES_20260828_R1 \
  --output-root "$out" \
  --workers 2 \
  --smoke

python3 - "$out" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
summary = json.loads((root / "bank_summary.json").read_text())
assert summary["verdict"] == "CTT_H01_WIND_BANK_SMOKE_PASS"
assert summary["file_count"] == 2
assert summary["scientific_gate_eligible"] is False
print("CTT_H01_WIND_BANK_SMOKE_POSTCHECK=PASS")
PY
