#!/bin/bash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash
RESULTS=/tmp/v8_exp/ablation_h01air/results.csv
mkdir -p /tmp/v8_exp/ablation_h01air
echo "config,seed,error_m,localized,elapsed_s" > $RESULTS
for cfg in Full A1_FixedEta A2_NoEProc A3_NoDDM A4_NoLevy A5_NoUpwind A6_NoGPAlt; do
  echo "=== Running $cfg ==="
  EXTRA=""
  case $cfg in
    A1_FixedEta) EXTRA="opgsl.modules.adaptive_eta:=false" ;;
    A2_NoEProc) EXTRA="opgsl.e_process.enabled:=false" ;;
    A3_NoDDM) EXTRA="opgsl.ddm.enabled:=false" ;;
    A4_NoLevy) EXTRA="opgsl.modules.levy:=false" ;;
    A5_NoUpwind) EXTRA="opgsl.modules.upwind_tracking:=false" ;;
    A6_NoGPAlt) EXTRA="opgsl.altitude.gp:=false" ;;
  esac
  for seed in 0 1 2 3 4 5 6 7 8 9; do
    echo "  Seed $seed..."
    LOG=/tmp/v8_exp/ablation_h01air/${cfg}_s${seed}.log
    timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py method:=M7_full_saisc_pf algorithm:=OPGSL opgsl.event_driven.enabled:=true opgsl.seed:=$seed scenario:=H01_air $EXTRA > $LOG 2>&1
    DIST=$(grep -oP "endpoint distance.*?: \K[0-9.]+" $LOG | tail -1)
    LOC=$(grep -oP "Localized.*?: \K[01]" $LOG | tail -1)
    if [ -z "$DIST" ]; then DIST=99.0; fi
    if [ -z "$LOC" ]; then LOC=0; fi
    echo "$cfg,$seed,$DIST,$LOC,300" >> $RESULTS
    echo "    -> dist=$DIST loc=$LOC"
    pkill -f gsl_actionserver 2>/dev/null
    pkill -f vgr_sim_node 2>/dev/null
    sleep 2
  done
done
echo "=== DONE ==="
cat $RESULTS