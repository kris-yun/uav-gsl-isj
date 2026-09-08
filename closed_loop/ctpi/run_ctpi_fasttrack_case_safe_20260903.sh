#!/usr/bin/env bash
set -Eeo pipefail

# House-aware CTPI M1/M2/M3 fast-track paired runner.
#
# Scientific rule: this wrapper does not infer or tune the authoritative PMFS
# cadence.  STEPS_SOURCE_UPDATE, MAX_WARMUP_ITERATIONS and
# MIN_WARMUP_ITERATIONS are mandatory inputs recovered from the exact frozen
# paired PMFS runtime/parameter manifest.  The same values must be used for
# A0/F00/F01/F10/F11.

HOUSE="${HOUSE:?set HOUSE=H01,H02,H03 (or House01,House02,House03)}"
SEED="${SEED:?set SEED explicitly}"
SENSOR_SEED="${SENSOR_SEED:-12}"
ARM="${ARM:?set ARM=A0,F00,F01,F10,F11}"
RUN_ROOT="${RUN_ROOT:?set RUN_ROOT}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:?set PFDI_INSTALL_ROOT to the build of the current frozen commit}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:?recover STEPS_SOURCE_UPDATE from the authoritative paired PMFS manifest}"
MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS:?recover MAX_WARMUP_ITERATIONS from the authoritative paired PMFS manifest}"
MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS:?recover MIN_WARMUP_ITERATIONS from the authoritative paired PMFS manifest}"
INTEGRITY_REPORT="${INTEGRITY_REPORT:?set INTEGRITY_REPORT for this House bank}"
VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT:?set VGR_BRIDGE_SOURCE_ROOT to an audited vgr_bridge source overlay}"
ENV_PREFLIGHT="${ENV_PREFLIGHT:-}"
GEOMETRY_MANIFEST="${GEOMETRY_MANIFEST:-}"
QUALIFIED_HELPER="${QUALIFIED_HELPER:-}"

REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
BANK_ROOT_BASE="${BANK_ROOT_BASE:-/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1}"
CTPI_LAUNCH_FILE="${CTPI_LAUNCH_FILE:-${REPO_ROOT}/closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py}"
CTPI_PREFLIGHT_SCRIPT="${CTPI_PREFLIGHT_SCRIPT:-${REPO_ROOT}/tools/cpir_formal_preflight.py}"
DOMAIN_ID="${DOMAIN_ID:-230}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-1200}"
TIMEOUT_SEC="${TIMEOUT_SEC:-240.0}"
REALTIME_FACTOR="${REALTIME_FACTOR:-1.0}"
NAV_COMMAND_QUANTUM_S="${NAV_COMMAND_QUANTUM_S:-2.0}"
FRAME_QUERY_WAIT_SEC="${FRAME_QUERY_WAIT_SEC:-120}"
GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY="${GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY:-false}"
METHOD="${METHOD:-CTPI_CREL_TSDC_PIP}"
METHOD_FAMILY="${METHOD_FAMILY:-ctpi_three_module}"

python3 - "${TIMEOUT_SEC}" <<'PY_HORIZON'
import sys
v=float(sys.argv[1])
if abs(v-240.0)>1e-12:
    raise SystemExit('CTPI_FASTTRACK_TIMEOUT_MUST_BE_240_FOR_FROZEN_BANK_HORIZON')
PY_HORIZON

