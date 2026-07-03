#!/usr/bin/env python3
"""Statistical analysis for e-process ablation experiment results."""
import csv, sys, os
from collections import defaultdict
from scipy import stats as sp_stats
import numpy as np

def load_data(csv_path):
    """Load experiment data."""
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dist = float(row['dist'])
                data.append({
                    'method': row['method'],
                    'house': row['house'],
                    'seed': int(row['seed']),
                    'distance': dist,
                    'steps': int(row['steps']) if row['steps'] else -1,
                    'elapsed': int(row['elapsed']) if row['elapsed'] else -1,
                    'converge': row['converge_type'],
                })
            except (ValueError, KeyError):
                continue
    return data

def compute_stats(data):
    """Compute descriptive statistics."""
    groups = defaultdict(list)
    for d in data:
        groups[(d['method'], d['house'])].append(d['distance'])
    
    print("\n=== Descriptive Statistics (mean ± std, n) ===")
    methods = sorted(set(d['method'] for d in data))
    houses = sorted(set(d['house'] for d in data))
    
    header = f"{'Method':<15}"
    for h in houses:
        header += f" {h:>20}"
    header += f" {'Overall':>20}"
    print(header)
    print("-" * (15 + 21 * (len(houses) + 1)))
    
    for m in methods:
        line = f"{m:<15}"
        all_vals = []
        for h in houses:
            vals = groups.get((m, h), [])
            all_vals.extend(vals)
            if vals:
                mean = np.mean(vals)
                std = np.std(vals, ddof=1) if len(vals) > 1 else 0
                line += f" {mean:.2f}±{std:.2f}(n={len(vals):>2})"
            else:
                line += f" {'—':>20}"
        if all_vals:
            mean = np.mean(all_vals)
            std = np.std(all_vals, ddof=1) if len(all_vals) > 1 else 0
            line += f" {mean:.2f}±{std:.2f}(n={len(all_vals):>2})"
        print(line)
    
    return groups

def pairwise_tests(data, groups):
    """Perform pairwise statistical tests."""
    methods = sorted(set(d['method'] for d in data))
    houses = sorted(set(d['house'] for d in data))
    
    print("\n=== Pairwise Tests: Full vs Each Ablation (Mann-Whitney U) ===")
    print(f"{'Comparison':<30} {'House':<10} {'U-stat':>10} {'p-value':>10} {'Effect size':>12} {'Significant':>12}")
    print("-" * 90)
    
    for h in houses:
        full_vals = groups.get(('Full', h), [])
        if not full_vals:
            continue
        for m in methods:
            if m == 'Full':
                continue
            other_vals = groups.get((m, h), [])
            if not other_vals or len(other_vals) < 2:
                continue
            
            try:
                U, p = sp_stats.mannwhitneyu(full_vals, other_vals, alternative='two-sided')
                # Cliff's delta
                n1, n2 = len(full_vals), len(other_vals)
                delta = (2 * U / (n1 * n2)) - 1  # Cliff's delta
                sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                print(f"Full vs {m:<25} {h:<10} {U:>10.1f} {p:>10.4f} {delta:>12.3f} {sig:>12}")
            except Exception as e:
                print(f"Full vs {m:<25} {h:<10} Error: {e}")

def convergence_analysis(data):
    """Analyze convergence types."""
    print("\n=== Convergence Type Analysis ===")
    conv = defaultdict(lambda: defaultdict(int))
    for d in data:
        conv[d['method']][d['converge']] += 1
    
    methods = sorted(conv.keys())
    all_types = sorted(set(d['converge'] for d in data))
    
    header = f"{'Method':<15}"
    for t in all_types:
        header += f" {t:>12}"
    print(header)
    print("-" * (15 + 13 * len(all_types)))
    
    for m in methods:
        line = f"{m:<15}"
        total = sum(conv[m].values())
        for t in all_types:
            count = conv[m].get(t, 0)
            pct = 100 * count / total if total > 0 else 0
            line += f" {count:>5}({pct:>4.0f}%)"
        print(line)

def stopping_analysis(data):
    """Analyze stopping behavior."""
    print("\n=== Stopping Step Analysis ===")
    steps = defaultdict(list)
    for d in data:
        if d['steps'] > 0:
            steps[d['method']].append(d['steps'])
    
    methods = sorted(steps.keys())
    print(f"{'Method':<15} {'Mean Steps':>12} {'Std Steps':>12} {'Min':>6} {'Max':>6}")
    print("-" * 55)
    for m in methods:
        s = steps[m]
        print(f"{m:<15} {np.mean(s):>12.1f} {np.std(s, ddof=1):>12.1f} {min(s):>6} {max(s):>6}")

def bootstrap_ci(data, n_boot=10000, alpha=0.05):
    """Compute bootstrap confidence intervals."""
    print(f"\n=== Bootstrap {int((1-alpha)*100)}% Confidence Intervals ===")
    groups = defaultdict(list)
    for d in data:
        groups[(d['method'], d['house'])].append(d['distance'])
    
    methods = sorted(set(d['method'] for d in data))
    houses = sorted(set(d['house'] for d in data))
    
    for m in methods:
        for h in houses:
            vals = groups.get((m, h), [])
            if len(vals) < 3:
                continue
            boot_means = []
            for _ in range(n_boot):
                sample = np.random.choice(vals, size=len(vals), replace=True)
                boot_means.append(np.mean(sample))
            ci_low = np.percentile(boot_means, 100 * alpha / 2)
            ci_high = np.percentile(boot_means, 100 * (1 - alpha / 2))
            print(f"{m:<15} {h:<10} {np.mean(vals):.2f} [{ci_low:.2f}, {ci_high:.2f}] (n={len(vals)})")

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cp_sbd_exp/ablation_eprocess.csv"
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)
    
    print(f"Loading data from: {csv_path}")
    data = load_data(csv_path)
    print(f"Loaded {len(data)} valid runs")
    
    if len(data) < 5:
        print("Not enough data for analysis")
        sys.exit(0)
    
    groups = compute_stats(data)
    pairwise_tests(data, groups)
    convergence_analysis(data)
    stopping_analysis(data)
    bootstrap_ci(data)

if __name__ == "__main__":
    main()