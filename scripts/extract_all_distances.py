#!/usr/bin/env python3
"""Extract final distance from all log files in /tmp/cp_sbd_exp/"""
import os, re, glob, csv, sys

LOG_DIR = "/tmp/cp_sbd_exp"
OUT_CSV = "/tmp/cp_sbd_exp/all_distances_v2.csv"

# Source positions per house
SOURCES = {
    "House01": (-0.40, -2.90),
    "House02": (0.0, -1.0),
    "House03": (-0.45, 1.9),
}

# Method -> (ddm, wraig, cp) config
METHODS = {
    "Full": (True, True, True),
    "NoDDM": (False, True, True),
    "NoWRAIG": (True, False, True),
    "Baseline": (False, False, False),
    "NoCP": (True, True, False),
    "CPonly": (False, False, True),
    "DDMonLy": (True, False, False),
    "WRAIGonly": (True, False, False),  # same as DDMonLy?
}

# Baseline methods
BASELINES = ["SensorAwareSurgeCastPF", "PMFS", "GrGSL"]

def extract_from_log(log_path):
    """Extract final step info from a log file."""
    try:
        with open(log_path, 'r', errors='replace') as f:
            content = f.read()
    except:
        return None
    
    # Remove ANSI codes
    content = re.sub(r'\x1b\[[0-9;]*m', '', content)
    
    # Find all OPGSL-AI step lines
    step_pattern = r'OPGSL-AI step=(\d+)\s+\(([+-]?[\d.]+),\s*([+-]?[\d.]+),?\s*[+-]?[\d.]*\)'
    steps = re.findall(step_pattern, content)
    
    if not steps:
        # Try baseline format: "Found the emission source!" with coordinates
        found_pattern = r'Found the emission source.*?(\-?[\d.]+).*?(\-?[\d.]+)'
        found = re.search(found_pattern, content, re.DOTALL)
        if found:
            return {"ex": float(found.group(1)), "ey": float(found.group(2)), "steps": -1, "converge": "found"}
        return None
    
    last = steps[-1]
    return {
        "steps": int(last[0]),
        "ex": float(last[1]),
        "ey": float(last[2]),
        "converge": "found" if "Found the emission source" in content else "other"
    }

def parse_filename(fname):
    """Parse method, house, seed from filename like Full_House01_s0.log"""
    m = re.match(r'(.+?)_(House\d+)_s(\d+)\.log', fname)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    return None, None, None

def main():
    rows = []
    logs = glob.glob(os.path.join(LOG_DIR, "*.log"))
    
    for log_path in sorted(logs):
        fname = os.path.basename(log_path)
        if fname.startswith("batch") or fname.startswith("watcher") or fname.startswith("test"):
            continue
        
        method, house, seed = parse_filename(fname)
        if not method or not house:
            continue
        
        info = extract_from_log(log_path)
        if not info:
            continue
        
        sx, sy = SOURCES.get(house, (0, 0))
        dist = ((info["ex"] - sx)**2 + (info["ey"] - sy)**2)**0.5
        
        # Determine method type
        is_baseline = method in BASELINES
        
        rows.append({
            "method": method,
            "house": house,
            "seed": seed,
            "distance": round(dist, 3),
            "steps": info["steps"],
            "converge": info["converge"],
            "is_baseline": is_baseline,
            "log_file": fname,
        })
    
    # Write CSV
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=["method","house","seed","distance","steps","converge","is_baseline","log_file"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["method"], r["house"], r["seed"])))
    
    print(f"Extracted {len(rows)} runs -> {OUT_CSV}")
    
    # Summary table
    from collections import defaultdict
    summary = defaultdict(list)
    for r in rows:
        summary[(r["method"], r["house"])].append(r["distance"])
    
    print("\n=== Summary (mean ± std, n) ===")
    print(f"{'Method':<25} {'House01':>20} {'House02':>20} {'House03':>20}")
    print("-" * 90)
    methods = sorted(set(r["method"] for r in rows))
    for m in methods:
        vals = []
        for h in ["House01", "House02", "House03"]:
            d = summary.get((m, h), [])
            if d:
                import statistics
                mean = statistics.mean(d)
                std = statistics.stdev(d) if len(d) > 1 else 0
                vals.append(f"{mean:.2f}±{std:.2f} (n={len(d)})")
            else:
                vals.append("—")
        print(f"{m:<25} {vals[0]:>20} {vals[1]:>20} {vals[2]:>20}")

if __name__ == "__main__":
    main()