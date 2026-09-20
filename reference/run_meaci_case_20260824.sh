#!/usr/bin/env bash
set -Eeo pipefail

# Frozen ME-ACI House01/House02/House03 closed-loop runner.
# The algorithm binary is isolated; vgr_bridge and message packages are the
# existing VM runtime overlays.  No source code or authoritative Main-V8 tree
# is modified by this script.

HOUSE="${HOUSE:?set HOUSE=House01, House02, or House03}"
SEED="${SEED:?set SEED=0 or 1}"
ARM="${ARM:?set ARM=off or on}"
RUN_ROOT="${RUN_ROOT:?set RUN_ROOT=/dev/shm/meaci_runs_20260824}"
PFDI_MODE="${PFDI_MODE:-off}"
TNQC_MODE="${TNQC_MODE:-off}"
case "${TNQC_MODE}" in
  off|shadow|fused|only) ;;
  *) echo "unsupported TNQC_MODE=${TNQC_MODE}; use off, shadow, fused, or only" >&2; exit 2 ;;
esac
TNQC_SUFFIX=""
if [[ "${TNQC_MODE}" != "off" ]]; then
  TNQC_SUFFIX="_tnqc_${TNQC_MODE}"
fi
RUN_DIR="${RUN_ROOT}/${HOUSE}_seed${SEED}_${ARM}_${PFDI_MODE}${TNQC_SUFFIX}"
RUN_ID="${RUN_ID:-PFDI_${HOUSE}_S${SEED}_${ARM}_${PFDI_MODE}${TNQC_SUFFIX}_$(date -u +%Y%m%dT%H%M%SZ)}"
DOMAIN_ID="${DOMAIN_ID:-230}"
TADM_REPLICAS="${TADM_REPLICAS:-8}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-900}"
TARGET_SOURCE_UPDATES="${TARGET_SOURCE_UPDATES:-0}"
TARGET_ACCEPTED_UPDATES="${TARGET_ACCEPTED_UPDATES:-0}"
POSTERIOR_GUIDANCE_WEIGHT="${POSTERIOR_GUIDANCE_WEIGHT:-0}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:-/dev/shm/meaci_online_20260824}"
GMRF_INSTALL_ROOT="${GMRF_INSTALL_ROOT:-}"
GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY="${GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY:-false}"
GMRF_PREFIX=""
if [[ -n "${GMRF_INSTALL_ROOT}" ]]; then
  GMRF_PREFIX="${GMRF_INSTALL_ROOT}/install/gmrf_wind_mapping"
fi

if [[ "${HOUSE}" == "House01" ]]; then
  VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House01"
  CONFIG_ID="2,4-1_fast"
  SOURCE_X="-0.40"; SOURCE_Y="-2.90"; SOURCE_Z="-0.30"
  START_X="-3.17"; START_Y="-1.75"
  ENV_ID="VGR_House01"; SCENARIO_ID="H01_cfg_2_4_1_fast"
  # Offline config 2,4-1 belongs to the held-out H02 configuration group and
  # is evaluated with the set-0 prior calibrated on group H01.
  TADM_PRIOR_SET="0"
  GAS_BACKEND="raw_house1_snapshot"
  RAW_QUERY="/dev/shm/house1_raw_query"
elif [[ "${HOUSE}" == "House02" ]]; then
  VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House02"
  CONFIG_ID="3,5-1_fast"
  SOURCE_X="0.00"; SOURCE_Y="-1.00"; SOURCE_Z="0.20"
  START_X="-0.50"; START_Y="-2.50"
  ENV_ID="VGR_House02"; SCENARIO_ID="H02_cfg_3_5_1_fast"
  # House02 is outside the offline House01 configuration bank; retain the
  # frozen operational set-1 mapping used by the original closed-loop bridge.
  TADM_PRIOR_SET="1"
  GAS_BACKEND="gaden_player"
  # House02 uses gaden_player; the launch contract still requires a
  # non-empty raw_query_executable token even though this backend never
  # invokes it.  Keep this as a contract placeholder, not a data source.
  RAW_QUERY="/bin/true"
  REALIZATION="${VGR_DATA}/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20"
