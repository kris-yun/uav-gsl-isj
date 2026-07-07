import csv, os

# Check the old baseline data from HANDOFF/results
baseline_dir = "/tmp/gsl_isj_results"
# June 11 PMFS baseline results
for s in range(8):
    path = f"{baseline_dir}/House01_PMFS_s{s}.csv"  
    if not os.path.exists(path):
        path = f"{baseline_dir}/House01_PMFS_baseline_s{s}.csv"
    if os.path.exists(path):
        with open(path) as f:
            rows = list(csv.DictReader(f))
        if rows:
            r = rows[0]
            method = r.get("method", "unknown")
            dist = r.get("min_distance_to_source", "?")
            declared = r.get("server_declared_error", "?")
            print(f"s{s}: method={method} min_dist={dist} declared={declared}")

print("\n=== Today noWRANF ===")
for s in range(3):
    path = f"{baseline_dir}/House01_noWRANF_s{s}.csv"
    if os.path.exists(path):
        with open(path) as f:
            rows = list(csv.DictReader(f))
        if rows:
            r = rows[0]
            method = r.get("method", "unknown")
            dist = r.get("min_distance_to_source", "?")
            declared = r.get("server_declared_error", "?")
            print(f"s{s}: method={method} min_dist={dist} declared={declared}")
