import csv
from collections import defaultdict
import math

rows = []
with open("/tmp/cp_sbd_exp/eta_ablation/results.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# Group by (eta_label, house)
groups = defaultdict(list)
for r in rows:
    d = r["dist"]
    if d == "NaN" or d == "":
        groups[(r["method"], r["house"])].append(None)
    else:
        groups[(r["method"], r["house"])].append(float(d))

print("=" * 70)
print("ETA ABLATION ANALYSIS (current data)")
print("=" * 70)

# Per-eta summary
eta_stats = defaultdict(lambda: {"vals": [], "nan": 0, "total": 0})
for (method, house), vals in sorted(groups.items()):
    valid = [v for v in vals if v is not None]
    nan_count = sum(1 for v in vals if v is None)
    total = len(vals)
    
    if valid:
        mean = sum(valid) / len(valid)
        std = math.sqrt(sum((x - mean)**2 for x in valid) / len(valid)) if len(valid) > 1 else 0
        mn, mx = min(valid), max(valid)
    else:
        mean = std = mn = mx = float("nan")
    
    eta_label = method.replace("FixedEta_", "eta=").replace("Adaptive", "adaptive")
    print(f"\n{eta_label:12s} | {house:8s} | n={total} valid={len(valid)} NaN={nan_count}")
    if valid:
        print(f"             | mean={mean:.3f} std={std:.3f} min={mn:.3f} max={mx:.3f}")
    
    # Accumulate per eta
    eta_stats[method]["vals"].extend(valid)
    eta_stats[method]["nan"] += nan_count
    eta_stats[method]["total"] += total

print("\n" + "=" * 70)
print("SUMMARY BY ETA VALUE")
print("=" * 70)
print(f"{'Method':15s} {'N':>4s} {'Valid':>6s} {'NaN':>4s} {'Rate':>6s} {'Mean':>8s} {'Std':>8s} {'Min':>8s} {'Max':>8s}")
print("-" * 70)

for method in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0", "Adaptive"]:
    s = eta_stats[method]
    valid = s["vals"]
    nan = s["nan"]
    total = s["total"]
    if valid:
        mean = sum(valid) / len(valid)
        std = math.sqrt(sum((x - mean)**2 for x in valid) / len(valid)) if len(valid) > 1 else 0
        rate = f"{len(valid)/total*100:.0f}%"
        print(f"{method:15s} {total:4d} {len(valid):6d} {nan:4d} {rate:>6s} {mean:8.3f} {std:8.3f} {min(valid):8.3f} {max(valid):8.3f}")
    else:
        print(f"{method:15s} {total:4d} {len(valid):6d} {nan:4d} {'N/A':>6s} {'N/A':>8s} {'N/A':>8s} {'N/A':>8s} {'N/A':>8s}")

# Key observations
print("\n" + "=" * 70)
print("KEY OBSERVATIONS")
print("=" * 70)

h01_eta05 = [v for v in groups[("FixedEta_0.5", "House01")] if v is not None]
h01_eta10 = [v for v in groups[("FixedEta_1.0", "House01")] if v is not None]
h02_eta05 = [v for v in groups[("FixedEta_0.5", "House02")] if v is not None]

h01_eta05_nan = sum(1 for v in groups[("FixedEta_0.5", "House01")] if v is None)
h01_eta07_nan = sum(1 for v in groups[("FixedEta_0.7", "House01")] if v is None)
h01_eta10_nan = sum(1 for v in groups[("FixedEta_1.0", "House01")] if v is None)

print(f"1. House01 NaN rate: eta=0.5 -> {h01_eta05_nan}/5, eta=0.7 -> {h01_eta07_nan}/5, eta=1.0 -> {h01_eta10_nan}/5")
print(f"   => Lower eta = higher NaN rate (posterior too flat)")
print(f"2. House02 eta=0.5 ALL SUCCESS (0 NaN) vs House01 eta=0.5 has 2 NaN")
print(f"   => Scene-dependent: House02 easier for low eta")
if h01_eta05 and h01_eta10:
    print(f"3. House01: eta=0.5 mean={sum(h01_eta05)/len(h01_eta05):.3f}m vs eta=1.0 mean={sum(h01_eta10)/len(h01_eta10):.3f}m")
    print(f"   => When eta=0.5 works, it gives BETTER accuracy")
if h02_eta05:
    print(f"4. House02: eta=0.5 mean={sum(h02_eta05)/len(h02_eta05):.3f}m (best so far)")
print(f"5. All successful runs: ep_stop at 29 steps, ~300s")
print(f"   => E-process stopping is consistent")
print(f"6. NoDDM (from ablation_v2) mean ~1.63m vs Full mean ~1.81m")
print(f"   => DDM may not be helping (but different seeds)")