case "${HOUSE}" in
  H01|House01)
    HSHORT="H01"; HOUSE_LONG="House01"
    VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House01"
    CONFIG_ID="2,4-1_fast"
    SOURCE_X="-0.40"; SOURCE_Y="-2.90"; SOURCE_Z="-0.30"
    START_X="-3.17"; START_Y="-1.75"
    ENV_ID="VGR_House01"; SCENARIO_ID="H01_cfg_2_4_1_fast"
    GAS_BACKEND="raw_house1_snapshot"
    RAW_QUERY="${QUALIFIED_HELPER:-/dev/shm/house1_raw_query}"
    REALIZATION="${VGR_DATA}/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30"
    ;;
  H02|House02)
    HSHORT="H02"; HOUSE_LONG="House02"
    VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House02"
    CONFIG_ID="3,5-1_fast"
    SOURCE_X="0.00"; SOURCE_Y="-1.00"; SOURCE_Z="0.20"
    START_X="-0.50"; START_Y="-2.50"
    ENV_ID="VGR_House02"; SCENARIO_ID="H02_cfg_3_5_1_fast"
    GAS_BACKEND="gaden_player"
    RAW_QUERY="${QUALIFIED_HELPER:-/bin/true}"
    REALIZATION="${VGR_DATA}/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20"
    ;;
  H03|House03)
    HSHORT="H03"; HOUSE_LONG="House03"
    VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House03"
    CONFIG_ID="1-2,5_fast"
    SOURCE_X="-0.45"; SOURCE_Y="1.90"; SOURCE_Z="-0.10"
    START_X="2.00"; START_Y="0.00"
    ENV_ID="VGR_House03"; SCENARIO_ID="H03_cfg_1-2_5_fast"
    GAS_BACKEND="gaden_player"
    RAW_QUERY="${QUALIFIED_HELPER:-/bin/true}"
    REALIZATION="${VGR_DATA}/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10"
    ;;
  *) echo "CPIR_FORMAL_UNSUPPORTED_HOUSE=${HOUSE}" >&2; exit 2 ;;
esac

case "${ARM}" in
  A0) PFDI_MODE="off" ;;
  F00) PFDI_MODE="ctpi_f00" ;;
  F01) PFDI_MODE="ctpi_f01" ;;
  F10) PFDI_MODE="ctpi_f10" ;;
  F11) PFDI_MODE="ctpi_f11" ;;
  M1) PFDI_MODE="cer_m1" ;;
  M1M2) PFDI_MODE="cer_m1_m2" ;;
  M1R) PFDI_MODE="cer_ratio_m1" ;;
  M1M2R) PFDI_MODE="cer_ratio_m1_m2" ;;
  M1C) PFDI_MODE="cer_core_m1" ;;
  M1S) PFDI_MODE="cer_core_seq_m1" ;;
  M1P) PFDI_MODE="cer_core_stop_m1" ;;
  M1E) PFDI_MODE="cer_core_ensemble_m1" ;;
  M1F) PFDI_MODE="cer_core_eventtime_m1" ;;
  M1G) PFDI_MODE="cer_core_invariant_m1" ;;
  M1H) PFDI_MODE="cer_core_robust_m1" ;;
  *) echo "CTPI_FASTTRACK_UNSUPPORTED_ARM=${ARM}" >&2; exit 2 ;;
esac

BANK_ROOT="${BANK_ROOT:-${BANK_ROOT_BASE}/${HSHORT}}"
RUN_ID="${RUN_ID:-CTPI_${HSHORT}_S${SEED}_${ARM}_$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_DIR="${RUN_ROOT}/${HSHORT}_seed${SEED}_${ARM}"
CPIR_AUDIT_DIR="${RUN_DIR}/ctpi_audit"
PREFLIGHT_JSON="${RUN_DIR}/ctpi_formal_preflight.json"
ALGORITHM_BINARY="${PFDI_INSTALL_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
VGR_BRIDGE_CONTRACT="${VGR_BRIDGE_SOURCE_ROOT}/vgr_bridge/result_contract.py"

for path in "${CTPI_LAUNCH_FILE}" "${ALGORITHM_BINARY}" "${VGR_BRIDGE_CONTRACT}"; do
  [[ -e "${path}" ]] || { echo "CPIR_FORMAL_REQUIRED_PATH_MISSING=${path}" >&2; exit 3; }
