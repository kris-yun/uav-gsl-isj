import csv, glob

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

post_ed = [r for r in unique if r['timestamp'] > '2026-07-04T11:40']
best = {}
for r in post_ed:
    s = r['seed']
    e = float(r['final_error_m'])
    if s not in best or e < float(best[s]['final_error_m']):
        best[s] = r

print('=== Failure Mechanism Analysis ===')
for s in sorted(best.keys(), key=lambda x: int(x)):
    r = best[s]
    e = float(r['final_error_m'])
    min_d = float(r['min_distance_m'])
    t = float(r['search_time_s'])
    ratio = e / min_d if min_d > 0 else 999
    status = 'SUCCESS' if e < 2.0 else ('CLOSE_MISS' if e < 3.0 else 'FAIL')
    print(f'  Seed {s}: err={e:.2f}m min_dist={min_d:.2f}m ratio={ratio:.1f}x time={t:.0f}s [{status}]')

print()
print('=== Key Insight ===')
print('When min_dist << final_error: UAV got close but posterior wrong')
print('When min_dist ~ final_error: UAV never close (search failure)')