elif [[ "${HOUSE}" == "House03" ]]; then
  VGR_DATA="/mnt/hgfs/workspace/GADEN_files/scenarios/House03"
  CONFIG_ID="1-2,5_fast"
  SOURCE_X="-0.45"; SOURCE_Y="1.90"; SOURCE_Z="-0.10"
  START_X="2.00"; START_Y="0.00"
  ENV_ID="VGR_House03"; SCENARIO_ID="H03_cfg_1-2_5_fast"
  # House03 is a transfer evaluation: keep the predeclared set-1 prior;
  # do not fit or tune this prior from House03 truth.
  TADM_PRIOR_SET="1"
  GAS_BACKEND="gaden_player"
  RAW_QUERY="/bin/true"
  REALIZATION="${VGR_DATA}/gas_simulations/${CONFIG_ID}/FilamentSimulation_gasType_10_sourcePosition_-0.45_1.90_-0.10"
else
  echo "unsupported HOUSE=${HOUSE}" >&2
  exit 2
fi

if [[ "${ARM}" == "on" || "${ARM}" == "off_matched" ]]; then
  TADM_ENABLED="true"
  TADM_DIR="${RUN_DIR}/tadm"
else
  TADM_ENABLED="false"
  TADM_DIR="/tmp/tadm_disabled"
fi

mkdir -p "${RUN_DIR}"
export ROS_LOG_DIR="${ROS_LOG_DIR:-${RUN_DIR}/ros_log}"
export TMPDIR="${TMPDIR:-${RUN_DIR}/tmp}"
mkdir -p "${ROS_LOG_DIR}" "${TMPDIR}"
PROVENANCE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PROVENANCE_LOCAL="$(date +%Y-%m-%dT%H:%M:%S%z)"
HOSTNAME_VALUE="$(hostname)"
ALGORITHM_BINARY="${PFDI_INSTALL_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
ALGORITHM_SHA256="$(sha256sum "${ALGORITHM_BINARY}" 2>/dev/null | awk '{print $1}' || true)"
cat > "${RUN_DIR}/runtime_manifest.json" <<EOF
{
  "contract": "${RUN_CONTRACT:-MEACI_CLOSED_LOOP_V1}",
  "run_id": "${RUN_ID}",
  "house": "${HOUSE}",
  "seed": ${SEED},
  "arm": "${ARM}",
  "pfdi_mode": "${PFDI_MODE}",
  "tnqc_mode": "${TNQC_MODE}",
  "ros_domain_id": ${DOMAIN_ID},
  "vm_hostname": "${HOSTNAME_VALUE}",
  "provenance_utc": "${PROVENANCE_UTC}",
  "provenance_local": "${PROVENANCE_LOCAL}",
  "algorithm_binary": "${ALGORITHM_BINARY}",
  "algorithm_sha256": "${ALGORITHM_SHA256}",
  "timeout_sec": "${TIMEOUT_SEC:-300.0}",
  "outer_deadline_sec": "${OUTER_DEADLINE_SEC}",
  "target_source_updates": "${TARGET_SOURCE_UPDATES}",
  "target_accepted_updates": "${TARGET_ACCEPTED_UPDATES}",
  "steps_source_update": "${STEPS_SOURCE_UPDATE:-10}",
  "tadm_replicas": "${TADM_REPLICAS}",
  "realtime_factor": "${REALTIME_FACTOR:-1.0}"
}
EOF
export ROS_DOMAIN_ID="${DOMAIN_ID}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
source /opt/ros/humble/setup.bash
source /dev/shm/house1_msgs_install/setup.bash
if [[ -n "${GMRF_PREFIX}" && -f "${GMRF_PREFIX}/local_setup.bash" ]]; then
  source "${GMRF_PREFIX}/local_setup.bash"
fi
if [[ -n "${GMRF_PREFIX}" ]]; then
  export AMENT_PREFIX_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:${GMRF_PREFIX}:/dev/shm/house1_vgr_install:/dev/shm/house1_msgs_install:/home/zyc/ros2_ws/install/gmrf_wind_mapping:/home/zyc/ros2_ws/install:/opt/ros/humble"