done
if [[ -n "${ENV_PREFLIGHT}" ]]; then
  for path in "${ENV_PREFLIGHT}" "${GEOMETRY_MANIFEST}" "${QUALIFIED_HELPER}"; do
    [[ -e "${path}" ]] || { echo "CER_ENVIRONMENT_BINDING_MISSING=${path}" >&2; exit 3; }
  done
else
  for path in "${CTPI_PREFLIGHT_SCRIPT}" "${INTEGRITY_REPORT}"; do
    [[ -e "${path}" ]] || { echo "CPIR_FORMAL_REQUIRED_PATH_MISSING=${path}" >&2; exit 3; }
  done
  [[ -d "${BANK_ROOT}" ]] || { echo "CPIR_FORMAL_BANK_ROOT_MISSING=${BANK_ROOT}" >&2; exit 3; }
  [[ ! -e "${BANK_ROOT}/IN_PROGRESS" ]] || { echo "CPIR_FORMAL_BANK_STILL_IN_PROGRESS=${BANK_ROOT}" >&2; exit 3; }
fi
[[ -d "${VGR_DATA}" ]] || { echo "CPIR_FORMAL_VGR_DATA_MISSING=${VGR_DATA}" >&2; exit 3; }
if [[ "${HSHORT}" == "H01" ]]; then
  [[ -x "${RAW_QUERY}" ]] || { echo "CPIR_FORMAL_RAW_QUERY_MISSING=${RAW_QUERY}" >&2; exit 3; }
fi
[[ -d "${REALIZATION}" ]] || { echo "CPIR_FORMAL_REALIZATION_MISSING=${REALIZATION}" >&2; exit 3; }

[[ ! -e "${RUN_DIR}" ]] || { echo "CTPI_FASTTRACK_REFUSE_STALE_RUN_DIR=${RUN_DIR}" >&2; exit 70; }
mkdir -p "${RUN_DIR}" "${CPIR_AUDIT_DIR}"
if [[ -z "${ENV_PREFLIGHT}" ]]; then
python3 "${CTPI_PREFLIGHT_SCRIPT}" \
  --house "${HSHORT}" \
  --bank-root "${BANK_ROOT}" \
  --integrity-report "${INTEGRITY_REPORT}" \
  --steps-source-update "${STEPS_SOURCE_UPDATE}" \
  --max-warmup-iterations "${MAX_WARMUP_ITERATIONS}" \
  --min-warmup-iterations "${MIN_WARMUP_ITERATIONS}" \
  --json-out "${PREFLIGHT_JSON}" \
  >"${RUN_DIR}/cpir_preflight_stdout.json"

readarray -t PREFLIGHT_VALUES < <(python3 - "${PREFLIGHT_JSON}" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
assert p['verdict']=='CPIR_FORMAL_PREFLIGHT_PASS'
la=p['launch_args']
print(la['cpir_expected_bank_summary_sha256'])
print(la['cpir_expected_cell_manifest_sha256'])
PY
)
BANK_SUMMARY_SHA="${PREFLIGHT_VALUES[0]}"
CELL_MANIFEST_SHA="${PREFLIGHT_VALUES[1]}"
else
  BANK_SUMMARY_SHA=NOT_USED_EVENT_EVIDENCE
  CELL_MANIFEST_SHA=NOT_USED_EVENT_EVIDENCE
fi

