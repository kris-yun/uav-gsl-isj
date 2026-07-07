import csv, glob, os, statistics

results = {}
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv')):
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            seed = row.get('seed','?')
            error = float(row.get('final_error_m',999))
            min_dist = float(row.get('min_distance_m',999))
            term = row.get('termination_reason','?')
            success2 = row.get('localized_success_2m','?')
            success1 = row.get('localized_success_1m','?')
            time_s = float(row.get('search_time_s',0))
            path_m = float(row.get('path_length_m',0))
            if seed not in results or os.path.getmtime(f) > os.path.getmtime(results[seed][0]):
                results[seed] = (f, error, min_dist, term, success2, success1, time_s, path_m)

errors = []
min_dists = []
for seed in sorted(results.keys(), key=int):
    f, err, md, term, s2, s1, t, p = results[seed]
    errors.append(err)
    min_dists.append(md)
    print(f'Seed {seed}: error={err:.2f}m  min_dist={md:.2f}m  s@1m={s1}  s@2m={s2}  time={t:.0f}s  path={p:.1f}m  term={term}')

if errors:
    print(f'\n=== SUMMARY ===')
    print(f'N={len(errors)}  Mean_error={statistics.mean(errors):.2f}m  Median={statistics.median(errors):.2f}m  Std={statistics.stdev(errors):.2f}m')
    succ2 = sum(1 for e in errors if e <= 2.0)
    succ1 = sum(1 for e in errors if e <= 1.0)
    print(f'Success@1m={succ1}/{len(errors)}={100*succ1/len(errors):.0f}%  Success@2m={succ2}/{len(errors)}={100*succ2/len(errors):.0f}%')
    print(f'Min_dist: mean={statistics.mean(min_dists):.2f}m  min={min(min_dists):.2f}m')
    # Key diagnostic: how often UAV got close but final error was large
    close_but_wrong = sum(1 for md, err in zip(min_dists, errors) if md < 1.5 and err > 2.0)
    print(f'Close_but_wrong(min<1.5m, err>2m): {close_but_wrong}/{len(errors)}')
