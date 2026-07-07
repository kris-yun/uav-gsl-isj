import csv, os

for f in ["/tmp/gsl_clean_results/House01_PMFS_nolimit_s0.csv"]:
    if not os.path.exists(f):
        print("NOT FOUND")
        continue
    with open(f) as fh:
        r = list(csv.DictReader(fh))[0]
    print(f"min_dist={float(r['min_distance_to_source']):.3f}m")
    print(f"server_declared={r['server_declared_error']}")
    print(f"iterations={r['server_iterations']}")
    print(f"elapsed={float(r['elapsed_sec']):.1f}s")
    print(f"timed_out={r['timed_out']}")

tf = "/tmp/gsl_clean_results/House01_PMFS_nolimit_s0_traj.csv"
if os.path.exists(tf):
    with open(tf) as fh:
        rows = list(csv.DictReader(fh))
    dists = [(float(r['elapsed_sec']), float(r['dist_to_source']), float(r['x']), float(r['y']), float(r['gas'])) for r in rows]
    min_d = min(d[1] for d in dists)
    for d in dists:
        if abs(d[1] - min_d) < 0.01:
            print(f"Min: {min_d:.3f}m at t={d[0]:.1f}s ({d[2]:.2f},{d[3]:.2f}) gas={d[4]:.4f}")
            break
    for t_target in [30, 60, 90, 120]:
        for d in dists:
            if abs(d[0] - t_target) < 2:
                print(f"  t={t_target}: {d[1]:.3f}m ({d[2]:.2f},{d[3]:.2f}) gas={d[4]:.4f}")
