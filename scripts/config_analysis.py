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

jul3 = [r for r in unique if '2026-07-03' in r['timestamp']]
jul4 = [r for r in unique if '2026-07-04' in r['timestamp']]

print('=== Jul3 config ===')
r0 = jul3[0]
for k in ['environment_id','scenario_id','dataset','config_id','source_config','wind_config','start_config']:
    print(f'  {k}={r0.get(k,"")}')

print()
print('=== Jul4 config ===')
r1 = jul4[0]
for k in ['environment_id','scenario_id','dataset','config_id','source_config','wind_config','start_config']:
    print(f'  {k}={r1.get(k,"")}')

print()
print('=== Jul3 module flags ===')
for k in sorted(r0.keys()):
    if k.startswith('use_'):
        print(f'  {k}={r0[k]}')

print()
print('=== Jul4 module flags ===')
for k in sorted(r1.keys()):
    if k.startswith('use_'):
        print(f'  {k}={r1[k]}')

print()
print('=== Jul3: runs from different configs ===')
configs3 = set()
for r in jul3:
    configs3.add((r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')))
for c in sorted(configs3):
    count = sum(1 for r in jul3 if (r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')) == c)
    errors = [float(r['final_error_m']) for r in jul3 if r['final_error_m'] and (r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')) == c]
    import statistics
    mean_e = statistics.mean(errors) if errors else 0
    print(f'  {c}: n={count} mean_err={mean_e:.3f}')

print()
print('=== Jul4: runs from different configs ===')
configs4 = set()
for r in jul4:
    configs4.add((r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')))
for c in sorted(configs4):
    count = sum(1 for r in jul4 if (r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')) == c)
    errors = [float(r['final_error_m']) for r in jul4 if r['final_error_m'] and (r.get('environment_id',''), r.get('scenario_id',''), r.get('start_config','')) == c]
    mean_e = statistics.mean(errors) if errors else 0
    print(f'  {c}: n={count} mean_err={mean_e:.3f}')
