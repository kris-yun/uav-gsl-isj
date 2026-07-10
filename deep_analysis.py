import csv
import statistics
import math
from collections import defaultdict

# Read ablation data
abl_data = defaultdict(list)
with open('experiment_results/ablation_10seeds_final.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        abl_data[row['config']].append({
            'error': float(row['error_m']),
            'localized': int(row['localized'])
        })

# Read main 160-run data
main_data = defaultdict(lambda: defaultdict(list))
with open('experiment_results/isj_full_160runs.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        main_data[row['method']][row['scenario']].append({
            'error': float(row['error_m']),
            'localized': int(row['localized']),
            'elapsed': float(row['elapsed_s'])
        })

print("=" * 70)
print("DEEP ABLATION ANALYSIS (H01_gnd, 10 seeds each)")
print("=" * 70)

configs = ['Full', 'A1_FixedEta', 'A2_NoEProc', 'A3_NoDDM', 'A4_NoLevy', 'A5_NoUpwind', 'A6_NoGPAlt']
full_errors = [d['error'] for d in abl_data['Full']]
full_success = sum(d['localized'] for d in abl_data['Full'])

for config in configs:
    errors = [d['error'] for d in abl_data[config]]
    success = sum(d['localized'] for d in abl_data[config])
    mean_e = statistics.mean(errors)
    std_e = statistics.stdev(errors)
    
    # Compute delta vs Full
    delta_mean = mean_e - statistics.mean(full_errors)
    delta_success = full_success - success
    
    # Effect size (Cohen's d)
    pooled_std = math.sqrt((statistics.stdev(full_errors)**2 + std_e**2) / 2)
    cohens_d = delta_mean / pooled_std if pooled_std > 0 else 0
    
    # Failure analysis
    failures = [d for d in abl_data[config] if d['localized'] == 0]
    failure_errors = [d['error'] for d in failures]
    
    print(f"\n{config}:")
    print(f"  Mean={mean_e:.3f}m, Std={std_e:.3f}m, Success={success}/10")
    print(f"  Delta: mean +{delta_mean:.3f}m, success -{delta_success}/10")
    print(f"  Cohen's d = {cohens_d:.2f}")
    if failures:
        print(f"  Failure seeds: errors={[f'{e:.2f}' for e in failure_errors]}")
        print(f"  Failure mean error = {statistics.mean(failure_errors):.2f}m")

print("\n" + "=" * 70)
print("MODULE CONTRIBUTION RANKING")
print("=" * 70)

impacts = []
for config in configs[1:]:
    errors = [d['error'] for d in abl_data[config]]
    success = sum(d['localized'] for d in abl_data[config])
    delta_mean = statistics.mean(errors) - statistics.mean(full_errors)
    delta_success = full_success - success
    pooled_std = math.sqrt((statistics.stdev(full_errors)**2 + statistics.stdev(errors)**2) / 2)
    cohens_d = delta_mean / pooled_std if pooled_std > 0 else 0
    impacts.append({
        'config': config,
        'delta_mean': delta_mean,
        'delta_success': delta_success,
        'cohens_d': cohens_d,
        'mean': statistics.mean(errors),
        'success': success
    })

# Sort by impact (success drop + error increase)
impacts.sort(key=lambda x: (-x['delta_success'], -x['delta_mean']))

for i, imp in enumerate(impacts):
    label = imp['config'].split('_', 1)[1] if '_' in imp['config'] else imp['config']
    print(f"  {i+1}. {label}: success -{imp['delta_success']}/10, error +{imp['delta_mean']:.3f}m, d={imp['cohens_d']:.2f}")

print("\n" + "=" * 70)
print("CRITICAL ANALYSIS: Are modules truly independent?")
print("=" * 70)

# Check if Full > sum of parts
full_mean = statistics.mean(full_errors)
print(f"\nFull model mean error: {full_mean:.3f}m")
print(f"\nModule removal impact (error increase):")
for imp in impacts:
    label = imp['config'].split('_', 1)[1] if '_' in imp['config'] else imp['config']
    pct = (imp['delta_mean'] / full_mean) * 100
    print(f"  {label}: +{imp['delta_mean']:.3f}m ({pct:.1f}% increase)")

# Check if any module removal IMPROVES performance
print(f"\nModules that might HURT performance (removal improves):")
for imp in impacts:
    if imp['delta_mean'] < 0:
        label = imp['config'].split('_', 1)[1] if '_' in imp['config'] else imp['config']
        print(f"  WARNING: {label} removal REDUCES error by {-imp['delta_mean']:.3f}m")

# Per-seed analysis: does Full always win?
print(f"\nHead-to-head: Full vs each ablation (per seed)")
for config in configs[1:]:
    wins = sum(1 for i in range(10) if abl_data['Full'][i]['error'] < abl_data[config][i]['error'])
    ties = sum(1 for i in range(10) if abl_data['Full'][i]['error'] == abl_data[config][i]['error'])
    losses = 10 - wins - ties
    label = config.split('_', 1)[1] if '_' in config else config
    print(f"  vs {label}: {wins}W/{ties}T/{losses}L")

print("\n" + "=" * 70)
print("ETA COEFFICIENT ANALYSIS")
print("=" * 70)

# Analyze if the fixed eta coefficients are justified
print("\nCurrent eta formula:")
print("  detected:   eta = 0.6 + 0.3 * c_w  (range [0.6, 0.9])")
print("  non-detect: eta = 0.15 + 0.35 * c_w (range [0.15, 0.5])")
print("\nKey question: Can these be made data-adaptive?")
print("  - The coefficients {0.6, 0.3, 0.15, 0.35} are fixed")
print("  - They control the credibility gap between detection/non-detection")
print("  - Detection eta range [0.6, 0.9] is 1.5-6x the non-detection range [0.15, 0.5]")
print("  - This asymmetry is the CORE mechanism for posterior locking prevention")

# Analyze detection rates from main data
print("\nEmpirical detection rates (from main experiments):")
for method in ['OPGSL']:
    for sc in ['H01_gnd', 'H01_air', 'H02_air', 'H03_gnd']:
        errors = [d['error'] for d in main_data[method][sc]]
        elapsed = [d['elapsed'] for d in main_data[method][sc]]
        print(f"  {sc}: mean_error={statistics.mean(errors):.2f}m, mean_time={statistics.mean(elapsed):.0f}s")
