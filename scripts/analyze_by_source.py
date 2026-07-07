import csv, glob, os, statistics

# Analyze by source position
by_source = {}
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv')):
    with open(f) as fh:
        r = csv.DictReader(fh).__next__()
        src = (r.get('ground_truth_x','?'), r.get('ground_truth_y','?'))
        err = float(r.get('final_error_m', 999))
        ts = r.get('timestamp','')
        seed = r.get('seed','?')
        if src not in by_source:
            by_source[src] = []
        by_source[src].append((ts, err, seed))

for src, runs in sorted(by_source.items()):
    errors = [e for _, e, _ in runs]
    n = len(errors)
    mean = statistics.mean(errors)
    med = statistics.median(errors)
    s2m = sum(1 for e in errors if e <= 2.0)
    print(f'\nSource {src}: N={n}  Mean={mean:.2f}m  Median={med:.2f}m  Success@2m={s2m}/{n}={100*s2m/n:.0f}%')
    # Show per-date breakdown
    dates = {}
    for ts, err, seed in runs:
        d = ts[:10]
        if d not in dates: dates[d] = []
        dates[d].append(err)
    for d in sorted(dates):
        de = dates[d]
        print(f'  {d}: N={len(de)} Mean={statistics.mean(de):.2f}m  Success@2m={sum(1 for e in de if e<=2.0)}/{len(de)}')
