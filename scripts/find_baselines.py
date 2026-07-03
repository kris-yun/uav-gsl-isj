import csv, os, glob

# Search for GrGSL and surge_cast results everywhere
search_dirs = ["/tmp/gsl_isj_results", "/home/zyc/HANDOFF/results", "/home/zyc/HANDOFF"]
for d in search_dir if os.path.exists(d := "/home/zyc/HANDOFF/results") else []:
    pass

# Check HANDOFF baseline summary
hf = "/home/zyc/HANDOFF/results/handoff_baseline_summary.csv"
if os.path.exists(hf):
    with open(hf) as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(row)
else:
    print(f"NOT FOUND: {hf}")

# Search all CSVs for GrGSL and surge_cast
import subprocess
result = subprocess.run(["find", "/tmp/gsl_isj_results", "/home/zyc/HANDOFF", "-name", "*GrGSL*", "-o", "-name", "*surge*", "-o", "-name", "*infotaxis*"], capture_output=True, text=True, timeout=5)
print("\n=== Found files ===")
for line in result.stdout.strip().split('\n'):
    if line and '_server' not in line and '_traj' not in line:
        print(f"  {line}")
