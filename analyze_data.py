# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict

eprocess_full = {
    'House01': [2.833, 2.072, 1.854, 1.673, 1.188, 2.581, 1.778, 1.288, 0.699, 2.370],
    'House02': [2.895, 1.690, 1.983, 1.828, 1.440, 1.257, 1.859, 1.641, 1.641, 2.060],
    'House03': [0.597, 0.774, 2.504, 2.324, 0.330, 2.243, 2.373, 0.684, 3.622, 2.355],
}

baselines = {
    'PMFS': {'House01': [2.997, 3.094, 3.094], 'House02': [6.772, 5.242, 5.242], 'House03': [5.517, 6.269, 6.269]},
    'GrGSL': {'House01': [3.659, 4.178, 4.178], 'House02': [7.312, 3.556, 6.532], 'House03': [2.208, 7.646, 7.646]},
    'SurgeCast': {'House01': [3.054, 2.855, 3.865], 'House02': [0.439, 0.269, 0.528], 'House03': [1.476, 0.754, 0.754]},
}

v5_final = {
    'House01': [2.540, 1.861, 1.146, 1.697, 1.966, 1.243, 2.540, 1.565, 1.997, 2.032],
    'House02': [1.287, 0.887, 1.107],
}

def stats(dists):
    n = len(dists)
    mean = sum(dists)/n
    std = (sum((d-mean)**2 for d in dists)/n)**0.5
    return mean, std

print('='*70)
print('EXPERIMENTAL DATA ANALYSIS')
print('='*70)

print('\n--- Ours (eprocess_v2, Full, 10 seeds) ---')
for h in ['House01', 'House02', 'House03']:
    m, s = stats(eprocess_full[h])
    print(f'  {h}: mean={m:.3f}m, std={s:.3f}m, n={len(eprocess_full[h])}')
all_ours = [d for ds in eprocess_full.values() for d in ds]
m, s = stats(all_ours)
print(f'  Overall: mean={m:.3f}m, std={s:.3f}m, n={len(all_ours)}')

print('\n--- Ours (v5_final, partial, House01 10seed + House02 3seed) ---')
for h in sorted(v5_final.keys()):
    m, s = stats(v5_final[h])
    print(f'  {h}: mean={m:.3f}m, std={s:.3f}m, n={len(v5_final[h])}')

print('\n--- Baselines (3 seeds) ---')
for method in ['SurgeCast', 'GrGSL', 'PMFS']:
    print(f'  {method}:')
    for h in ['House01', 'House02', 'House03']:
        m, s = stats(baselines[method][h])
        print(f'    {h}: mean={m:.3f}m, std={s:.3f}m')
    all_b = [d for ds in baselines[method].values() for d in ds]
    m, s = stats(all_b)
    print(f'    Overall: mean={m:.3f}m, std={s:.3f}m')

print('\n--- Comparison (Overall mean) ---')
ours_mean = sum(all_ours)/len(all_ours)
for method in ['SurgeCast', 'GrGSL', 'PMFS']:
    all_b = [d for ds in baselines[method].values() for d in ds]
    bm = sum(all_b)/len(all_b)
    better = 'YES' if ours_mean < bm else 'NO'
    print(f'  Ours ({ours_mean:.3f}m) vs {method} ({bm:.3f}m): We better? {better}')

print('\n--- Per-House Winner ---')
for h in ['House01', 'House02', 'House03']:
    ours_m = sum(eprocess_full[h])/len(eprocess_full[h])
    best_method = 'Ours'
    best_mean = ours_m
    for method in ['SurgeCast', 'GrGSL', 'PMFS']:
        bm = sum(baselines[method][h])/len(baselines[method][h])
        if bm < best_mean:
            best_mean = bm
            best_method = method
    print(f'  {h}: Winner={best_method} ({best_mean:.3f}m), Ours={ours_m:.3f}m')

print('\n--- Consistency Analysis ---')
ours_stds = [stats(eprocess_full[h])[1] for h in ['House01','House02','House03']]
sc_stds = [stats(baselines['SurgeCast'][h])[1] for h in ['House01','House02','House03']]
print(f'  Our std across houses: {[f"{s:.3f}" for s in ours_stds]}')
print(f'  SurgeCast std: {[f"{s:.3f}" for s in sc_stds]}')
print(f'  Our coefficient of variation: {s/m*100:.1f}%')