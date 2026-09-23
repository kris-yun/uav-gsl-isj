#!/usr/bin/env bash
set -Ee -o pipefail

# Fresh VGR run root and isolated official-PMFS binary. No old R2 path is writable.
ROOT="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
HOUSE="${HOUSE:-House01}"
SEED="${SEED:-0}"
STAGE="${RECOVERY_STAGE:-R0}"
ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-211}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-1800}"
case "${STAGE}" in R0|R2|R3) ;; *) echo "unsupported stage" >&2; exit 64 ;; esac
case "${SEED}" in 0|1) ;; *) echo "unsupported frozen seed" >&2; exit 65 ;; esac
if (( ROS_DOMAIN_ID < 0 || ROS_DOMAIN_ID > 232 )); then
  echo "Fast DDS ROS_DOMAIN_ID must be <=232" >&2; exit 66
fi
case "${HOUSE}" in
  House01)
    CONFIG_ID='2,4-1_fast'; SOURCE_X=-0.40; SOURCE_Y=-2.90; SOURCE_Z=-0.30
    START_X=-3.17; START_Y=-1.75; ENV_ID=VGR_House01; SCENARIO_ID=H01_cfg_2_4_1_fast
    GAS_BACKEND=raw_house1_snapshot
    RAW_QUERY="${RAW_QUERY:-/home/zyc/hcmc_gaden_seed_build_20260922/house1_raw_query}"
    ;;
  House02)
    CONFIG_ID='3,5-1_fast'; SOURCE_X=0.00; SOURCE_Y=-1.00; SOURCE_Z=0.20
    START_X=-0.50; START_Y=-2.50; ENV_ID=VGR_House02; SCENARIO_ID=H02_cfg_3_5_1_fast
    GAS_BACKEND=gaden_player; RAW_QUERY=/bin/true
    REALIZATION="/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20"
    ;;
  House03)
    CONFIG_ID='1-2,5_fast'; SOURCE_X=-0.45; SOURCE_Y=1.90; SOURCE_Z=-0.10
    START_X=2.00; START_Y=0.00; ENV_ID=VGR_House03; SCENARIO_ID=H03_cfg_1-2_5_fast
    GAS_BACKEND=gaden_player; RAW_QUERY=/bin/true
    REALIZATION="/mnt/hgfs/workspace/GADEN_files/scenarios/House03/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10"
    ;;
  *) echo "unsupported House" >&2; exit 67 ;;
esac
VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/${HOUSE}"
WIND_DIR="${VGR_DATA}/wind_simulations/${CONFIG_ID}"
[[ -d "${WIND_DIR}" ]] || { echo "missing wind data: ${WIND_DIR}" >&2; exit 68; }
[[ $(find "${WIND_DIR}" -maxdepth 1 -type f -name '*.csv' | wc -l) -gt 0 ]] || {
  echo "no VGR wind CSV files" >&2; exit 69;
}
[[ -x "${RAW_QUERY}" ]] || { echo "missing raw query executable" >&2; exit 70; }

BIN="${ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
LAUNCH="${ROOT}/vgr_native_pmfs_recovery_20260923.launch.py"
PROBE="${ROOT}/probe_native_wind_service_20260923.py"
VERIFY="${ROOT}/verify_native_wind_parity_20260923.py"
WIND_SERVER=/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py
for path in "${BIN}" "${LAUNCH}" "${PROBE}" "${VERIFY}" "${WIND_SERVER}"; do
  [[ -f "${path}" ]] || { echo "missing runtime file: ${path}" >&2; exit 71; }
done
[[ -x "${BIN}" ]] || exit 72
grep -R -l -- '-DUSE_GADEN' "${ROOT}/build/gsl_server/CMakeFiles" >/dev/null 2>&1 || {
  echo "USE_GADEN missing from compile files" >&2; exit 73;
}

source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source "${ROOT}/install/setup.bash"
set -u
export ROS_DOMAIN_ID RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="/home/zyc/ros2_ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
if ldd "${RAW_QUERY}" | grep -Fq 'not found'; then
  echo "raw-query runtime libraries unresolved" >&2; exit 73
