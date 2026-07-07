import csv, os, glob

results_dir = "/tmp/gsl_isj_results"
source = (-0.4, -2.9)

print("=" * 70)
print(f"Source location: ({source[0]}, {source[1]})")
print("=" * 70)

for house in ["House01", "House02"]:
    print(f"\n=== {house} ===")
    methods = {}
    for f in sorted(glob.glob(f"{results_dir}/{house}_*_s*.csv")):
        fname = os.path.basename(f)
        if "_server" in fname or "_traj" in fname or "_path" in fname:
            continue
        # Parse method name: House01_METHODNAME_s0.csv
        parts = fname.replace(house + "_", "").rsplit("_s", 1)
        if len(parts) < 2:
            continue
        method = parts[0]
        
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                md = float(row.get("min_distance_to_source", 0))
                ep_x = float(row.get("end_x", 0)) if "end_x" in row else None
                ep_y = float(row.get("end_y", 0)) if "end_y" in row else None
                methods.setdefault(method, []).append(md)
                break
    
    for method, dists in sorted(methods.items()):
        avg = sum(dists) / len(dists)
        print(f"  {method:25s}: n={len(dists):2d}  avg={avg:.3f}m  range=[{min(dists):.3f}, {max(dists):.3f}]")
