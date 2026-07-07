script = """#!/bin/bash
DIR="/tmp/edbayes_exp"
mkdir -p "$DIR"
CSV="$DIR/experiment_results.csv"
echo "method,seed,final_error,localized2,steps,elapsed,converge_type" > "$CSV"
cd /home/zyc/gsl_ws
source install/setup.bash

cleanup() {
    pkill -9 -f gsl_actionserver_node 2>/dev/null
    pkill -9 -f vgr_sim_node 2>/dev/null
    pkill -9 -f gsl_benchmark_runner 2>/dev/null
    sleep 2
}

run_one() {
    local METHOD=$1 SEED=$2 EXTRA=$3
    local LOG="$DIR/${METHOD}_s${SEED}.log"
    cleanup
    local T0=$(date +%s)
    ros2 launch vgr_bridge vgr_ablation.launch.py \\
        vgr_data_path:=/home/zyc/enva_vgr config_id:=2,4-1_fast \\
        algorithm:=OPGSL method:=M7_full_saisc_pf \\
        source_x:=5.00 source_y:=6.20 source_z:=0.50 \\
        start_x:=4.0 start_y:=4.0 seed:=$SEED \\
        timeout_sec:=120 use_sbd:=true \\
        opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false \\
        $EXTRA > "$LOG" 2>&1 &
    local LPID=$!
    local WAIT=0
    while [ $WAIT -lt 180 ]; do
        sleep 5
        WAIT=$((WAIT + 5))
        if grep -q "DONE, CLOSING" "$LOG" 2>/dev/null; then sleep 3; break; fi
        if ! kill -0 $LPID 2>/dev/null; then break; fi
    done
    local T1=$(date +%s)
    local ELAPSED=$((T1 - T0))
    cleanup
    local FERR=$(grep "final_error=" "$LOG" | sed "s/.*final_error=\\\\([0-9.]*\\\\).*/\\\\1/" | tail -1)
    local LOC2=$(grep "localized2=" "$LOG" | sed "s/.*localized2=\\\\([0-9]*\\\\).*/\\\\1/" | tail -1)
    local STEPS=$(grep "OPGSL-AI step=" "$LOG" | tail -1 | sed "s/.*step=\\\\([0-9]*\\\\).*/\\\\1/")
    if [ -z "$STEPS" ]; then STEPS=$(grep -c "SDNBV" "$LOG"); fi
    local CTYPE="other"
    if grep -q "Found the emission source" "$LOG"; then CTYPE="found"
    elif grep -q "action_failure" "$LOG"; then CTYPE="timeout"
    fi
    echo "$METHOD,$SEED,$FERR,$LOC2,$STEPS,$ELAPSED,$CTYPE" | tee -a "$CSV"
    sleep 2
}

echo "=== ED-Bayes (event-driven) 10 seeds ==="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one "ED_Bayes" $s "opgsl.event_driven.enabled:=true"
done

echo "=== Baseline (continuous) 10 seeds ==="
for s in 0 1 2 3 4 5 6 7 8 9; do
    run_one "Baseline" $s "opgsl.event_driven.enabled:=false"
done

echo "=== Summary ==="
cat "$CSV"
"""

with open('D:/ZYC/A-gas/run_exp.py', 'w') as f:
    f.write('import subprocess\n')
    f.write('script = """' + script + '"""\n')
    f.write('with open("/tmp/run_edbayes.sh", "w") as f:\n')
    f.write('    f.write(script)\n')
    f.write('subprocess.run(["chmod", "+x", "/tmp/run_edbayes.sh"])\n')
    f.write('print("Script written")\n')
print("Python script created")