else
  export AMENT_PREFIX_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:/dev/shm/house1_vgr_install:/dev/shm/house1_msgs_install:/home/zyc/ros2_ws/install/gmrf_wind_mapping:/home/zyc/ros2_ws/install:/opt/ros/humble"
fi
export CMAKE_PREFIX_PATH="${AMENT_PREFIX_PATH}"
export PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:/dev/shm/house1_vgr_install/lib/vgr_bridge:${PATH}"
export PYTHONPATH="/opt/ros/humble/local/lib/python3.10/dist-packages:/opt/ros/humble/lib/python3.10/site-packages:/dev/shm/house1_msgs_install/local/lib/python3.10/dist-packages:/dev/shm/house2_gaden_install/gaden_msgs/local/lib/python3.10/dist-packages:/dev/shm/house1_vgr_bridge:/home/zyc/ros2_ws/src/vgr_bridge:${PYTHONPATH:-}"
if [[ "${HOUSE}" == "House02" || "${HOUSE}" == "House03" ]]; then
  source /dev/shm/house2_gaden_install/gaden_msgs/share/gaden_msgs/local_setup.bash
  source /dev/shm/house2_gaden_install/gaden_common/share/gaden_common/local_setup.bash
  source /dev/shm/house2_gaden_install/gaden_player/share/gaden_player/local_setup.bash
fi
set -u
if [[ -n "${GMRF_PREFIX}" ]]; then
  export AMENT_PREFIX_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:${GMRF_PREFIX}:/dev/shm/house2_gaden_install/gaden_player:/dev/shm/house2_gaden_install/gaden_common:/dev/shm/house2_gaden_install/gaden_msgs:/dev/shm/house1_vgr_install:/dev/shm/house1_msgs_install:/home/zyc/ros2_ws/install/gmrf_wind_mapping:/home/zyc/ros2_ws/install:/opt/ros/humble"
else
  export AMENT_PREFIX_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:/dev/shm/house2_gaden_install/gaden_player:/dev/shm/house2_gaden_install/gaden_common:/dev/shm/house2_gaden_install/gaden_msgs:/dev/shm/house1_vgr_install:/dev/shm/house1_msgs_install:/home/zyc/ros2_ws/install/gmrf_wind_mapping:/home/zyc/ros2_ws/install:/opt/ros/humble"
fi
export CMAKE_PREFIX_PATH="${AMENT_PREFIX_PATH}"
if [[ -n "${GMRF_PREFIX}" ]]; then
  export LD_LIBRARY_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:${GMRF_PREFIX}/lib:/dev/shm/house2_gaden_install/gaden_player/lib:/dev/shm/house2_gaden_install/gaden_common/lib:/dev/shm/house2_gaden_install/gaden_msgs/lib:/dev/shm/house2_gaden_build/gaden_common/third_party/gaden_core/third_party/libbsc:/dev/shm/house1_msgs_install/lib:/dev/shm/house1_vgr_install/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/home/zyc/ros2_ws/install/lib:/opt/ros/humble/lib:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="${PFDI_INSTALL_ROOT}/install/gsl_server:/dev/shm/house2_gaden_install/gaden_player/lib:/dev/shm/house2_gaden_install/gaden_common/lib:/dev/shm/house2_gaden_install/gaden_msgs/lib:/dev/shm/house2_gaden_build/gaden_common/third_party/gaden_core/third_party/libbsc:/dev/shm/house1_msgs_install/lib:/dev/shm/house1_vgr_install/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/home/zyc/ros2_ws/install/lib:/opt/ros/humble/lib:${LD_LIBRARY_PATH:-}"
fi

CHILD_PIDS=()
cleanup_children() {
  for pid in "${CHILD_PIDS[@]:-}"; do
    kill -TERM "${pid}" 2>/dev/null || true
  done
  sleep 1
  for pid in "${CHILD_PIDS[@]:-}"; do
    kill -KILL "${pid}" 2>/dev/null || true
  done
}
trap cleanup_children EXIT INT TERM

