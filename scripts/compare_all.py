import csv, os

source = (-0.4, -2.9)
base = "D:/ZYC/A-gas/HANDOFF/results"
tmp = "/tmp/gsl_isj_results"

print(f"Source: ({source[0]}, {source[1]})")
print()
print(f"{'Method':<25} {'n':>3} {'avg_min':>8} {'min':>8} {'max':>8}")
print("-" * 60)

for method in ["PMFS", "GrGSL", "surge_cast"]:
    dists = []
    for s in range(10):
        f = f"{base}/House01_{method}_s{s}.csv"
        if os.path.exists(f):
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    dists.append(float(row.get("min_distance_to_source", 0)))
                    break
    if dists:
        avg = sum(dists) / len(dists)
        print(f"{method + ' (HANDOFF)':<25} {len(dists):>3} {avg:>8.3f} {min(dists):>8.3f} {max(dists):>8.3f}")

# From /tmp
for label, pattern in [
    ("PMFS (clean)", "PMFS_baseline"),
    ("FUSED", "FUSED"),
    ("orig_wranf", "orig_wranf"),
    ("WRANF_SENPAI", "WRANF_SENPAI"),
]:
    dists = []
    for s in range(10):
        f = f"{tmp}/House01_{pattern}_s{s}.csv"
        if os.path.exists(f):
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    dists.append(float(row.get("min_distance_to_source", 0)))
                    break
    if dists:
        avg = sum(dists) / len(dists)
        print(f"{label:<25} {len(dists):>3} {avg:>8.3f} {min(dists):>8.3f} {max(dists):>8.3f}")

# Get endpoint positions for each method
print("\n=== CLOSEST APPROACH POSITIONS ===")
for method in ["PMFS", "GrGSL", "surge_cast"]:
    for s in range(3):
        tf = f"{base}/House01_{method}_s{s}_traj.csv"
        if os.path.exists(tf):
            with open(tf) as fh:
                rows = list(csv.DictReader(fh))
            if rows:
                # Find min distance point
                min_d = 999
                min_r = None
                for r in rows:
                    d = float(r.get("dist_to_source", 999))
                    if d < min_d:
                        min_d = d
                        min_r = r
                if min_r:
                    x, y = float(min_r['x']), float(min_r['y'])
                    g = float(min_r.get('gas', 0))
                    w = float(min_r.get('wind_speed', 0))
                    wd = float(min_r.get('wind_dir', 0))
                    print(f"  {method} s{s}: closest=({x:.2f},{y:.2f}) dist={min_d:.3f}m gas={g:.4f} wind={w:.4f} dir={wd:.2f}")
