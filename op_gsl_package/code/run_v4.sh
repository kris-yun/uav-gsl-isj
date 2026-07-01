#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

R="/home/zyc/results_v4"
mkdir -p "$R"

CONFIGS=("2,4-1_fast:-0.4:-2.9:-0.3:House01" "3,5-1_fast:0.0:-1.0:0.2:House02" "1-2,5_fast:-0.45:1.9:-0.1:House03")
SEEDS=(0 1 2 3 4)

echo "=== OPGSL-3D v4 Experiment Suite ===" | tee "$R/log.txt"
echo "Started: $(date)" | tee -a "$R/log.txt"

# Part 1: OPGSL ablation (A0-A4) x 3 houses x 5 seeds
ABLATION_NAMES=("A0_baseline" "A1_esc_only" "A2_levy_only" "A3_layer_only" "A4_full")
ABLATION_PARAMS=(
  "opgsl.altitude.esc:=false opgsl.altitude.levy:=false opgsl.altitude.layer_scan:=false opgsl.altitude.decay:=false"
  "opgsl.altitude.esc:=true opgsl.altitude.levy:=false opgsl.altitude.layer_scan:=false opgsl.altitude.decay:=false"
  "opgsl.altitude.esc:=false opgsl.altitude.levy:=true opgsl.altitude.layer_scan:=false opgsl.altitude.decay:=false"
  "opgsl.altitude.esc:=false opgsl.altitude.levy:=false opgsl.altitude.layer_scan:=true opgsl.altitude.decay:=false"
  "opgsl.altitude.esc:=true opgsl.altitude.levy:=true opgsl.altitude.layer_scan:=true opgsl.altitude.decay:=true"
)

for CONFIG_STR in "${CONFIGS[@]}"; do
  IFS=':' read -r CONFIG SX SY SZ HOUSE <<< "$CONFIG_STR"
  for idx in "${!ABLATION_NAMES[@]}"; do
    ABL_NAME="${ABLATION_NAMES[$idx]}"
    ABL_P="${ABLATION_PARAMS[$idx]}"
    for SEED in "${SEEDS[@]}"; do
      RUN_ID="OPGSL_${ABL_NAME}_${HOUSE}_s${SEED}"
      RUN_DIR="/tmp/gsl_runs/v4_${RUN_ID}"
      RESULT="$R/${RUN_ID}.csv"
      if [ -f "$RUN_DIR/run_status.json" ]; then
        echo "SKIP $RUN_ID" | tee -a "$R/log.txt"
        continue
      fi
      echo "Run $RUN_ID $(date +%H:%M:%S)" | tee -a "$R/log.txt"
      pkill -9 -f gsl_ 2>/dev/null; pkill -9 -f vgr_ 2>/dev/null
      rm -rf /dev/shm/fastrtps_* 2>/dev/null; sleep 2
      mkdir -p "$RUN_DIR"
      timeout 350 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
        config_id:=$CONFIG algorithm:=OPGSL method:=M0_sc_pf_hard_base \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 flight_height:=0.3 \
        seed:=$SEED timeout_sec:=300 \
        resultsFile:=$RESULT run_dir:=$RUN_DIR \
        $ABL_P \
        2>&1 | grep -E "RESULT|final_error|CONVERGED|phase=" | tail -3 | tee -a "$R/log.txt"
      echo "Done $RUN_ID $(date +%H:%M:%S)" | tee -a "$R/log.txt"
    done
  done
done

# Part 2: Baselines (surge_cast, GrGSL) x 3 houses x 5 seeds
for CONFIG_STR in "${CONFIGS[@]}"; do
  IFS=':' read -r CONFIG SX SY SZ HOUSE <<< "$CONFIG_STR"
  for ALG in surge_cast GrGSL; do
    for SEED in "${SEEDS[@]}"; do
      RUN_ID="${ALG}_${HOUSE}_s${SEED}"
      RUN_DIR="/tmp/gsl_runs/v4_${RUN_ID}"
      RESULT="$R/${RUN_ID}.csv"
      if [ -f "$RUN_DIR/run_status.json" ]; then
        echo "SKIP $RUN_ID" | tee -a "$R/log.txt"
        continue
      fi
      echo "Run $RUN_ID $(date +%H:%M:%S)" | tee -a "$R/log.txt"
      pkill -9 -f gsl_ 2>/dev/null; pkill -9 -f vgr_ 2>/dev/null
      rm -rf /dev/shm/fastrtps_* 2>/dev/null; sleep 2
      mkdir -p "$RUN_DIR"
      timeout 350 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
        config_id:=$CONFIG algorithm:=$ALG method:=M0_sc_pf_hard_base \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 flight_height:=0.3 \
        seed:=$SEED timeout_sec:=300 \
        resultsFile:=$RESULT run_dir:=$RUN_DIR \
        2>&1 | grep -E "RESULT|final_error|HasEnded" | tail -3 | tee -a "$R/log.txt"
      echo "Done $RUN_ID $(date +%H:%M:%S)" | tee -a "$R/log.txt"
    done
  done
done

echo "=== ALL DONE ===" | tee -a "$R/log.txt"
echo "Finished: $(date)" | tee -a "$R/log.txt"
