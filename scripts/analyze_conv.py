import csv, os

# Analyze noWRANF vs FUSED trajectories
for cfg, seeds in [("noWRANF", [0,1,2]), ("FUSED", [0,1,2,3,8,9])]:
    print(f"=== {cfg} ===")
    for s in seeds:
        path = f"/tmp/gsl_isj_results/House01_{cfg}_s{s}_traj.csv"
        if not os.path.exists(path):
            continue
        with open(path) as f:
            rows = list(csv.DictReader(f))
        dists = [(float(r['elapsed_sec']), float(r['dist_to_source']),
                  float(r['x']), float(r['y']),
                  float(r['gas']), float(r['wind_speed'])) for r in rows]
        min_d = min(d[1] for d in dists)
        # Find the closest point
        for t,d,x,y,g,w in dists:
            if abs(d - min_d) < 0.01:
                print(f"  s{s}: closest at t={t:.1f}s dist={d:.3f}m pos=({x:.2f},{y:.2f}) gas={g:.4f} wind={w:.4f}")
                break
        # Show what happens around convergence declaration time (~36s)
        print(f"    Around convergence (35-42s):")
        for t,d,x,y,g,w in dists:
            if 35 < t < 42:
                print(f"      t={t:.1f}s dist={d:.3f}m pos=({x:.2f},{y:.2f}) gas={g:.6f}")
        print()
