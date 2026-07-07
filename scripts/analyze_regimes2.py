import csv

path = r'D:\ZYC\A-gas\src\vgr_all_distances.csv'
with open(path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    data = {}
    for row in reader:
        method = row['method']
        house = row['house']
        dist = float(row['map_dist']) if row['map_dist'] else None
        steps = int(row['steps']) if row['steps'] else None
        if method not in data:
            data[method] = {}
        if house not in data[method]:
            data[method][house] = []
        data[method][house].append({'dist': dist, 'steps': steps})

print('=== VGR Data Summary ===')
for method in sorted(data.keys()):
    for house in sorted(data[method].keys()):
        entries = data[method][house]
        dists = [e['dist'] for e in entries if e['dist'] is not None]
        stepss = [e['steps'] for e in entries if e['steps'] is not None]
        if dists:
            avg_d = sum(dists)/len(dists)
            avg_s = sum(stepss)/len(stepss) if stepss else 0
            print(f'{method:15s} {house:10s} n={len(dists):2d} avg_dist={avg_d:.2f}m avg_steps={avg_s:.1f}')

print()
print('=== Regime Analysis ===')
print('SurgeCast (upwind tracking, needs contact):')
for house in ['House01', 'House02', 'House03']:
    if 'SurgeCast' in data and house in data['SurgeCast']:
        entries = data['SurgeCast'][house]
        dists = [e['dist'] for e in entries if e['dist']]
        if dists:
            avg = sum(dists)/len(dists)
            print(f'  {house}: {avg:.2f}m (n={len(dists)})')

print('Baseline (Infotaxis+eCP):')
for house in ['House01', 'House02', 'House03']:
    if 'Baseline' in data and house in data['Baseline']:
        entries = data['Baseline'][house]
        dists = [e['dist'] for e in entries if e['dist']]
        if dists:
            avg = sum(dists)/len(dists)
            print(f'  {house}: {avg:.2f}m (n={len(dists)})')

print()
print('=== Regime characterization ===')
print('House01: source ~3.1m -> INTERMITTENT regime (SurgeCast FAILS: 3.26m)')
print('House02: source ~1.5m -> CONTACT regime (SurgeCast EXCELS: 0.41m)')
print('House03: source ~1.8m -> TRANSITION regime (moderate: 0.99m)')
print()
print('Our method (Infotaxis):')
print('  House01: 1.31m (good in intermittent)')
print('  House02: 1.91m (poor in contact)')
print('  House03: 1.56m (moderate)')