if [[ "${HOUSE}" == "House02" || "${HOUSE}" == "House03" ]]; then
  # House02 has no raw-query executable.  Use the already generated official
  # realization through the existing GADEN player and wind-value server.
  nohup /dev/shm/house2_gaden_install/gaden_player/lib/gaden_player/player --ros-args -r __node:=gaden_player \
    -p num_simulators:=1 -p simulation_data_0:="${REALIZATION}" \
    -p occupancyFile:="${VGR_DATA}/OccupancyGrid3D.csv" -p initial_iteration:=0 \
    -p player_freq:=1.0 -p manual_iteration_mode:=true \
    >"${RUN_DIR}/gaden_player.log" 2>&1 &
  CHILD_PIDS+=("$!")
  # The existing vgr_bridge executable is valid but its old install metadata
  # is incomplete, so call the installed console script directly.
  nohup python3 /home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py --ros-args -r __node:=wind_value_server \
    -p vgr_data_path:="${VGR_DATA}" -p config_id:="${CONFIG_ID}" \
    >"${RUN_DIR}/wind_value_server.log" 2>&1 &
  CHILD_PIDS+=("$!")
  # Do not launch vgr_sim_node on a fixed wall-clock sleep.  GADEN can take
  # longer than 15 s to load a large realization, and VGR's FrameQueryWorker
  # otherwise exits after its own 10 s service wait.  Wait for the service in
  # this ROS domain and fail closed if our own player exits first.
  FRAME_QUERY_WAIT_SEC="${FRAME_QUERY_WAIT_SEC:-120}"
  frame_query_deadline=$((SECONDS + FRAME_QUERY_WAIT_SEC))
  while ! ros2 service type /frame_query >/dev/null 2>&1; do
    if ! kill -0 "${CHILD_PIDS[0]}" 2>/dev/null; then
      echo "PFDI_GADEN_PLAYER_EXITED_BEFORE_FRAME_QUERY_READY" >&2
      exit 65
    fi
    if (( SECONDS >= frame_query_deadline )); then
      echo "PFDI_FRAME_QUERY_READY_TIMEOUT_SEC=${FRAME_QUERY_WAIT_SEC}" >&2
      exit 66
    fi
    sleep 2
  done
  echo "PFDI_GADEN_FRAME_QUERY_READY DOMAIN=${ROS_DOMAIN_ID}"
fi

LAUNCH="${PFDI_INSTALL_ROOT}/launch/vgr_gsl_pmfs_pfdi.launch.py"

