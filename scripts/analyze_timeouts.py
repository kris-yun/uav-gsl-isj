import csv, os, glob
results_dir = "D:/ZYC/A-gas/experiments/round6_adaptive_sampling/results"
csvs = sorted(glob.glob(os.path.join(results_dir, "House01_*.csv")))

print(f"=== Round 6 House01 Results Summary ===\n")
print(f"{'Algo':<14} {'Seeds':>5} {'OK':>3} {'TO':>3} | {'MinDist(mean)':>13} {'MinDist(min)':>12} {'S@2m':>5}")
print("-" * 75)

from collections import defaultdict
stats = defaultdict(lambda: {'ok':[], 'to':[], 'dists':[]})

for f in csvs:
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            algo = row.get('algorithm_name_from_repo','?')
            md = float(row.get('min_distance_to_source', -1))
            to = row.get('timed_out', 'False') == 'True'
            s2 = row.get('success_at_2m', '0')
            stats[algo]['dists'].append(md)
            if to:
                stats[algo]['to'].append(md)
            else:
                stats[algo]['ok'].append(md)

for algo in sorted(stats.keys()):
    s = stats[algo]
    n = len(s['dists'])
    n_ok = len(s['ok'])
    n_to = len(s['to'])
    mean_d = sum(s['dists'])/len(s['dists']) if s['dists'] else 0
    min_d = min(s['dists']) if s['dists'] else 0
    s2_count = sum(1 for d in s['dists'] if d <= 2.0)
    print(f"{algo:<14} {n:>5} {n_ok:>3} {n_to:>3} | {mean_d:>13.2f} {min_d:>12.2f} {s2_count:>5}")

# Check timeout patterns
print(f"\n=== Timeout Analysis ===")
for f in csvs:
    name = os.path.basename(f).replace('.csv','')
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            to = row.get('timed_out', 'False')
            el = float(row.get('elapsed_sec', 0))
            n_pos = int(row.get('n_positions', 0))
            md = float(row.get('min_distance_to_source', -1))
            if to == 'True':
                print(f"  {name}: {el:.0f}s, {n_pos} positions, min_dist={md:.2f}m")
