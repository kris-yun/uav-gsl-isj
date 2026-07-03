import csv, os, math

source = (-0.4, -2.9)
base = "D:/ZYC/A-gas/HANDOFF/results"

print(f"Source: ({source[0]}, {source[1]})")
print(f"{'Method':<20} {'n':>3} {'avg_min':>8} {'min':>8} {'max':>8} {'avg_end':>8}")
print("-" * 65)

for method in ["PMFS", "GrGSL", "surge_cast"]:
    dists = []
    end_dists = []
    for s in range(8):
        f = f"{base}/House01_{method}_s{s}.csv"
        if not os.path.exists(f):
            continue
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                md = float(row.get("min_distance_to_source", 0))
                dists.append(md)
                break
    
    if dists:
        avg = sum(dists) / len(dists)
        print(f"{method:<20} {len(dists):>3} {avg:>8.3f} {min(dists):>8.3f} {max(dists):>8.3f}")

# Also show the newer PMFS baseline from /tmp
print("\n=== PMFS baseline (newer, /tmp) ===")
for f_name in ["PMFS_baseline", "PMFS_BASELINE"]:
    dists = []
    for s in range(10):
        f = f"/tmp/gsl_isj_results/House01_{f_name}_s{s}.csv"
        if os.path.exists(f):
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    dists.append(float(row.get("min_distance_to_source", 0)))
                    break
    if dists:
        avg = sum(dists) / len(dists)
        print(f"  {f_name}: n={len(dists)} avg={avg:.3f} min={min(dists):.3f} max={max(dists):.3f}")

# Key methods comparison
print("\n=== KEY RESULTS COMPARISON ===")
print(f"{'Method':<25} {'n':>3} {'avg':>8} {'min':>8} {'improvement':>12}")
print("-" * 60)
baseline_avg = None
for method_name, dir_path, pattern in [
    ("PMFS (official)", base, "PMFS"),
    ("GrGSL (official)", base, "GrGSL"),
    ("surge_cast (official)", base, "surge_cast"),
    ("PMFS (/tmp newer)", "/tmp/gsl_isj_results", "PMFS_baseline"),
    ("FUSED (WRANF)", "/tmp/gsl_isj_results", "FUSED"),
    ("orig_wranf", "/tmp/gsl_isj_results", "orig_wranf"),
    ("WRANF_SENPAI", "/tmp/gsl_isj_results", "WRANF_SENPAI"),
]:
    dists = []
    for s in range(10):
        f = f"{dir_path}/House01_{method_name if method_name.startswith('PMFS') else pattern}_s{s}.csv"
        if not os.path.exists(f):
            f = f"{dir_path}/House01_{pattern}_s{s}.csv"
        if os.path.exists(f):
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    dists.append(float(row.get("min_distance_to_source", 0)))
                    break
    if dists:
        avg = sum(dists) / len(dists)
        if baseline_avg is None:
            baseline_avg = avg
        impr = (baseline_avg - avg) / baseline_avg * 100 if baseline_avg else 0
        print(f"{method_name:<25} {len(dists):>3} {avg:>8.3f} {min(dists):>8.3f} {impr:>+11.1f}%")
