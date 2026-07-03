import csv, os, glob
results_dir = "D:/ZYC/A-gas/experiments/round6_adaptive_sampling/results"
csvs = sorted(glob.glob(os.path.join(results_dir, "House01_*.csv")))
print(f"Found {len(csvs)} CSVs\n")
print(f"{'Config':<12} {'Seed':>4} | {'MinDist':>8} | {'Elapsed':>8} | {'S@1m':>4} | {'S@2m':>4} | {'Timeout':>7}")
print("-" * 70)
for f in csvs:
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            algo = row.get('algorithm_name_from_repo','?')
            seed = row.get('seed','?')
            md = float(row.get('min_distance_to_source', -1))
            el = float(row.get('elapsed_sec', -1))
            s1 = row.get('success_at_1m', '0')
            s2 = row.get('success_at_2m', '0')
            to = row.get('timed_out', 'False')
            print(f"{algo:<12} {seed:>4} | {md:>8.2f} | {el:>7.1f}s | {s1:>4} | {s2:>4} | {to:>7}")
