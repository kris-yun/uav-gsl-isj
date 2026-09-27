#!/usr/bin/env bash
set -eo pipefail

# DQA ablation matrix: baseline / SDR / TDC / MHC / DQA(SDR+TDC+MHC)
source /opt/ros/humble/setup.bash
source "${ROS_WS_SETUP:-$HOME/ros2_ws/install/setup.bash}"

RESULTS_DIR="${RESULTS_DIR:-/tmp/uav_gsl_dqa}"
VGR_DATA_BASE="${VGR_DATA_BASE:-/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios}"
DATASET="${DATASET:-House01}"
SEEDS_STR="${SEEDS:-0 1 2 3 4 5 6 7 8 9}"
CONDITIONS_STR="${CONDITIONS:-baseline sdr tdc mhc dqa}"
FORCE="${FORCE:-0}"
LAUNCH_TIMEOUT="${LAUNCH_TIMEOUT:-420}"
POLL_TIMEOUT="${POLL_TIMEOUT:-390}"

mkdir -p "$RESULTS_DIR"

case "$DATASET" in
  House01)
    CONFIG_ID="2,4-1_fast"; SOURCE_X="-0.40"; SOURCE_Y="-2.90"; SOURCE_Z="-0.30"
    START_X="-5.0"; START_Y="-5.0" ;;
  House02)
    CONFIG_ID="3,5-1_fast"; SOURCE_X="0.0"; SOURCE_Y="-1.0"; SOURCE_Z="-0.30"
    START_X="-5.0"; START_Y="-5.0" ;;
  House03)
    CONFIG_ID="1-2,5_fast"; SOURCE_X="8.2"; SOURCE_Y="5.0"; SOURCE_Z="-0.30"
    START_X="-5.0"; START_Y="-5.0" ;;
  *) echo "[ERR] Unknown DATASET=$DATASET" >&2; exit 1 ;;
esac

DATA_PATH="$VGR_DATA_BASE/$DATASET"
[[ -d "$DATA_PATH" ]] || { echo "[ERR] data path not found: $DATA_PATH" >&2; exit 1; }

kill_ros() {
  killall -9 gsl_actionserver_node vgr_sim_node gmrf_wind_mapping_node gsl_benchmark_runner 2>/dev/null || true
  rm -rf /dev/shm/fastrtps_* 2>/dev/null || true
}

flags_for_condition() {
  SDR=false; TDC=false; MHC=false
  case "$1" in
    baseline) ;;  # all OFF
    sdr) SDR=true ;;
    tdc) TDC=true ;;
    mhc) MHC=true ;;
    dqa) SDR=true; TDC=true; MHC=true ;;
    *) echo "[ERR] unknown condition: $1" >&2; exit 2 ;;
  esac
}

run_one() {
  local seed="$1" cond="$2"
  flags_for_condition "$cond"
  local tag="${DATASET}_${cond}_s${seed}"
  local server="$RESULTS_DIR/${tag}_server.csv"

  if [[ "$FORCE" != "1" && -s "$server" ]]; then
    echo "[SKIP] $tag exists"
    return 0
  fi

  rm -f "$server" "$server.audit.csv"
  kill_ros; sleep 3
  echo "[START] $tag $(date +%T)"

  timeout "$LAUNCH_TIMEOUT" ros2 launch vgr_bridge vgr_gsl_unified_ablation.launch.py \
    vgr_data_path:="$DATA_PATH" config_id:="$CONFIG_ID" dataset:="$DATASET" method_id:="$cond" \
    source_x:="$SOURCE_X" source_y:="$SOURCE_Y" source_z:="$SOURCE_Z" \
    start_x:="$START_X" start_y:="$START_Y" seed:="$seed" \
    server_results_file:="$server" \
    sdr_enabled:="$SDR" tdc_enabled:="$TDC" mhc_enabled:="$MHC" \
    pwc_enabled:=false psde_online_enabled:=false psde_final_enabled:=false \
    asa_enabled:=false spw_enabled:=false bwe_enabled:=false pgpt_enabled:=false hce_enabled:=false \
    > "$RESULTS_DIR/${tag}.log" 2>&1 &
  local pid=$!

  for _ in $(seq 1 "$POLL_TIMEOUT"); do
    sleep 1
    if [[ -s "$server" ]]; then sleep 2; kill -9 $pid 2>/dev/null || true; kill_ros; sleep 2
      echo "[DONE] $tag: $(tail -1 "$server")"; return 0; fi
    kill -0 $pid 2>/dev/null || break
  done
  kill -9 $pid 2>/dev/null || true; kill_ros; sleep 2
  [[ -s "$server" ]] && echo "[DONE] $tag: $(tail -1 "$server")" || echo "[FAIL] $tag"
}

for seed in $SEEDS_STR; do
  for cond in $CONDITIONS_STR; do
    run_one "$seed" "$cond"
  done
done

echo "[SUMMARY]"
for cond in $CONDITIONS_STR; do
  vals=()
  for seed in $SEEDS_STR; do
    f="$RESULTS_DIR/${DATASET}_${cond}_s${seed}_server.csv"
    [[ -f "$f" ]] && v=$(tail -1 "$f" | awk -F, '{print $7}') && vals+=("$v")
  done
  if [[ ${#vals[@]} -gt 0 ]]; then
    mean=$(printf '%s\n' "${vals[@]}" | awk '{s+=$1}END{printf "%.3f",s/NR}')
    echo "  $cond: n=${#vals[@]} mean=${mean}m  vals=[${vals[*]}]"
  fi
done
done
