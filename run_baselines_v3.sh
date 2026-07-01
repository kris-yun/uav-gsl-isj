#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

OUTDIR=/tmp/baselines_v3
mkdir -p $OUTDIR

echo "BASELINE_START $(date)" > $OUTDIR/summary.txt

run_one() {
  local algo=$1 method=$2 house=$3 seed=$4 datapath=$5 sx=$6 sy=$7 sz=$8
  local tag="${algo}_${house}_s${seed}"
  local logfile="$OUTDIR/${tag}.log"
  
  pkill -9 -f ros2 2>/dev/null
  pkill -9 -f gsl 2>/dev/null
  sleep 2
  
  echo "[$(date)] Running $tag method=$method" 
  
  timeout 360 ros2 launch vgr_bridge vgr_opgsl3d_ablation.launch.py \
    vgr_data_path:=$datapath \
    algorithm:=$algo \
    method:=$method \
    method_family:=baseline \
    ablation_id:=${algo} \
    run_id:=${tag} \
    run_dir:=$OUTDIR/${tag} \
    output_dir:=$OUTDIR \
    environment_id:=${house} \
    scenario_id:=${house}_default \
    dataset:=${house} \
    source_x:=$sx source_y:=$sy source_z:=$sz \
    start_x:=-0.9 start_y:=0.15 \
    seed:=$seed \
    flight_height:=0.3 \
    timeout_sec:=300.0 \
    resultsFile:=$OUTDIR/${tag}_result.txt \
    > $logfile 2>&1 || true
  
  local result=$(grep "RESULT IS:" $logfile 2>/dev/null | tail -1)
  echo "$tag: $result"
  echo "$tag: $result" >> $OUTDIR/summary.txt
}

# House01
run_one "PMFS" "B4_PMFS_official" "House01" "0" "/home/zyc/vgr_data_scenarios/House01" "-0.40" "-2.90" "-0.30"
run_one "GrGSL" "B5_GrGSL_official" "House01" "0" "/home/zyc/vgr_data_scenarios/House01" "-0.40" "-2.90" "-0.30"
run_one "SurgeCast" "B0_surge_cast_official" "House01" "0" "/home/zyc/vgr_data_scenarios/House01" "-0.40" "-2.90" "-0.30"

# House02
run_one "PMFS" "B4_PMFS_official" "House02" "0" "/home/zyc/vgr_data_scenarios/House02" "0.0" "-1.0" "0.20"
run_one "GrGSL" "B5_GrGSL_official" "House02" "0" "/home/zyc/vgr_data_scenarios/House02" "0.0" "-1.0" "0.20"
run_one "SurgeCast" "B0_surge_cast_official" "House02" "0" "/home/zyc/vgr_data_scenarios/House02" "0.0" "-1.0" "0.20"

# House03
run_one "PMFS" "B4_PMFS_official" "House03" "0" "/home/zyc/vgr_data_scenarios/House03" "-0.45" "1.90" "-0.10"
run_one "GrGSL" "B5_GrGSL_official" "House03" "0" "/home/zyc/vgr_data_scenarios/House03" "-0.45" "1.90" "-0.10"
run_one "SurgeCast" "B0_surge_cast_official" "House03" "0" "/home/zyc/vgr_data_scenarios/House03" "-0.45" "1.90" "-0.10"

echo "ALL_BASELINES_DONE $(date)" >> $OUTDIR/summary.txt