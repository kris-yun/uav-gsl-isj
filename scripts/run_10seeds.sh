#!/bin/bash
# 10-seed experiment with grid-fixed original code
# Source: (5.0, 6.2), Environment: A1_fast, Config: vgr_ablation
RESULTS_FILE="/tmp/gridfix_10seeds.csv"
echo "seed,error_m,min_dist_m,term,time_s" > $RESULTS_FILE

for seed in $(seq 0 9); do
    echo "[$(date +%H:%M:%S)] Running seed=$seed..."
    timeout 150 ros2 launch vgr_bridge vgr_ablation.launch.py seed:=$seed timeout_sec:=120 opgsl_cp:=false opgsl_ddm:=false 2>&1 > /tmp/seed_${seed}.log
    
    # Extract result from latest CSV
    latest=$(ls -t /tmp/gsl_runs_v4/results/raw/*_s${seed}_*record.csv 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        err=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['final_error_m'])")
        md=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['min_distance_m'])")
        term=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['termination_reason'])")
        ts=$(python3 -c "import csv; r=csv.DictReader(open('$latest')).__next__(); print(r['search_time_s'])")
        echo "$seed,$err,$md,$term,$ts" >> $RESULTS_FILE
        echo "  -> error=${err}m min_dist=${md}m term=$term"
    else
        echo "  -> NO RESULT FILE FOUND"
        echo "$seed,999,999,missing,0" >> $RESULTS_FILE
    fi
    sleep 2
done

echo ""
echo "=== SUMMARY ==="
python3 -c "
import csv
with open('$RESULTS_FILE') as f:
    rows = list(csv.DictReader(f))
errs = [float(r['error_m']) for r in rows if float(r['error_m']) < 999]
import statistics
print('N=%d Mean=%.2fm Median=%.2fm Std=%.2fm' % (len(errs), statistics.mean(errs), statistics.median(errs), statistics.stdev(errs) if len(errs)>1 else 0))
s2m = sum(1 for e in errs if e <= 2.0)
print('Success@2m: %d/%d = %.0f%%' % (s2m, len(errs), 100*s2m/len(errs)))
"
echo "=== DONE ==="