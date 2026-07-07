import math

# OPGSL V7 results (corrected)
opgsl = [1.683, 2.222, 3.387, 2.222, 0.989, 1.665, 1.392, 2.222, 2.222, 1.621]

# Baselines (from experiment)
saiscpf = [2.375, 3.421, 3.421, 2.375, 2.970, 3.421, 3.643, 2.338, 3.482, 2.548]
surgecast = [3.138, 3.151, 3.151, 3.920, 3.151, 2.797, 1.267, 3.678, 3.151, 3.151]
grgsl = [4.271, 4.271, 4.271, 4.271, 2.546, 4.271, 4.271, 4.271, 2.515, 4.271]

def mean(x): return sum(x)/len(x)
def std(x):
    m = mean(x)
    return math.sqrt(sum((xi-m)**2 for xi in x)/(len(x)-1))

def paired_t_test(a, b):
    n = len(a)
    diffs = [ai-bi for ai, bi in zip(a, b)]
    d_bar = mean(diffs)
    s_d = std(diffs)
    t_stat = d_bar / (s_d / math.sqrt(n))
    # Two-tailed p-value approximation for df=9
    # t_crit at p=0.05 two-tailed df=9 is 2.262
    # t_crit at p=0.01 two-tailed df=9 is 3.250
    # t_crit at p=0.001 two-tailed df=9 is 4.781
    if abs(t_stat) > 4.781: p = "<0.001"
    elif abs(t_stat) > 3.250: p = "<0.01"
    elif abs(t_stat) > 2.262: p = "<0.05"
    else: p = ">=0.05 (n.s.)"
    return t_stat, p

print("=" * 60)
print("EXPERIMENT RESULTS - House01, 2,4-1_fast, 10 seeds")
print("=" * 60)
print(f"\n{'Method':<30} {'Mean':>8} {'Std':>8} {'Success(<=2m)':>13}")
print("-" * 60)

for name, data in [("OPGSL (ours)", opgsl), ("SensorAwareSurgeCastPF", saiscpf), ("SurgeCast", surgecast), ("GrGSL", grgsl)]:
    m = mean(data)
    s = std(data)
    succ = sum(1 for e in data if e <= 2.0)
    print(f"{name:<30} {m:>7.3f}m {s:>7.3f}m {succ:>5}/{len(data):<5} ({100*succ/len(data):.0f}%)")

print(f"\n{'='*60}")
print("PAIRED T-TESTS (OPGSL vs each baseline)")
print(f"{'='*60}")
print(f"\n{'Comparison':<35} {'t-stat':>8} {'p-value':>12} {'Sig?':>6}")
print("-" * 60)

for name, data in [("vs SA-SC-PF", saiscpf), ("vs SurgeCast", surgecast), ("vs GrGSL", grgsl)]:
    t_stat, p = paired_t_test(opgsl, data)
    sig = "***" if "***" in p else ("**" if "<0.01" in p else ("*" if "<0.05" in p else "n.s."))
    print(f"{name:<35} {t_stat:>8.3f} {p:>12} {sig:>6}")

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"OPGSL mean error: {mean(opgsl):.3f}m +/- {std(opgsl):.3f}m")
print(f"Best baseline:    {mean(saiscpf):.3f}m (SA-SC-PF)")
print(f"Improvement:      {100*(mean(saiscpf)-mean(opgsl))/mean(saiscpf):.0f}% error reduction")
print(f"Success rate:     {sum(1 for e in opgsl if e<=2.0)}/10 = {100*sum(1 for e in opgsl if e<=2.0)/10:.0f}%")