mkdir -p "${RUN_DIR}"
ALGORITHM_SHA256="$(sha256sum "${ALGORITHM_BINARY}" | awk '{print $1}')"
VGR_BRIDGE_CONTRACT_SHA256="$(sha256sum "${VGR_BRIDGE_CONTRACT}" | awk '{print $1}')"
GIT_COMMIT="${GIT_COMMIT:-$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo UNKNOWN)}"
cat >"${RUN_DIR}/formal_runtime_manifest.json" <<EOF
{
  "contract": "CTPI_FASTTRACK_PAIRED_RUN_V0",
  "run_id": "${RUN_ID}",
  "house": "${HSHORT}",
  "seed": ${SEED},
  "algorithm_seed": ${SEED},
  "sensor_seed": ${SENSOR_SEED},
  "arm": "${ARM}",
  "pfdi_mode": "${PFDI_MODE}",
  "method": "${METHOD}",
  "method_family": "${METHOD_FAMILY}",
  "git_commit": "${GIT_COMMIT}",
  "algorithm_sha256": "${ALGORITHM_SHA256}",
  "vgr_bridge_source_root": "${VGR_BRIDGE_SOURCE_ROOT}",
  "vgr_bridge_contract_sha256": "${VGR_BRIDGE_CONTRACT_SHA256}",
  "bank_summary_sha256": "${BANK_SUMMARY_SHA}",
  "cell_manifest_sha256": "${CELL_MANIFEST_SHA}",
  "environment_preflight": "${ENV_PREFLIGHT}",
  "geometry_manifest": "${GEOMETRY_MANIFEST}",
  "steps_source_update": ${STEPS_SOURCE_UPDATE},
  "max_warmup_iterations": ${MAX_WARMUP_ITERATIONS},
  "min_warmup_iterations": ${MIN_WARMUP_ITERATIONS},
  "start_x": ${START_X},
  "start_y": ${START_Y},
  "gas_backend": "${GAS_BACKEND}",
  "realization": "${REALIZATION}",
  "config_id": "${CONFIG_ID}",
  "timeout_sec": ${TIMEOUT_SEC},
  "realtime_factor": ${REALTIME_FACTOR}
}
EOF

export ROS_DOMAIN_ID="${DOMAIN_ID}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_LOG_DIR="${RUN_DIR}/ros_log"
export TMPDIR="${RUN_DIR}/tmp"
mkdir -p "${ROS_LOG_DIR}" "${TMPDIR}"

source /opt/ros/humble/setup.bash
[[ -f /dev/shm/house1_msgs_install/setup.bash ]] && source /dev/shm/house1_msgs_install/setup.bash
[[ -f "${PFDI_INSTALL_ROOT}/install/setup.bash" ]] && source "${PFDI_INSTALL_ROOT}/install/setup.bash"

if [[ "${HSHORT}" == "H02" || "${HSHORT}" == "H03" ]]; then
  for setup in \
    /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_msgs/share/gaden_msgs/local_setup.bash \
    /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common/share/gaden_common/local_setup.bash \
    /home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_player/share/gaden_player/local_setup.bash; do
    [[ -f "${setup}" ]] || { echo "CPIR_FORMAL_GADEN_SETUP_MISSING=${setup}" >&2; exit 4; }
    source "${setup}"
  done
fi

# Preserve the known working GADEN/VGR loader order from the frozen paired runner.
export AMENT_PREFIX_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:${PFDI_INSTALL_ROOT}/deps/install/vgr_bridge:${PFDI_INSTALL_ROOT}/deps/install/gmrf_msgs:${PFDI_INSTALL_ROOT}/deps/install/gsl_actions:${PFDI_INSTALL_ROOT}/deps/install/olfaction_msgs:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_player:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_msgs:/dev/shm/house1_vgr_install:/home/zyc/ros2_ws/install/gmrf_wind_mapping:/opt/ros/humble:${AMENT_PREFIX_PATH:-}"
export CMAKE_PREFIX_PATH="${AMENT_PREFIX_PATH}"
export PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:/dev/shm/house1_vgr_install/lib/vgr_bridge:${PATH}"
export PYTHONPATH="${VGR_BRIDGE_SOURCE_ROOT}:${PFDI_INSTALL_ROOT}/deps/install/gsl_actions/local/lib/python3.10/dist-packages:${PFDI_INSTALL_ROOT}/deps/install/gmrf_msgs/local/lib/python3.10/dist-packages:${PFDI_INSTALL_ROOT}/deps/install/olfaction_msgs/local/lib/python3.10/dist-packages:/opt/ros/humble/local/lib/python3.10/dist-packages:/opt/ros/humble/lib/python3.10/site-packages:/dev/shm/house1_msgs_install/local/lib/python3.10/dist-packages:/dev/shm/house2_gaden_install/gaden_msgs/local/lib/python3.10/dist-packages:/dev/shm/house1_vgr_bridge:/home/zyc/ros2_ws/src/vgr_bridge:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server/lib:${PFDI_INSTALL_ROOT}/deps/install/gmrf_msgs/lib:${PFDI_INSTALL_ROOT}/deps/install/gsl_actions/lib:${PFDI_INSTALL_ROOT}/deps/install/olfaction_msgs/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_player/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_msgs/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_build/gaden_common/third_party/gaden_core/third_party/libbsc:/dev/shm/house1_vgr_install/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/opt/ros/humble/lib:${LD_LIBRARY_PATH:-}"

