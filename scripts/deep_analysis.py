import csv, glob, statistics
from collections import Counter

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

jul3 = [r for r in unique if '2026-07-03' in r['timestamp']]
jul3.sort(key=lambda x: float(x.get('final_error_m','99')))

print('=== Jul3 TOP 10 best results ===')
for r in jul3[:10]:
    print(f"  err={float(r['final_error_m']):.3f}m min_dist={float(r['min_distance_m']):.3f}m time={float(r['search_time_s']):.1f}s term={r['termination_reason']} loc2m={r['localized_success_2m']} seed={r['seed']} ts={r['timestamp']}")

print()
print('=== Jul3 module settings from best run ===')
best = jul3[0]
for k in ['use_sdbe','use_iasc','use_sepf','use_pcrd','use_pgn','use_hmm','ablation_id','method','method_family']:
    print(f'  {k}={best.get(k,"")}')
    
print()
terms = Counter(r['termination_reason'] for r in jul3)
print(f'Jul3 terminations: {dict(terms)}')

print()
print('=== Jul3: runs with error < 1.5m ===')
excellent = [r for r in jul3 if float(r.get('final_error_m','99')) < 1.5]
print(f'Count: {len(excellent)}')
for r in excellent:
    print(f"  err={float(r['final_error_m']):.3f}m seed={r['seed']} term={r['termination_reason']} ts={r['timestamp']}")

print()
print('=== Jul3: check if any EDPA-STOP in Jul3 ===')
for r in jul3:
    if 'edpa' in str(r).lower() or 'EDPA' in str(r):
        print(f"  Found EDPA reference: {r['timestamp']}")
        
print()
print('=== Jul4 detailed per-run ===')
jul4 = [r for r in unique if '2026-07-04' in r['timestamp']]
jul4.sort(key=lambda x: x['timestamp'])
for r in jul4:
    print(f"  s{r['seed']} err={float(r['final_error_m']):.3f}m min={float(r['min_distance_m']):.3f}m time={float(r['search_time_s']):.1f}s term={r['termination_reason']} ts={r['timestamp']}")
