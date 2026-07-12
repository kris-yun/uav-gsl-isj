import csv, math
from collections import defaultdict

rows = []
with open("/tmp/cp_sbd_exp/eta_ablation/results.csv") as f:
    for r in csv.DictReader(f):
        rows.append(r)

# Group by (method, house)
groups = defaultdict(list)
for r in rows:
    d = r["dist"]
    groups[(r["method"], r["house"])].append(None if d == "NaN" or d == "" else float(d))

# Print per-house results
print("=" * 80)
print("ETA ABLATION - COMPLETE RESULTS (60 runs)")
print("=" * 80)

for h in ["House01", "House02", "House03"]:
    print(f"\n--- {h} ---")
    for m in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0", "Adaptive"]:
        vals = groups.get((m, h), [])
        valid = [v for v in vals if v is not None]
        nan = sum(1 for v in vals if v is None)
        if valid:
            mean = sum(valid) / len(valid)
            std = math.sqrt(sum((x - mean)**2 for x in valid) / len(valid)) if len(valid) > 1 else 0
            label = m.replace("FixedEta_", "eta=").replace("Adaptive", "adpt")
            print(f"  {label:8s}: {mean:.3f} +/- {std:.3f} m  [{len(valid)}/{len(vals)} valid, NaN={nan}]")
        else:
            label = m.replace("FixedEta_", "eta=").replace("Adaptive", "adpt")
            print(f"  {label:8s}: ALL NaN [{len(vals)} runs]")

# Overall summary
print("\n" + "=" * 80)
print("OVERALL SUMMARY")
print("=" * 80)
print(f"{'Method':12s} {'N':>3s} {'Valid':>5s} {'NaN':>3s} {'Rate':>5s} {'Mean':>8s} {'Std':>8s} {'Min':>8s} {'Max':>8s}")
print("-" * 65)

for m in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0", "Adaptive"]:
    all_vals = []
    total_nan = 0
    total = 0
    for h in ["House01", "House02", "House03"]:
        vals = groups.get((m, h), [])
        total += len(vals)
        for v in vals:
            if v is not None:
                all_vals.append(v)
            else:
                total_nan += 1
    if all_vals:
        mean = sum(all_vals) / len(all_vals)
        std = math.sqrt(sum((x - mean)**2 for x in all_vals) / len(all_vals)) if len(all_vals) > 1 else 0
        rate = f"{len(all_vals)/total*100:.0f}%"
        label = m.replace("FixedEta_", "eta=").replace("Adaptive", "adaptive")
        print(f"{label:12s} {total:3d} {len(all_vals):5d} {total_nan:3d} {rate:>5s} {mean:8.3f} {std:8.3f} {min(all_vals):8.3f} {max(all_vals):8.3f}")

# Comparison with baselines
print("\n" + "=" * 80)
print("COMPARISON WITH BASELINES (from baselines_final.csv)")
print("=" * 80)

baselines = defaultdict(list)
with open("/tmp/cp_sbd_exp/baselines_final.csv") as f:
    for r in csv.DictReader(f):
        d = r.get("dist", r.get("map_dist", "NaN"))
        if d and d != "NaN" and d != "N/A":
            try:
                baselines[(r["method"], r["house"])].append(float(d))
            except:
                pass

for m in ["SensorAwareSurgeCastPF", "GrGSL", "PMFS"]:
    all_vals = []
    for h in ["House01", "House02", "House03"]:
        all_vals.extend(baselines.get((m, h), []))
    if all_vals:
        mean = sum(all_vals) / len(all_vals)
        std = math.sqrt(sum((x - mean)**2 for x in all_vals) / len(all_vals)) if len(all_vals) > 1 else 0
        print(f"{m:25s}: mean={mean:.3f} std={std:.3f} n={len(all_vals)}")

# Key finding
print("\n" + "=" * 80)
print("KEY FINDING: ADAPTIVE vs FIXED")
print("=" * 80)

# Compute per-house comparison
for h in ["House01", "House02", "House03"]:
    print(f"\n{h}:")
    for m in ["FixedEta_0.5", "FixedEta_0.7", "FixedEta_1.0", "Adaptive"]:
        vals = [v for v in groups.get((m, h), []) if v is not None]
        nan = sum(1 for v in groups.get((m, h), []) if v is None)
        if vals:
            mean = sum(vals) / len(vals)
            label = m.replace("FixedEta_", "eta=").replace("Adaptive", "adpt")
            print(f"  {label:8s}: {mean:.3f}m ({len(vals)}/{len(vals)+nan} valid)")
