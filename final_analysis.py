import csv, math
from collections import defaultdict

# Load entropy data
entropy = defaultdict(list)
with open("/tmp/cp_sbd_exp/eta_ablation/results_entropy.csv") as f:
    for r in csv.DictReader(f):
        d = r["dist"]
        entropy[r["house"]].append(None if d == "NaN" or d == "" else float(d))

# Load old data
old_data = defaultdict(lambda: defaultdict(list))
with open("/tmp/cp_sbd_exp/eta_ablation/results.csv") as f:
    for r in csv.DictReader(f):
        d = r["dist"]
        old_data[r["method"]][r["house"]].append(None if d == "NaN" or d == "" else float(d))

def stats(vals):
    valid = [v for v in vals if v is not None]
    nan = sum(1 for v in vals if v is None)
    if valid:
        m = sum(valid)/len(valid)
        s = math.sqrt(sum((x-m)**2 for x in valid)/len(valid)) if len(valid) > 1 else 0
        return m, s, len(valid), nan
    return float("nan"), float("nan"), 0, nan

print("=" * 75)
print("FINAL COMPARISON: EntropyEta vs Old Adaptive vs Fixed Eta vs Baselines")
print("=" * 75)

# Per-house comparison
for h in ["House01", "House02", "House03"]:
    print(f"\n--- {h} ---")
    for method in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0"]:
        m, s, n, nan = stats(old_data[method].get(h, []))
        label = method.replace("FixedEta_", "eta=")
        print(f"  {label:8s}: {m:.3f} +/- {s:.3f} m  [{n}/{n+nan} valid]")
    
    m, s, n, nan = stats(old_data["Adaptive"].get(h, []))
    print(f"  {'old_adpt':8s}: {m:.3f} +/- {s:.3f} m  [{n}/{n+nan} valid]")
    
    m, s, n, nan = stats(entropy.get(h, []))
    print(f"  {'ENTROPY':8s}: {m:.3f} +/- {s:.3f} m  [{n}/{n+nan} valid]  <<<")

# Overall summary
print("\n" + "=" * 75)
print("OVERALL SUMMARY")
print("=" * 75)
print(f"{'Method':15s} {'Rate':>5s} {'Mean':>8s} {'Std':>8s} {'Min':>8s} {'Max':>8s}")
print("-" * 55)

for method in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0", "Adaptive"]:
    all_v = []
    total_nan = 0
    total = 0
    for h in ["House01", "House02", "House03"]:
        vals = old_data[method].get(h, [])
        total += len(vals)
        for v in vals:
            if v is not None: all_v.append(v)
            else: total_nan += 1
    if all_v:
        m = sum(all_v)/len(all_v)
        s = math.sqrt(sum((x-m)**2 for x in all_v)/len(all_v))
        label = method.replace("FixedEta_", "eta=").replace("Adaptive", "old_adpt")
        print(f"{label:15s} {len(all_v)/total*100:4.0f}% {m:8.3f} {s:8.3f} {min(all_v):8.3f} {max(all_v):8.3f}")

# Entropy
all_e = []
total_e = 0
for h in ["House01", "House02", "House03"]:
    vals = entropy.get(h, [])
    total_e += len(vals)
    for v in vals:
        if v is not None: all_e.append(v)
if all_e:
    m = sum(all_e)/len(all_e)
    s = math.sqrt(sum((x-m)**2 for x in all_e)/len(all_e))
    print(f"{'ENTROPY_eta':15s} {len(all_e)/total_e*100:4.0f}% {m:8.3f} {s:8.3f} {min(all_e):8.3f} {max(all_e):8.3f}  <<<")

# Baselines
print("-" * 55)
baselines = defaultdict(list)
with open("/tmp/cp_sbd_exp/baselines_final.csv") as f:
    for r in csv.DictReader(f):
        d = r.get("dist", r.get("map_dist", ""))
        if d and d != "NaN" and d != "N/A":
            try: baselines[r["method"]].append(float(d))
            except: pass
for m_name in ["SensorAwareSurgeCastPF", "GrGSL", "PMFS"]:
    vals = baselines.get(m_name, [])
    if vals:
        m = sum(vals)/len(vals)
        s = math.sqrt(sum((x-m)**2 for x in vals)/len(vals))
        print(f"{m_name:15s} {'100%':>5s} {m:8.3f} {s:8.3f} {min(vals):8.3f} {max(vals):8.3f}")