ARGS=(
  "vgr_data_path:=${VGR_DATA}" "config_id:=${CONFIG_ID}" "algorithm:=PMFS"
  "method:=B4_PMFS_official" "method_family:=proposed_ablation" "ablation_id:=${ARM}"
  "run_id:=${RUN_ID}" "run_uuid:=${RUN_ID}" "run_dir:=${RUN_DIR}"
  "output_dir:=${RUN_ROOT}" "environment_id:=${ENV_ID}" "scenario_id:=${SCENARIO_ID}"
  "dataset:=${HOUSE}" "source_config:=official_gaden_source" "wind_config:=official_gaden_wind"
  "sensor_config:=fopdt_tau1p2_dead0p4_noise0" "start_config:=frozen_native_start"
  "source_x:=${SOURCE_X}" "source_y:=${SOURCE_Y}" "source_z:=${SOURCE_Z}"
  "start_x:=${START_X}" "start_y:=${START_Y}" "seed:=${SEED}" "flight_height:=0.3"
  "timeout_sec:=${TIMEOUT_SEC:-300.0}" "path_budget_m:=-1.0" "scale:=3" "useWindGroundTruth:=false"
  "convergence_thr:=-1.0" "sourceDiscriminationPower:=1.0" "refineFraction:=0.25"
  # Keep the frozen PMFS cadence by default.  Acceleration experiments may
  # override only this scheduler variable (e.g. STEPS_SOURCE_UPDATE=3),
  # leaving the warmup, simulator horizon, replicas, and likelihood fixed.
  "stepsSourceUpdate:=${STEPS_SOURCE_UPDATE:-10}" "maxRegionSize:=5" "deltaTime:=0.2" "noiseSTDev:=0.5"
  "iterationsToRecord:=200" "maxWarmupIterations:=3" "minWarmupIterations:=1"
  "blurSigmaX:=0.0" "blurSigmaY:=0.0" "hitPriorProbability:=0.1" "maxUpdatesPerStop:=8"
  "kernelSigma:=0.5" "kernelStretchConstant:=1.5" "confidenceMeasurementWeight:=0.5"
  "confidenceSigmaSpatial:=0.5" "localEstimationWindowSize:=2" "openMoveSetExpasion:=5"
  "explorationProbability:=0.05" "initialExplorationMoves:=2" "distanceWeight:=0.15"
  "markers_height:=0.2" "measurement_settle_samples:=0" "measurement_block_samples:=10" \
  "measurement_deduplicate_sim_timestamps:=true" \
  # Keep the frozen PMFS budget in simulation seconds without silently
  # doubling wall-clock duration.  The launch default and the historical
  # qualification runs use realtime_factor=1.0; callers may override it
  # explicitly for a diagnostic run.
  "sensor_model_mode:=dynamic" "gaden_iteration_mode:=seeded_time_replay" "realtime_factor:=${REALTIME_FACTOR:-1.0}" "sim_stop_at_s:=${SIM_STOP_AT_S:--1.0}" "nav_command_quantum_s:=${NAV_COMMAND_QUANTUM_S:-2.0}"
  "gas_backend:=${GAS_BACKEND}" "raw_query_executable:=${RAW_QUERY}"
  "gmrf_update_on_new_observation_only:=${GMRF_UPDATE_ON_NEW_OBSERVATION_ONLY}"
  "p2_shadow_enabled:=false" "p2_shadow_directory:=/tmp/tadm_p2_disabled" "p2_global_seed:=20260818"
  "p2_shadow_replicas:=0" "tadm_enabled:=${TADM_ENABLED}" "pfdi_mode:=${PFDI_MODE}" "tadm_directory:=${TADM_DIR}"
  "tadm_prior_set:=${TADM_PRIOR_SET}" "tadm_global_seed:=20260818" "tadm_replicas:=${TADM_REPLICAS}"
  "posterior_guidance_weight:=${POSTERIOR_GUIDANCE_WEIGHT}"
  "tadm_transport_substream:=6077111455669390931"
  "context_bank_export_enabled:=true" "context_bank_export_directory:=${RUN_DIR}/context_bank"
  "use_sdbe:=1" "use_iasc:=1" "use_sepf:=1" "use_sage:=0" "use_beacon:=0"
  "use_beacon_tr:=0" "use_pcrd:=0" "use_pgn:=0" "use_tpp:=0" "use_hmm:=0"
  "temperature_tau:=1.0" "tau_adaptive:=0" "tau_ess_target_ratio:=0.5" "tau_alpha:=0.3"
  "infoTaxis:=false" "use_infotaxis:=false" "use_gui:=false"
)
# Keep the historical launch contract untouched for TNQC_MODE=off. The TNQC
# argument is appended only for an explicit experimental arm so old installed
# launch files remain usable for the frozen baseline.
if [[ "${TNQC_MODE}" != "off" ]]; then
  ARGS+=("tnqc_mode:=${TNQC_MODE}")
fi

