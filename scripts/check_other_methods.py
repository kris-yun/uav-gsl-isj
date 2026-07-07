import csv, os, glob

# Check HANDOFF baselines for GrGSL and surge_cast
handoff_dir = "/home/zyc/HANDOFF/results"
alt_dir = "/tmp/gsl_isj_results"

print("=== Other algorithms on House01 ===")
for prefix in ["GrGSL", "surge_cast"]:
    for d in [handoff_dir, alt_dir]:
        files = sorted(glob.glob(f"{d}/House01_{prefix}_s*.csv"))
        files = [f for f in files if "_server" not in f and "_traj" not in f and "_path" not in f]
        if files:
            print(f"\n  {prefix} (from {d}):")
            for f in files:
                with open(f) as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        md = float(row.get("min_distance_to_source", 0))
                        print(f"    {os.path.basename(f)}: min_dist={md:.3f}m")
                        break

# Check for endpoint data
print("\n=== Endpoint positions (from traj data) ===")
for method, seeds in [("PMFS_baseline", [0,1,2,3,4,5]), ("FUSED", [0,1,2,3,8,9])]:
    for s in seeds:
        tf = f"{alt_dir}/House01_{method}_s{s}_traj.csv"
        if os.path.exists(tf):
            with open(tf) as fh:
                rows = list(csv.DictReader(fh))
            if rows:
                last = rows[-1]
                x, y = float(last['x']), float(last['y'])
                import math
                dist = math.sqrt((x - (-0.4))**2 + (y - (-2.9))**2)
                print(f"  {method} s{s}: end=({x:.2f},{y:.2f}) dist={dist:.3f}m")
