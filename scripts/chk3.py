import csv, glob, os

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
        if seed not in results or ts > results[seed][0]:
            results[seed] = (ts, err, md)

# Show only latest 3 seeds
for seed in ['0', '1', '2']:
    if seed in results:
        ts, err, md = results[seed]
        print("Seed %s: error=%.2fm  min_dist=%.2fm  ts=%s" % (seed, err, md, ts[:19]))