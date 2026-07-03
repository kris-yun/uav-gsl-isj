import csv, os, glob

for house in ["House01", "House02", "House03"]:
    print(f"=== {house} ===")
    for prefix in ["PMFS_baseline", "FUSED", "noWRANF", "noSENPAI", "noGRACE", "noESSA"]:
        files = sorted(glob.glob(f"/tmp/gsl_isj_results/{house}_{prefix}_s*.csv"))
        # Filter out server/traj files
        files = [f for f in files if "_server" not in f and "_traj" not in f and "_path" not in f]
        if not files:
            continue
        dists = []
        for f in files:
            with open(f) as fh:
                rows = list(csv.DictReader(fh))
            if rows and "min_distance_to_source" in rows[0]:
                dists.append(float(rows[0]["min_distance_to_source"]))
        if dists:
            avg = sum(dists) / len(dists)
            print(f"  {prefix}: n={len(dists)} avg={avg:.3f}m min={min(dists):.3f}m max={max(dists):.3f}m")
            for i, d in enumerate(dists):
                print(f"    s{i}: {d:.3f}m")
    print()