echo "PFDI_CASE_START HOUSE=${HOUSE} SEED=${SEED} ARM=${ARM} PFDI_MODE=${PFDI_MODE} TNQC_MODE=${TNQC_MODE} DOMAIN=${ROS_DOMAIN_ID} RUN_DIR=${RUN_DIR}"
set +e
setsid ros2 launch "${LAUNCH}" "${ARGS[@]}" >"${RUN_DIR}/launch.log" 2>&1 &
launch_pid=$!
deadline=$((SECONDS + OUTER_DEADLINE_SEC))
while kill -0 "${launch_pid}" 2>/dev/null; do
  if [[ -s "${RUN_DIR}/run_status.json" ]]; then
    # The benchmark has frozen its terminal record.  Give writers a short
    # flush window, then stop only this launch process group.
    sleep 3
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    sleep 5
    if kill -0 "${launch_pid}" 2>/dev/null; then
      kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    fi
    break
  fi
  if (( TARGET_SOURCE_UPDATES > 0 )); then
    score_file="${RUN_DIR}/tadm/meaci_update_summary.csv"
    ec_edcl_score_file="${RUN_DIR}/tadm/ec_edcl_update_summary.csv"
    if [[ -s "${ec_edcl_score_file}" ]]; then
      score_file="${ec_edcl_score_file}"
    fi
    if [[ ! -s "${score_file}" && -s "${RUN_DIR}/tadm/a9_tv_sd_tfei_diagnostic.csv" ]]; then
      score_file="${RUN_DIR}/tadm/a9_tv_sd_tfei_diagnostic.csv"
    fi
    if [[ -s "${score_file}" ]]; then
      if [[ "${score_file}" == "${RUN_DIR}/tadm/meaci_update_summary.csv" ]]; then
        completed_updates="$(awk -F, 'NR > 1 && $7 == 1 {seen[$2]=1} END {print length(seen)+0}' "${score_file}")"
        accepted_updates="$(awk -F, 'NR > 1 && $8 == 1 {seen[$2]=1} END {print length(seen)+0}' "${score_file}")"
      elif [[ "${score_file}" == "${ec_edcl_score_file}" ]]; then
        completed_updates="$(awk -F, 'NR > 1 && $4 == "VALID" {seen[$2]=1} END {print length(seen)+0}' "${score_file}")"
        accepted_updates="${completed_updates}"
      else
        completed_updates="$(awk -F, 'NR > 1 {seen[$2]=1} END {print length(seen)+0}' "${score_file}")"
        accepted_updates="$(awk -F, 'NR > 1 && $7 == 1 {seen[$2]=1} END {print length(seen)+0}' "${score_file}")"
      fi
      if (( completed_updates >= TARGET_SOURCE_UPDATES && accepted_updates >= TARGET_ACCEPTED_UPDATES )); then
        cat > "${RUN_DIR}/run_status.json" <<EOF
{
  "status": "evidence_target_reached",
  "run_id": "${RUN_ID}",
  "method": "B4_PMFS_official",
  "seed": ${SEED},
  "gsl_result_code": "target_source_and_accepted_updates_reached",
  "gsl_action_status": "controlled_evidence_stop",
  "completed_source_updates": ${completed_updates},
  "accepted_source_updates": ${accepted_updates}
}
EOF
        sleep 3
        kill -INT -- "-${launch_pid}" 2>/dev/null || true
        sleep 5
        if kill -0 "${launch_pid}" 2>/dev/null; then
          kill -KILL -- "-${launch_pid}" 2>/dev/null || true
        fi
        break
      fi
    fi
  fi
  if (( SECONDS >= deadline )); then
    kill -INT -- "-${launch_pid}" 2>/dev/null || true
    sleep 25
    kill -KILL -- "-${launch_pid}" 2>/dev/null || true
    break
  fi
  sleep 2
done
wait "${launch_pid}"
status=$?
set -e
if [[ -s "${RUN_DIR}/run_status.json" ]]; then
  EVALUATOR_SCRIPT="${EVALUATOR_SCRIPT:-/dev/shm/meaci_online_20260824/evaluate_meaci.py}"
  if [[ -f "${EVALUATOR_SCRIPT}" ]]; then
    python3 "${EVALUATOR_SCRIPT}" --run-dir "${RUN_DIR}" --truth-x "${SOURCE_X}" --truth-y "${SOURCE_Y}" || {
      echo "PFDI_EXTERNAL_EVALUATOR_FAILED" >&2
    }
  fi
  echo "PFDI_CASE_COMPLETE HOUSE=${HOUSE} SEED=${SEED} ARM=${ARM}"
  exit 0
fi
exit "${status}"
