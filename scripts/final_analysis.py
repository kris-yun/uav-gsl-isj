import csv, glob, os, statistics

results = {}
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv')):
    with open(f) as fh:
        r = csv.DictReader(fh).__next__()
        src_x = float(r.get('ground_truth_x', 0))
        src_y = float(r.get('ground_truth_y', 0))
        if abs(src_x - 5.0) > 0.1 or abs(src_y - 6.2) > 0.1:
            continue
        seed = r.get('seed', '?')
        ts = r.get('timestamp', '')
        err = float(r.get('final_error_m', 999))
        md = float(r.get('min_distance_m', 999))
        s2m = r.get('localized_success_2m', '0')
        s1m = r.get('localized_success_1m', '0')
        if seed not in results or ts > results[seed][0]:
            results[seed] = (ts, err, md, s2m, s1m)

# Only show most recent 10 seeds
seeds_sorted = sorted(results.keys(), key=lambda s: results[s][0], reverse=True)[:10]
seeds_sorted.sort(key=lambda s: int(s))

errors = []
for seed in seeds_sorted:
    ts, err, md, s2m, s1m = results[seed]
    errors.append(err)
    print("Seed %s: error=%.2fm  min_dist=%.2fm  s@1m=%s  s@2m=%s  ts=%s" % (seed, err, md, s1m, s2m, ts[:19]))

if errors:
    print("\n=== SUMMARY ===")
    print("N=%d  Mean=%.2fm  Median=%.2fm  Std=%.2fm" % (len(errors), statistics.mean(errors), statistics.median(errors), statistics.stdev(errors) if len(errors)>1 else 0))
    s2m = sum(1 for e in errors if e <= 2.0)
    s1m = sum(1 for e in errors if e <= 1.0)
    print("Success@1m: %d/%d = %.0f%%" % (s1m, len(errors), 100*s1m/len(errors)))
    print("Success@2m: %d/%d = %.0f%%" % (s2m, len(errors), 100*s2m/len(errors)))