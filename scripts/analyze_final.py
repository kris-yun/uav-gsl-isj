import csv, glob, statistics

records = []
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*.csv')):
    try:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                records.append(row)
    except:
        pass

seen = set()
unique = []
for r in records:
    ts = r.get('timestamp','')
    if ts not in seen:
        seen.add(ts)
        unique.append(r)

# Latest runs (post 10:30)
today_late = [r for r in unique if '2026-07-04' in r['timestamp'] and r['timestamp'] > '2026-07-04T10:30']
today_late.sort(key=lambda x: x['timestamp'])

print(f'Records post 10:30: {len(today_late)}')
for r in today_late:
    print(f"  s{r['seed']} err={float(r['final_error_m']):.3f}m min={float(r['min_distance_m']):.3f}m time={float(r['search_time_s']):.1f}s term={r['termination_reason']} loc2m={r['localized_success_2m']} ts={r['timestamp']}")

# Best per seed
best = {}
for r in today_late:
    s = r['seed']
    e = float(r['final_error_m'])
    if s not in best or e < float(best[s]['final_error_m']):
        best[s] = r

print()
print('Best per seed (event-driven):')
errors = []
for s in sorted(best.keys(), key=lambda x: int(x)):
    r = best[s]
    e = float(r['final_error_m'])
    errors.append(e)
    print(f"  Seed {s}: error={e:.3f}m time={float(r['search_time_s']):.1f}s term={r['termination_reason']}")

if errors:
    print(f'Mean: {statistics.mean(errors):.3f}m, Std: {statistics.stdev(errors) if len(errors)>1 else 0:.3f}m')
    print(f'Success@2m: {sum(1 for e in errors if e < 2.0)}/{len(errors)}')
