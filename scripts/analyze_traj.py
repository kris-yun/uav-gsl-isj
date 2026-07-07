import csv, os

configs = {
    "FUSED": [0,1,2,3,4,7,8,9],
    "noWRANF": [0,1,2],
    "noSENPAI": [0,1,2],
    "noGRACE": [0,1],
    "noESSA": [0]
}

for cfg, seeds in configs.items():
    print(f"=== {cfg} ===")
    for s in seeds:
        f = f"House01_{cfg}_s{s}_traj.csv"
        if not os.path.exists(f):
            print(f"  s{s}: MISSING")
            continue
        with open(f) as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        if not rows:
            print(f"  s{s}: EMPTY")
            continue
        dists = [float(r["dist_to_source"]) for r in rows]
        min_d = min(dists)
        last_d = dists[-1]
        min_idx = dists.index(min_d)
        min_t = float(rows[min_idx]["elapsed_sec"])
        print(f"  s{s}: min={min_d:.3f}m  end={last_d:.3f}m  min_time={min_t:.1f}s  npts={len(rows)}")
    print()