fi
RUN_ID="${RUN_ID:-NATIVE_RECOVERY_${STAGE}_${HOUSE}_S${SEED}_$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_DIR="${ROOT}/runs/${RUN_ID}"
[[ ! -e "${RUN_DIR}" ]] || { echo "run root exists; refusing overwrite: ${RUN_DIR}" >&2; exit 74; }
mkdir -p "${RUN_DIR}" "${RUN_DIR}/ros_log"
export ROS_LOG_DIR="${RUN_DIR}/ros_log"
export NATIVE_RECOVERY_WIND_QUERY_CSV="${RUN_DIR}/wind_query.csv"
export NATIVE_RECOVERY_WIND_UPDATE_CSV="${RUN_DIR}/wind_source_update.csv"
export NATIVE_RECOVERY_MEASUREMENT_EVENTS_CSV="${RUN_DIR}/measurement_events.csv"
export NATIVE_RECOVERY_MEASURED_MAP_CSV="${RUN_DIR}/measured_map_at_update.csv"
export NATIVE_RECOVERY_CANDIDATES_CSV="${RUN_DIR}/frozen_candidate_geometry.csv"
export NATIVE_RECOVERY_UPDATE_COMPLETE_FILE="${RUN_DIR}/source_update_complete.txt"

CHILD_PIDS=()
cleanup() {
  local pid
  for pid in "${CHILD_PIDS[@]:-}"; do kill -TERM "${pid}" 2>/dev/null || true; done
}
trap cleanup EXIT INT TERM

if [[ "${GAS_BACKEND}" == gaden_player ]]; then
  GADEN_PLAYER_BINARY="${GADEN_PLAYER_BINARY:-/dev/shm/house2_gaden_install/gaden_player/lib/gaden_player/player}"
  [[ -x "${GADEN_PLAYER_BINARY}" && -d "${REALIZATION}" ]] || {
    echo "GADEN player or House realization unavailable" >&2; exit 75;
  }
  "${GADEN_PLAYER_BINARY}" --ros-args -r __node:=gaden_player \
    -p num_simulators:=1 -p simulation_data_0:="${REALIZATION}" \
    -p occupancyFile:="${VGR_DATA}/OccupancyGrid3D.csv" -p initial_iteration:=0 \
    -p player_freq:=1.0 -p manual_iteration_mode:=true \
    >"${RUN_DIR}/gaden_player.log" 2>&1 &
  CHILD_PIDS+=("$!")
  deadline=$((SECONDS + 120))
  until [[ "$(ros2 service type /frame_query 2>/dev/null)" == 'gaden_msgs/srv/FrameQuery' ]]; do
    kill -0 "${CHILD_PIDS[-1]}" 2>/dev/null || { echo "GADEN player exited" >&2; exit 76; }
    (( SECONDS < deadline )) || { echo "frame_query timeout" >&2; exit 77; }
    sleep 2
  done
fi

[[ -z "$(ros2 service type /wind_value 2>/dev/null)" ]] || {
  echo "pre-existing /wind_value in ROS domain; refusing mixed provenance" >&2; exit 78;
}
python3 -u "${WIND_SERVER}" --ros-args -r __node:=wind_value_server \
  -p vgr_data_path:="${VGR_DATA}" -p config_id:="${CONFIG_ID}" \
  >"${RUN_DIR}/wind_value_server.log" 2>&1 &
CHILD_PIDS+=("$!")
deadline=$((SECONDS + 60))
until [[ "$(ros2 service type /wind_value 2>/dev/null)" == 'gaden_msgs/srv/WindPosition' ]]; do
  kill -0 "${CHILD_PIDS[-1]}" 2>/dev/null || { echo "wind server exited" >&2; exit 79; }
  (( SECONDS < deadline )) || { echo "wind service type timeout" >&2; exit 80; }
  sleep 2
done
python3 "${PROBE}" --x "${START_X}" --y "${START_Y}" --z 0.3 \
  --output "${RUN_DIR}/wind_service_probe.json" >"${RUN_DIR}/wind_service_probe.log" 2>&1

