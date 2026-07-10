import csv
from collections import defaultdict

abl_data = defaultdict(list)
with open('experiment_results/ablation_10seeds_final.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        abl_data[row['config']].append({
            'error': float(row['error_m']),
            'localized': int(row['localized']),
            'seed': int(row['seed'])
        })

print("SEED-BY-SEED ANALYSIS: Full vs FixedEta")
print("=" * 60)
print(f"{'Seed':<6} {'Full':<12} {'FixedEta':<12} {'Winner':<10} {'Delta':<10}")
print("-" * 60)

full_wins = 0
fixed_wins = 0
ties = 0

for i in range(10):
    full_e = abl_data['Full'][i]['error']
    fixed_e = abl_data['A1_FixedEta'][i]['error']
    delta = fixed_e - full_e
    if full_e < fixed_e - 0.01:
        winner = "Full"
        full_wins += 1
    elif fixed_e < full_e - 0.01:
        winner = "FixedEta"
        fixed_wins += 1
    else:
        winner = "TIE"
        ties += 1
    print(f"{i:<6} {full_e:<12.3f} {fixed_e:<12.3f} {winner:<10} {delta:<+10.3f}")

print("-" * 60)
print(f"Full wins: {full_wins}, FixedEta wins: {fixed_wins}, Ties: {ties}")

print("\n" + "=" * 60)
print("KEY QUESTION: When does FixedEta beat Full?")
print("=" * 60)

for i in range(10):
    full_e = abl_data['Full'][i]['error']
    fixed_e = abl_data['A1_FixedEta'][i]['error']
    if fixed_e < full_e - 0.01:
        print(f"  Seed {i}: Full={full_e:.3f}m, Fixed={fixed_e:.3f}m, Diff={full_e-fixed_e:.3f}m")

print("\n" + "=" * 60)
print("ADAPTIVE ETA COEFFICIENT ANALYSIS")
print("=" * 60)
print("\nCurrent formula:")
print("  detected:   eta = 0.6 + 0.3 * c_w  (c_w in [0,1])")
print("  non-detect: eta = 0.15 + 0.35 * c_w")
print("\nFixed eta = 0.5 (ablation baseline)")
print("\nThe adaptive eta has TWO regimes:")
print("  1. During detection: eta > 0.6 (ALWAYS > fixed 0.5)")
print("  2. During non-detection with low c_w: eta ~ 0.15 (MUCH < fixed 0.5)")
print("  3. During non-detection with high c_w: eta ~ 0.5 (= fixed 0.5)")
print("\nHYPOTHESIS: The problem is regime 2.")
print("  When c_w is low AND no detection, eta drops to 0.15.")
print("  This makes the posterior almost frozen (barely updates).")
print("  If the UAV is actually NEAR the source but wind is chaotic,")
print("  the low eta prevents the posterior from concentrating.")
print("  With fixed eta=0.5, the posterior still updates meaningfully.")
print("\nPROPOSED FIX: eta = 0.3 + 0.4 * c_w for non-detection")
print("  This gives range [0.3, 0.7] instead of [0.15, 0.5]")
print("  The minimum is now 0.3 (not 0.15), preventing posterior freeze.")
