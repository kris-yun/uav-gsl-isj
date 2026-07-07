#!/bin/bash
# Run baseline algorithms on A1_fast scenario
# Source: (5.0, 6.2), Start: (4.0, 4.0)

RESULTS_FILE="/tmp/baseline_results.csv"
echo "algorithm,seed,error_m,min_dist_m,term,time_s" > $RESULTS_FILE

run_baseline() {
    local algo=$1
    local seed=$2
    echo "[$(date +%H:%M:%S)] Running $algo seed=$seed..."
    timeout 150 ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
        algorithm:=$algo \
        seed:=$seed \
        source_x:=5.00 \
        source_y:=6.20 \
        start_x:=4.0 \
        start_y:=4.0 \
        vgr_data_path:=/home/zyc/enva_vgr \
        config_id:="2,4-1_fast" \
        timeout_sec:=120 2>&1 > /tmp/${algo}_${seed}.log
    
    # Extract result
    latest=$(ls -t /tmp/gsl_runs_v4/results/raw/${algo}_*_s${seed}_*record.csv 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
        latest=$(ls -t /tmp/gsl_runs/results/raw/${algo}_*_s${seed}_*record.csv 2>/dev/null | head -1)
    fi
    if [ -n "$latest" ]; then
        err=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['final_error_m'])")
        md=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['min_distance_m'])")
        term=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['termination_reason'])")
        ts=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['search_time_s'])")
        echo "$algo,$seed,$err,$md,$term,$ts" >> $RESULTS_FILE
        echo "  -> $algo seed=$seed: error=${err}m min_dist=${md}m"
    else
        echo "  -> NO RESULT for $algo seed=$seed"
        echo "$algo,$seed,999,999,missing,0" >> $RESULTS_FILE
    fi
    sleep 2
}

# Run SurgeCast (SensorAwareSurgeCastPF) - 3 seeds
for seed in 0 1 2; do
    run_baseline "SensorAwareSurgeCastPF" $seed
done

# Run PMFS - 3 seeds
for seed in 0 1 2; do
    run_baseline "PMFS" $seed
done

echo ""
echo "=== BASELINE RESULTS ==="
cat $RESULTS_FILE
echo "=== DONE ==="