ARGS=(
  "vgr_data_path:=${VGR_DATA}" "config_id:=${CONFIG_ID}" "house:=${HOUSE}"
  "environment_id:=${ENV_ID}" "scenario_id:=${SCENARIO_ID}"
  "source_x:=${SOURCE_X}" "source_y:=${SOURCE_Y}" "source_z:=${SOURCE_Z}"
  "start_x:=${START_X}" "start_y:=${START_Y}" "flight_height:=0.3"
  "seed:=${SEED}" "run_id:=${RUN_ID}" "run_dir:=${RUN_DIR}"
  "timeout_sec:=300.0" "realtime_factor:=1.0"
  "gas_backend:=${GAS_BACKEND}" "raw_query_executable:=${RAW_QUERY}"
)
printf '%s\n' "${ARGS[@]}" >"${RUN_DIR}/launch_args.txt"
export RUN_DIR RUN_ID HOUSE SEED STAGE BIN LAUNCH WIND_SERVER ROOT
python3 - <<'PY'
import hashlib, importlib.util, json, os
from pathlib import Path
run = Path(os.environ['RUN_DIR'])
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
args = dict(line.strip().split(':=', 1) for line in (run/'launch_args.txt').read_text().splitlines())
spec = importlib.util.spec_from_file_location('native_recovery_launch', os.environ['LAUNCH'])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
effective_args = dict(module.DEFAULTS)
effective_args.update(args)
manifest = dict(contract='NATIVE_PMFS_BASELINE_RECOVERY_V1', stage=os.environ['STAGE'],
    house=os.environ['HOUSE'], seed=int(os.environ['SEED']), run_id=os.environ['RUN_ID'],
    useWindGroundTruth_requested=True, USE_GADEN_compiled=True,
    wind_service='/wind_value', wind_service_type='gaden_msgs/srv/WindPosition',
    algorithm_binary=os.environ['BIN'], algorithm_sha256=sha(os.environ['BIN']),
    launch_file=os.environ['LAUNCH'], launch_sha256=sha(os.environ['LAUNCH']),
    wind_server_source=os.environ['WIND_SERVER'], wind_server_sha256=sha(os.environ['WIND_SERVER']),
    gmrf_in_native_forward=False, launch_args=effective_args,
    ground_truth_use='offline evaluation/logging only; distanceThreshold=-1',
    evaluation_budget_s=300, smoke_stop='first completed PMFS source update' if os.environ['STAGE']=='R0' else None)
(run/'runtime_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
PY

echo "NATIVE_RECOVERY_START stage=${STAGE} house=${HOUSE} seed=${SEED} run=${RUN_DIR}"
setsid ros2 launch "${LAUNCH}" "${ARGS[@]}" >"${RUN_DIR}/launch.log" 2>&1 &
LAUNCH_PID=$!
deadline=$((SECONDS + OUTER_DEADLINE_SEC))
completed=0
while kill -0 "${LAUNCH_PID}" 2>/dev/null; do
  if [[ "${STAGE}" == R0 && -s "${RUN_DIR}/source_update_complete.txt" ]]; then
    if (( $(wc -l < "${RUN_DIR}/source_update_complete.txt") >= 1 )); then
      completed=1
      echo 'R0_SOURCE_UPDATE_OBSERVED' >"${RUN_DIR}/smoke_status.txt"
      kill -INT -- "-${LAUNCH_PID}" 2>/dev/null || true
      break
    fi
  elif [[ "${STAGE}" != R0 && -s "${RUN_DIR}/run_status.json" ]]; then
    completed=1; break
  fi
  (( SECONDS < deadline )) || { echo 'NATIVE_RECOVERY_OUTER_DEADLINE' >&2; break; }
  sleep 2
done
wait "${LAUNCH_PID}" || true
(( completed == 1 )) || { echo "recovery run did not reach stage completion" >&2; exit 81; }
grep -Fq 'NATIVE_RECOVERY_WIND_PATH=GADEN_GROUND_TRUTH' "${RUN_DIR}/launch.log" || {
  echo "no runtime GADEN wind path marker" >&2; exit 82;
}
python3 "${VERIFY}" "${RUN_DIR}" --house "${HOUSE}" --seed "${SEED}" \
  >"${RUN_DIR}/wind_parity_verify.log" 2>&1 || {
  cat "${RUN_DIR}/wind_parity_verify.log" >&2; exit 83;
}
echo "NATIVE_RECOVERY_${STAGE}_WIND_PARITY_PASS run=${RUN_DIR}"
