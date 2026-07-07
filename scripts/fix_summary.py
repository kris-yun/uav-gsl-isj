#!/usr/bin/env python3
"""Fix summary.csv by re-parsing logs."""
import re, csv, os, glob

DIR = "/tmp/cp_sbd_exp"
HOUSES = {
    "House01": (-0.40, -2.90, -0.30),
    "House02": (0.0, -1.0, 0.2),
    "House03": (-0.45, 1.9, -0.1),
}
rows = []
for log_file in sorted(glob.glob(os.path.join(DIR, "House*_s*.log"))):
    fname = os.path.basename(log_file)
    m = re.match(r"(House\d+)_s(\d+)\.log", fname)
    if not m:
        continue
    house = m.group(1)
    seed = int(m.group(2))
    sx, sy, sz = HOUSES[house]
    
    with open(log_file) as f:
        content = f.read()
    
    # Extract last OPGSL-AI step position
    step_lines = re.findall(r"OPGSL-AI step=(\d+) \(([-\d.]+),([-\d.]+),([-\d.]+)\)", content)
    if step_lines:
        last = step_lines[-1]
        steps = int(last[0])
        ex, ey = float(last[1]), float(last[2])
        dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
    else:
        steps = 0
        dist = None
    
    # Convergence type
    if "Found the emission source" in content:
        ctype = "found"
    elif "search complete" in content:
        ctype = "search_complete"
    elif "DONE, CLOSING" in content:
        ctype = "closed"
    else:
        ctype = "died"
    
    rows.append({
        "house": house, "seed": seed,
        "map_dist": "%.3f" % dist if dist else "N/A",
        "steps": steps, "converge_type": ctype,
    })

# Write summary
with open(os.path.join(DIR, "summary_fixed.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["house", "seed", "map_dist", "steps", "converge_type"])
    w.writeheader()
    w.writerows(rows)

# Print results
print("house,seed,map_dist,steps,converge_type")
for r in rows:
    print(f"{r['house']},{r['seed']},{r['map_dist']},{r['steps']},{r['converge_type']}")

print("\n=== Summary by house ===")
for h in ["House01", "House02", "House03"]:
    ds = [float(r["map_dist"]) for r in rows if r["house"] == h and r["map_dist"] != "N/A"]
    if ds:
        ds.sort()
        md = ds[len(ds)//2]
        print(f"{h}: n={len(ds)} median={md:.3f}m mean={sum(ds)/len(ds):.3f}m min={min(ds):.3f}m max={max(ds):.3f}m")
    else:
        print(f"{h}: no results yet")