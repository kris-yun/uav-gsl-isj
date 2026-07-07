import csv
path = "/tmp/gsl_clean_results/House01_WRANF_v4_s0_traj.csv"
with open(path) as f:
    rows = list(csv.DictReader(f))
dists = [(float(r['elapsed_sec']), float(r['dist_to_source']), float(r['x']), float(r['y']), float(r['gas'])) for r in rows]
min_d = min(d[1] for d in dists)
min_entry = [d for d in dists if abs(d[1] - min_d) < 0.01][0]
print(f"Min distance: {min_d:.3f}m at t={min_entry[0]:.1f}s pos=({min_entry[2]:.2f},{min_entry[3]:.2f}) gas={min_entry[4]:.4f}")
# Show distances at key timestamps
for t_target in [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]:
    near = [d for d in dists if abs(d[0] - t_target) < 2]
    if near:
        d = near[-1]
        print(f"  t={d[0]:.0f}s: dist={d[1]:.3f}m pos=({d[2]:.2f},{d[3]:.2f}) gas={d[4]:.4f}")
