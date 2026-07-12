#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

RESULTS_DIR=/tmp/v8_exp/ablation_handcrafted
mkdir -p $RESULTS_DIR
RESULTS=$RESULTS_DIR/results_h01air.csv
echo "config,scenario,seed,error_m,localized,elapsed_s" > $RESULTS

D=/home/zyc/vgr_data_scenarios/House01
C="1,3-2,4_fast"
SX=-0.60
SY=1.95
SZ=0.40
STX=-0.90
STY=0.15

CONFIGS=(Full A2_NoDDM A3_NoWRAIG A4_NoCP)
DDMS=(true false true true)
WRAIGS=(true true false true)
CPS=(true true true false)

for idx in 0 1 2 3; do
  CONFIG=${CONFIGS[$idx]}
  DDM=${DDMS[$idx]}
  WRAIG=${WRAIGS[$idx]}
  CP=${CPS[$idx]}
  for SEED in 0 1 2 3 4 5 6 7 8 9; do
    echo "Running: ${CONFIG} H01_air seed=${SEED}"
    START=$(date +%s)
    LOG=/tmp/abl_${CONFIG}_H01_air_${SEED}.txt
    timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py \
      method:=M7_full_saisc_pf algorithm:=OPGSL \
      opgsl_ddm:=${DDM} opgsl_wraig:=${WRAIG} opgsl_cp:=${CP} \
      vgr_data_path:="${D}" config_id:="${C}" \
      source_x:=${SX} source_y:=${SY} source_z:=${SZ} \
      start_x:=${STX} start_y:=${STY} seed:=${SEED} \
      resultsFile:=${RESULTS_DIR}/${CONFIG}_H01_air_${SEED}.csv > ${LOG} 2>&1
    ERR=$(grep -oP 'final_error[=:]\s*\K[0-9.]+' ${LOG} 2>/dev/null | tail -1)
    LOC=$(grep -oP 'localized[=:]\s*\K[01]' ${LOG} 2>/dev/null | tail -1)
    [ -z "${ERR}" ] && ERR=99.000
    [ -z "${LOC}" ] && LOC=0
    END=$(date +%s)
    ELAPSED=$((END - START))
    echo "${CONFIG},H01_air,${SEED},${ERR},${LOC},${ELAPSED}" >> ${RESULTS}
    echo "  -> err=${ERR} loc=${LOC} elapsed=${ELAPSED}s"
  done
done

echo "=== DONE ==="
cat ${RESULTS}
