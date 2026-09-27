#!/usr/bin/env bash
set -eo pipefail

# Runs matched-seed ablations with the fixed launch file.
# Required before paper claims: repeatability sanity -> House01 full -> House02/House03 full.

source /opt/ros/humble/setup.bash
source "${ROS_WS_SETUP:-$HOME/ros2_ws/install/setup.bash}"

RESULTS_DIR="${RESULTS_DIR:-/tmp/uav_gsl_ablation_fixed}"
VGR_DATA_BASE="${VGR_DATA_BASE:-/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios}"
DATASET="${DATASET:-House01}"
SEEDS_STR="${SEEDS:-0 1 2}"
CONDITIONS_STR="${CONDITIONS:-baseline pwc psde_final psde_online psde_both sdr full}"
FORCE="${FORCE:-0}"
LAUNCH_TIMEOUT="${LAUNCH_TIMEOUT:-420}"
POLL_TIMEOUT="${POLL_TIMEOUT:-390}"

mkdir -p "$RESULTS_DIR"

case "$DATASET" in
  House01)
    CONFIG_ID="${CONFIG_ID:-2,4-1_fast}"
    SOURCE_X="${SOURCE_X:--0.40}"
    SOURCE_Y="${SOURCE_Y:--2.90}"
    SOURCE_Z="${SOURCE_Z:--0.30}"
    START_X="${START_X:--5.0}"
    START_Y="${START_Y:--5.0}"
    ;;
  House02)
    CONFIG_ID="${CONFIG_ID:-3,5-1_fast}"
    SOURCE_X="${SOURCE_X:-0.0}"
    SOURCE_Y="${SOURCE_Y:--1.0}"
    SOURCE_Z="${SOURCE_Z:--0.30}"
    START_X="${START_X:--5.0}"
    START_Y="${START_Y:--5.0}"
    ;;
  House03)
    CONFIG_ID="${CONFIG_ID:-1-2,5_fast}"
    SOURCE_X="${SOURCE_X:-8.2}"
    SOURCE_Y="${SOURCE_Y:-5.0}"
    SOURCE_Z="${SOURCE_Z:--0.30}"
    START_X="${START_X:--5.0}"
    START_Y="${START_Y:--5.0}"
    ;;
  *)
    echo "[ERR] Unknown DATASET=$DATASET. Set CONFIG_ID/SOURCE_X/SOURCE_Y manually or add a case." >&2
    exit 1
    ;;
esac

DATA_PATH="$VGR_DATA_BASE/$DATASET"
[[ -d "$DATA_PATH" ]] || { echo "[ERR] data path not found: $DATA_PATH" >&2; exit 1; }

kill_ros() {
  killall -9 gsl_actionserver_node vgr_sim_node gmrf_wind_mapping_node gsl_benchmark_runner 2>/dev/null || true
  rm -rf /dev/shm/fastrtps_* 2>/dev/null || true
}

flags_for_condition() {
  local cond="$1"
  PWC=false; PSDE_ONLINE=false; PSDE_FINAL=false; SDR=false; BWE=false; PGPT=false; HCE=false; LEGACY_MAC=false; ASA=false; SPW=false
  case "$cond" in
    baseline) ;;
    pwc) PWC=true ;;
    psde_final|mac) PSDE_FINAL=true ;;
    psde_online) PSDE_ONLINE=true ;;
    psde_both|pwc_mac) PSDE_ONLINE=true; PSDE_FINAL=true ;;
    sdr) SDR=true ;;
    asa) ASA=true ;;
    spw) SPW=true ;;
    sdr_asa) SDR=true; ASA=true ;;
    sdr_spw) SDR=true; SPW=true ;;
    full_new) PWC=true; SDR=true; BAPR=true; HSPB=true ;;
    full) PWC=true; PSDE_ONLINE=true; PSDE_FINAL=true; SDR=true ;;
    bwe) BWE=true ;;
    pgpt) PGPT=true ;;
    hce) HCE=true ;;
    *) echo "[ERR] unknown condition: $cond" >&2; exit 2 ;;
  esac
}

run_one() {
  local seed="$1" cond="$2" rep_suffix="${3:-}"
  flags_for_condition "$cond"
  local tag="${DATASET}_${cond}_s${seed}${rep_suffix}"
  local server="$RESULTS_DIR/${tag}_server.csv"
  local path="$RESULTS_DIR/${tag}_traj.csv"
  local result="$RESULTS_DIR/${tag}_result.csv"
  local log="$RESULTS_DIR/${tag}.log"

  if [[ "$FORCE" != "1" && -s "$server" ]]; then
    echo "[SKIP] $tag: $(tail -1 "$server")"
    return 0
  fi

  rm -f "$server" "$server.audit.csv" "$path" "$result" "$log"
  kill_ros
  sleep 3
  echo "[START] $tag $(date +%F_%T)"

  timeout "$LAUNCH_TIMEOUT" ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
    vgr_data_path:="$DATA_PATH" config_id:="$CONFIG_ID" dataset:="$DATASET" method_id:="$cond" \
    source_x:="$SOURCE_X" source_y:="$SOURCE_Y" source_z:="$SOURCE_Z" \
    start_x:="$START_X" start_y:="$START_Y" seed:="$seed" \
    server_results_file:="$server" server_path_file:="$path" output_csv:="$result" \
    pwc_enabled:="$PWC" mac_enabled:="false" psde_online_enabled:="$PSDE_ONLINE" psde_final_enabled:="$PSDE_FINAL" \
    sdr_enabled:="$SDR" asa_enabled:="$ASA" spw_enabled:="$SPW" bwe_enabled:="$BWE" pgpt_enabled:="$PGPT" hce_enabled:="$HCE" \
    tdc_enabled:="false" gt_debug_logging:="false" verbose_debug:="false" wind_vector_is_flow_to:="true" \
    > "$log" 2>&1 &
  local launch_pid=$!

  for _ in $(seq 1 "$POLL_TIMEOUT"); do
    sleep 1
    if [[ -s "$server" ]]; then
      sleep 2
      kill -9 "$launch_pid" 2>/dev/null || true
      kill_ros
  sleep 3
      echo "[DONE] $tag: $(tail -1 "$server")"
      return 0
    fi
    if ! kill -0 "$launch_pid" 2>/dev/null; then
      break
    fi
  done

  kill -9 "$launch_pid" 2>/dev/null || true
  kill_ros
  sleep 3
  if [[ -s "$server" ]]; then
    echo "[DONE] $tag: $(tail -1 "$server")"
  else
    echo "[FAIL] $tag: no server result; see $log"
  fi
}

for seed in $SEEDS_STR; do
  for cond in $CONDITIONS_STR; do
    run_one "$seed" "$cond"
  done
done

echo "[SUMMARY]"
python3 "$(dirname "$0")/collect_results.py" "$RESULTS_DIR" || true
