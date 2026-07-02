#!/usr/bin/env python3
"""Analyze ablation and baseline logs with proper ANSI stripping."""
import re, csv, os, glob

DIR = "/tmp/cp_sbd_exp"
HOUSES = {
    "House01": (-0.40, -2.90, -0.30),
    "House02": (0.0, -1.0, 0.2),
    "House03": (-0.45, 1.9, -0.1),
}

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def analyze_log(log_file, method, house, seed):
    sx, sy, sz = HOUSES[house]
    with open(log_file) as f:
        content = strip_ansi(f.read())
    
    step_lines = re.findall(r"OPGSL-AI step=(\d+) \(([-\d.]+),([-\d.]+),([-\d.]+)\)", content)
    if step_lines:
        last = step_lines[-1]
        steps = int(last[0])
        ex, ey = float(last[1]), float(last[2])
        dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
    else:
        steps = 0
        dist = None
    
    map_lines = re.findall(r"posterior_MAP=\(([-\d.]+),([-\d.]+),([-\d.]+)\)", content)
    if map_lines:
        ml = map_lines[-1]
        mx, my = float(ml[0]), float(ml[1])
        map_dist = ((mx - sx)**2 + (my - sy)**2)**0.5
    elif dist is not None:
        map_dist = dist
    else:
        map_dist = None
    
    if "Found the emission source" in content: ctype = "found"
    elif "search complete" in content: ctype = "search_complete"
    elif "CP-STOP" in content: ctype = "cp_stop"
    elif "DDM-STOP" in content: ctype = "ddm_stop"
    elif "CONVERGED" in content: ctype = "converged"
    elif "HARD TIMEOUT" in content: ctype = "timeout"
    else: ctype = "other"
    
    elapsed_match = re.findall(r"t=([-\d.]+)", content)
    elapsed = float(elapsed_match[-1]) if elapsed_match else 0.0
    
    return {
        "method": method, "house": house, "seed": seed,
        "map_dist": "%.3f" % map_dist if map_dist else "N/A",
        "steps": steps, "elapsed": "%.1f" % elapsed,
        "converge_type": ctype
    }

# Analyze ablation logs
rows = []
for log_file in sorted(glob.glob(os.path.join(DIR, "*.log"))):
    fname = os.path.basename(log_file)
    # Match ablation pattern: Method_House_sSeed.log
    m = re.match(r"(\w+)_(House\d+)_s(\d+)\.log", fname)
    if not m: continue
    method, house, seed = m.group(1), m.group(2), int(m.group(3))
    if method == "baseline": continue
    rows.append(analyze_log(log_file, method, house, seed))

# Write ablation summary
fields = ["method","house","seed","map_dist","steps","elapsed","converge_type"]
with open(os.path.join(DIR, "ablation_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

print("=== ABLATION RESULTS ===")
print(",".join(fields))
for r in rows: print(",".join(str(r[k]) for k in fields))

print("\n=== Summary by method ===")
methods = sorted(set(r["method"] for r in rows))
for m in methods:
    ds = [float(r["map_dist"]) for r in rows if r["method"]==m and r["map_dist"]!="N/A"]
    ss = [int(r["steps"]) for r in rows if r["method"]==m and r["steps"]>0]
    if ds:
        ds.sort()
        print(f"{m}: n={len(ds)} median_dist={ds[len(ds)//2]:.3f}m mean_dist={sum(ds)/len(ds):.3f}m "
              f"mean_steps={sum(ss)/len(ss):.0f}" if ss else f"{m}: n={len(ds)} median={ds[len(ds)//2]:.3f}m")
    else:
        print(f"{m}: no results yet ({len([r for r in rows if r['method']==m])} runs logged)")