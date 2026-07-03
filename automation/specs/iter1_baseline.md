# Iteration 1: Baseline Validation

## Objective
Verify current DQA-AS performance and establish baseline metrics.

## Task
Run DQA-AS and all baselines on House01 with 5 seeds for both ideal and slow_mox sensors.

## Steps

### 1. Check Existing Results
First, check if we already have baseline results:
`python
import csv
from collections import defaultdict
import statistics

files = [
    'D:/ZYC/A-gas/workspace/uav_diagsense/results/h01_final_fair.csv',
    'D:/ZYC/A-gas/workspace/uav_diagsense/results/h01_slow_final.csv',
]

for path in files:
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    methods = defaultdict(list)
    for row in data:
        methods[row['method']].append(float(row['best_error_m']))
    
    print(f'\n=== {path.split("/")[-1]} ===')
    for m in sorted(methods.keys()):
        errors = methods[m]
        mean = statistics.mean(errors)
        n = len(errors)
        s1 = sum(1 for e in errors if e <= 1.0)
        s2 = sum(1 for e in errors if e <= 2.0)
        print(f'{m:15s}: n={n:3d}, mean={mean:.3f}, s@1={s1}/{n}, s@2={s2}/{n}')
`

### 2. If Results Exist
Copy to automation/results/ and create summary:
`ash
cp D:/ZYC/A-gas/workspace/uav_diagsense/results/h01_final_fair.csv D:/ZYC/A-gas/automation/results/iter1_baseline_ideal.csv
cp D:/ZYC/A-gas/workspace/uav_diagsense/results/h01_slow_final.csv D:/ZYC/A-gas/automation/results/iter1_baseline_slow.csv
`

### 3. Create Summary Report
Write to utomation/results/iter1_summary.md:
`markdown
# Iteration 1 Summary: Baseline Validation

## Results

### Ideal Sensor
| Method | N | Mean Error | Success@1m | Success@2m |
|--------|---|------------|------------|------------|
| DQA_AS | 5 | X.XXX | X/5 | X/5 |
| GreedyMAP | 5 | X.XXX | X/5 | X/5 |
| Random | 5 | X.XXX | X/5 | X/5 |
| KLD | 5 | X.XXX | X/5 | X/5 |
| Infotaxis | 5 | X.XXX | X/5 | X/5 |
| SurgeCast | 5 | X.XXX | X/5 | X/5 |

### Slow MOX Sensor
| Method | N | Mean Error | Success@1m | Success@2m |
|--------|---|------------|------------|------------|
| DQA_AS | 5 | X.XXX | X/5 | X/5 |
| GreedyMAP | 5 | X.XXX | X/5 | X/5 |
| Random | 5 | X.XXX | X/5 | X/5 |
| KLD | 5 | X.XXX | X/5 | X/5 |
| Infotaxis | 5 | X.XXX | X/5 | X/5 |
| SurgeCast | 5 | X.XXX | X/5 | X/5 |

## Key Findings
- DQA-AS performance vs baselines: [BETTER/SAME/WORSE]
- Sensor impact: [ideal vs slow_mox difference]

## Status
- [x] Baseline results collected
- [x] Summary created
- Ready for Iteration 2
`

### 4. Output
When complete, tell me:
"Iteration 1 complete. Baseline results saved to automation/results/iter1_summary.md"

## Success Criteria
- Results match existing h01_final_fair.csv (¡À5%)
- Summary file created with all metrics
- No crashes or errors