python3 - "${RUN_DIR}/vgr_bridge_runtime_preflight.json" "${METHOD}" "${VGR_BRIDGE_SOURCE_ROOT}" <<'PY_VGR_BRIDGE'
import hashlib
import json
import sys
from pathlib import Path

from vgr_bridge import gsl_benchmark_runner, result_contract

output = Path(sys.argv[1])
method = sys.argv[2]
expected_root = Path(sys.argv[3]).resolve()
if method not in result_contract.CANONICAL:
    raise SystemExit(f"CTPI_G2_M12_NON_CANONICAL_METHOD={method}")
contract_path = Path(result_contract.__file__).resolve()
runner_path = Path(gsl_benchmark_runner.__file__).resolve()
if expected_root not in contract_path.parents or expected_root not in runner_path.parents:
    raise SystemExit(
        "CTPI_G2_M12_VGR_BRIDGE_IMPORT_ESCAPE="
        f"expected_root:{expected_root},contract:{contract_path},runner:{runner_path}"
    )
payload = {
    "verdict": "CTPI_G2_M12_VGR_BRIDGE_PREFLIGHT_PASS",
    "method": method,
    "contract_path": str(contract_path),
    "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
    "runner_path": str(runner_path),
    "runner_sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
}
output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(payload["verdict"])
PY_VGR_BRIDGE

CHILD_PIDS=()
cleanup_children() {
  for pid in "${CHILD_PIDS[@]:-}"; do kill -TERM "${pid}" 2>/dev/null || true; done
  sleep 1
  for pid in "${CHILD_PIDS[@]:-}"; do kill -KILL "${pid}" 2>/dev/null || true; done
}
trap cleanup_children EXIT INT TERM

if [[ "${HSHORT}" == "H02" || "${HSHORT}" == "H03" ]]; then
  PLAYER=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_player/lib/gaden_player/player
  [[ -x "${PLAYER}" ]] || { echo "CPIR_FORMAL_GADEN_PLAYER_MISSING=${PLAYER}" >&2; exit 4; }
  "${PLAYER}" --ros-args -r __node:=gaden_player \
    -p num_simulators:=1 -p simulation_data_0:="${REALIZATION}" \
    -p occupancyFile:="${VGR_DATA}/OccupancyGrid3D.csv" -p initial_iteration:=0 \
    -p player_freq:=1.0 -p manual_iteration_mode:=true \
    >"${RUN_DIR}/gaden_player.log" 2>&1 &
  CHILD_PIDS+=("$!")

  python3 "${VGR_BRIDGE_SOURCE_ROOT}/vgr_bridge/wind_value_server.py" --ros-args \
    -r __node:=wind_value_server -p vgr_data_path:="${VGR_DATA}" -p config_id:="${CONFIG_ID}" \
    >"${RUN_DIR}/wind_value_server.log" 2>&1 &
  CHILD_PIDS+=("$!")

  frame_query_deadline=$((SECONDS + FRAME_QUERY_WAIT_SEC))
  until ros2 service type /frame_query >/dev/null 2>&1; do
    if ! kill -0 "${CHILD_PIDS[0]}" 2>/dev/null; then
      echo "CPIR_FORMAL_GADEN_PLAYER_EXITED_BEFORE_FRAME_QUERY" >&2; exit 65
    fi
    if (( SECONDS >= frame_query_deadline )); then
      echo "CPIR_FORMAL_FRAME_QUERY_TIMEOUT_SEC=${FRAME_QUERY_WAIT_SEC}" >&2; exit 66
    fi
    sleep 2
  done
  echo "CPIR_FORMAL_FRAME_QUERY_READY HOUSE=${HSHORT} DOMAIN=${ROS_DOMAIN_ID}"
