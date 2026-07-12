import re, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sources = {
    'House01': (-0.40, -2.90),
    'House02': (0.00, -1.00),
    'House03': (8.20, 5.00),
}

result = subprocess.run(['ssh', 'zyc@192.168.111.128', 
    "grep -E '(House|seed=|EP-STOP|RESULT:)' /tmp/cp_sbd_exp/wagbi_final/run.log"],
    capture_output=True, text=True, timeout=15)

lines = result.stdout.split('\n')

current_house = None
current_seed = None
results = []

for line in lines:
    hm = re.search(r'--- (House\d+) seed=(\d+) ---', line)
    if hm:
        current_house = hm.group(1)
        current_seed = int(hm.group(2))
        continue
    
    rm = re.search(r'EP-STOP.*MAP=\(([-\d.]+),([-\d.]+)', line)
    if rm and current_house:
        mx, my = float(rm.group(1)), float(rm.group(2))
        sx, sy = sources[current_house]
        dist = ((mx - sx)**2 + (my - sy)**2)**0.5
        results.append((current_house, current_seed, mx, my, dist))

print('method,house,seed,map_x,map_y,dist')
for r in results:
    print(f'Full,{r[0]},{r[1]},{r[2]},{r[3]},{r[4]:.3f}')

from collections import defaultdict
by_house = defaultdict(list)
for r in results:
    by_house[r[0]].append(r[4])

print('\n=== SUMMARY ===')
for house in sorted(by_house.keys()):
    dists = by_house[house]
    mean_d = sum(dists)/len(dists)
    std_d = (sum((d-mean_d)**2 for d in dists)/len(dists))**0.5
    print(f'{house}: mean={mean_d:.3f}m, std={std_d:.3f}m, n={len(dists)}')
    
all_dists = [r[4] for r in results]
mean_all = sum(all_dists)/len(all_dists)
std_all = (sum((d-mean_all)**2 for d in all_dists)/len(all_dists))**0.5
print(f'Overall: mean={mean_all:.3f}m, std={std_all:.3f}m, n={len(all_dists)}')
