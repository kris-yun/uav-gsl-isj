#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

R="/home/zyc/results_v4"
mkdir -p "$R"
LF="$R/log.txt"

echo "=== OPGSL-3D v4 Experiment Suite (FIXED launch) ===" | tee "$LF"
echo "Started: $(date)" | tee -a "$LF"

CONFIGS=("2,4-1_fast:-0.4:-2.9:-0.3:House01" "3,5-1_fast:0.0:-1.0:0.2:House02" "1-2,5_fast:-0.45:1.9:-0.1:House03")
SEEDS=(0 1 2 3 4)

# Ablation configs: name:esc:levy:layer:decay
ABLATIONS=("A0_baseline:false:false:false:false" "A1_esc_only:true:false:false:false" "A2_levy_only:false:true:false:false" "A3_layer_only:false:false:true:false" "A4_full:true:true:true:true")

for CONFIG_STR in "${CONFIGS[@]}"; do
  IFS=':' read -r CONFIG SX SY SZ HOUSE <<< "$CONFIG_STR"
  for ABL in "${ABLATIONS[@]}"; do
    IFS=':' read -r ANAME ESC LV LYR DECAY <<< "$ABL"
    for SEED in "${SEEDS[@]}"; do
      RUN_ID="OPGSL_${ANAME}_${HOUSE}_s${SEED}"
      RUN_DIR="/tmp/gsl_runs/v4_${RUN_ID}"
      RESULT="$R/${RUN_ID}.csv"

      # Skip if already done
      if [ -f "$RUN_DIR/run_status.json" ] && [ -f "$RESULT" ]; then
        echo "SKIP $RUN_ID" | tee -a "$LF"
        continue
      fi

      echo "Run $RUN_ID $(date +%H:%M:%S)" | tee -a "$LF"
      pkill -9 -f gsl_ 2>/dev/null; pkill -9 -f vgr_ 2>/dev/null
      rm -rf /dev/shm/fastrtps_* 2>/dev/null; sleep 2
      mkdir -p "$RUN_DIR"

      timeout 350 ros2 launch vgr_bridge vgr_opgsl3d_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
        config_id:=$CONFIG algorithm:=OPGSL method:=M0_sc_pf_hard_base \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 flight_height:=0.3 \
        seed:=$SEED timeout_sec:=300 \
        resultsFile:=$RESULT run_dir:=$RUN_DIR \
        opgsl_alt_esc:=$ESC opgsl_alt_levy:=$LV \
        opgsl_alt_layer_scan:=$LYR opgsl_alt_decay:=$DECAY \
        2>&1 | grep -E "RESULT|final_error|CONVERGED|phase=" | tail -3 | tee -a "$LF"

      echo "Done $RUN_ID $(date +%H:%M:%S)" | tee -a "$LF"
    done
  done
done

# Baselines (surge_cast, GrGSL) - use canonical launch (no OPGSL params needed)
for CONFIG_STR in "${CONFIGS[@]}"; do
  IFS=':' read -r CONFIG SX SY SZ HOUSE <<< "$CONFIG_STR"
  for ALG in surge_cast GrGSL; do
    for SEED in "${SEEDS[@]}"; do
      RUN_ID="${ALG}_${HOUSE}_s${SEED}"
      RUN_DIR="/tmp/gsl_runs/v4_${RUN_ID}"
      RESULT="$R/${RUN_ID}.csv"

      if [ -f "$RUN_DIR/run_status.json" ] && [ -f "$RESULT" ]; then
        echo "SKIP $RUN_ID" | tee -a "$LF"
        continue
      fi

      echo "Run $RUN_ID $(date +%H:%M:%S)" | tee -a "$LF"
      pkill -9 -f gsl_ 2>/dev/null; pkill -9 -f vgr_ 2>/dev/null
      rm -rf /dev/shm/fastrtps_* 2>/dev/null; sleep 2
      mkdir -p "$RUN_DIR"

      timeout 350 ros2 launch vgr_bridge vgr_opgsl3d_ablation.launch.py \
        vgr_data_path:=/home/zyc/vgr_data_scenarios/$HOUSE \
        config_id:=$CONFIG algorithm:=$ALG method:=M0_sc_pf_hard_base \
        source_x:=$SX source_y:=$SY source_z:=$SZ \
        start_x:=-0.9 start_y:=0.15 flight_height:=0.3 \
        seed:=$SEED timeout_sec:=300 \
        resultsFile:=$RESULT run_dir:=$RUN_DIR \
        2>&1 | grep -E "RESULT|final_error|HasEnded" | tail -3 | tee -a "$LF"

      echo "Done $RUN_ID $(date +%H:%M:%S)" | tee -a "$LF"
    done
  done
done

echo "=== ALL DONE ===" | tee -a "$LF"
echo "Finished: $(date)" | tee -a "$LF"