fi

ARGS=(
  "vgr_data_path:=${VGR_DATA}" "config_id:=${CONFIG_ID}" "algorithm:=PMFS"
  "method:=${METHOD}" "method_family:=${METHOD_FAMILY}" "ablation_id:=${ARM}"
  "run_id:=${RUN_ID}" "run_uuid:=${RUN_ID}" "run_dir:=${RUN_DIR}" "output_dir:=${RUN_ROOT}"
  "git_commit:=${GIT_COMMIT}" "code_manifest_sha256:=${ALGORITHM_SHA256}"
  "environment_id:=${ENV_ID}" "scenario_id:=${SCENARIO_ID}" "dataset:=${ENV_ID}"
  "source_config:=official_gaden_source" "wind_config:=official_gaden_wind"
  "sensor_config:=fopdt_tau1p2_dead0p4_noise0" "start_config:=frozen_native_start"
  "source_x:=${SOURCE_X}" "source_y:=${SOURCE_Y}" "source_z:=${SOURCE_Z}"
  "start_x:=${START_X}" "start_y:=${START_Y}" "seed:=${SEED}" "sensor_seed:=${SENSOR_SEED}" "flight_height:=0.3"
  "timeout_sec:=${TIMEOUT_SEC}" "path_budget_m:=-1.0" "scale:=3" "useWindGroundTruth:=false"
  "convergence_thr:=-1.0" "sourceDiscriminationPower:=1.0" "refineFraction:=0.25"
  "stepsSourceUpdate:=${STEPS_SOURCE_UPDATE}" "maxRegionSize:=5" "deltaTime:=0.2" "noiseSTDev:=0.5"
  "iterationsToRecord:=200" "maxWarmupIterations:=${MAX_WARMUP_ITERATIONS}" "minWarmupIterations:=${MIN_WARMUP_ITERATIONS}"
  "blurSigmaX:=0.0" "blurSigmaY:=0.0" "hitPriorProbability:=0.1" "th_gas_present:=0.1"
  "maxUpdatesPerStop:=8" "kernelSigma:=0.5" "kernelStretchConstant:=1.5"
  "confidenceMeasurementWeight:=0.5" "confidenceSigmaSpatial:=0.5" "localEstimationWindowSize:=2"
  "openMoveSetExpasion:=5" "explorationProbability:=0.05" "initialExplorationMoves:=2" "distanceWeight:=0.15"
  "markers_height:=0.2" "measurement_settle_samples:=0" "measurement_block_samples:=10"
  "measurement_deduplicate_sim_timestamps:=true"
  "sensor_model_mode:=dynamic" "gaden_iteration_mode:=seeded_time_replay" "realtime_factor:=${REALTIME_FACTOR}"
  "sim_stop_at_s:=-1.0" "nav_command_quantum_s:=${NAV_COMMAND_QUANTUM_S}"
  "gas_backend:=${GAS_BACKEND}" "raw_query_executable:=${RAW_QUERY}"
  "raw_gas_results:=${REALIZATION}"
  "cstar_environment_preflight:=${ENV_PREFLIGHT}" "cstar_geometry_manifest:=${GEOMETRY_MANIFEST}"
  "cstar_house:=${HSHORT}" "gmrf_map_yaml_file:=$(python3 - "${GEOMETRY_MANIFEST}" "${HSHORT}" <<'PY_MAP'
import json,sys
print(json.load(open(sys.argv[1]))[sys.argv[2]]['map_yaml_path'])
PY_MAP
)"
  "gmrf_update_on_new_observation_only:=${GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY}"
  "p2_shadow_enabled:=false" "tadm_enabled:=false" "pfdi_mode:=${PFDI_MODE}"
  "cpir_lookup_root:=${BANK_ROOT}" "cpir_audit_directory:=${CPIR_AUDIT_DIR}"
  "cpir_expected_house:=${HSHORT}" "cpir_expected_bank_summary_sha256:=${BANK_SUMMARY_SHA}"
  "cpir_expected_cell_manifest_sha256:=${CELL_MANIFEST_SHA}" "cpir_integrity_report:=${INTEGRITY_REPORT}"
  "cpir_expected_steps_source_update:=${STEPS_SOURCE_UPDATE}"
  "cpir_expected_max_warmup_iterations:=${MAX_WARMUP_ITERATIONS}"
  "cpir_expected_min_warmup_iterations:=${MIN_WARMUP_ITERATIONS}"
  "context_bank_export_enabled:=false"
  "ctpi_m3_horizontal_speed_mps:=0.4"
  "navigation_trace_file:=${RUN_DIR}/navigation_trace.csv"
  "source_estimate_trace_file:=${RUN_DIR}/source_estimate_trace.csv"
  "use_sdbe:=1" "use_iasc:=1" "use_sepf:=1" "use_sage:=0" "use_beacon:=0"
  "use_beacon_tr:=0" "use_pcrd:=0" "use_pgn:=0" "use_tpp:=0" "use_hmm:=0"
  "temperature_tau:=1.0" "tau_adaptive:=0" "infoTaxis:=false" "use_infotaxis:=false"
)

echo "CTPI_FASTTRACK_CASE_START HOUSE=${HSHORT} SEED=${SEED} ARM=${ARM} MODE=${PFDI_MODE} DOMAIN=${ROS_DOMAIN_ID}"
set +e
setsid ros2 launch "${CTPI_LAUNCH_FILE}" "${ARGS[@]}" >"${RUN_DIR}/launch.log" 2>&1 &
launch_pid=$!
deadline=$((SECONDS + OUTER_DEADLINE_SEC))
while kill -0 "${launch_pid}" 2>/dev/null; do
  if [[ -s "${RUN_DIR}/run_status.json" ]]; then
    sleep 3
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    sleep 5
    kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "CPIR_FORMAL_OUTER_DEADLINE_SEC=${OUTER_DEADLINE_SEC}" >&2
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    sleep 15
    kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    break
  fi
  sleep 2
done
wait "${launch_pid}"
status=$?
set -e

if [[ ! -s "${RUN_DIR}/run_status.json" ]]; then
  echo "CTPI_FASTTRACK_CASE_NO_TERMINAL_STATUS HOUSE=${HSHORT} SEED=${SEED} ARM=${ARM} STATUS=${status}" >&2
  exit 71
fi
python3 - "${RUN_DIR}/run_status.json" <<'PY_STATUS'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
if not isinstance(p,dict) or not p.get('status'):
    raise SystemExit('CTPI_FASTTRACK_TERMINAL_STATUS_INVALID')
print('CTPI_FASTTRACK_TERMINAL_STATUS='+str(p['status']))
PY_STATUS

echo "CTPI_FASTTRACK_CASE_COMPLETE HOUSE=${HSHORT} SEED=${SEED} ARM=${ARM} RUN_DIR=${RUN_DIR}"
