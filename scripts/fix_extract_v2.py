import csv, re, glob, os

LOG_DIR = "/tmp/cp_sbd_exp"
CSV_IN = os.path.join(LOG_DIR, "ablation_eprocess.csv")
CSV_OUT = os.path.join(LOG_DIR, "ablation_eprocess_v2.csv")

SOURCES = {
    "House01": (-0.40, -2.90),
    "House02": (0.0, -1.0),
    "House03": (-0.45, 1.9),
}

def extract_final_position(log_path):
    """Extract final UAV position from log file."""
    try:
        with open(log_path, 'r', errors='replace') as f:
            content = f.read()
    except:
        return None, None, None
    
    # Remove ANSI codes
    content = re.sub(r'\x1b\[[0-9;]*m', '', content)
    
    # Find last OPGSL-AI step line - coordinates are 3-tuple (x,y,z)
    pattern = r'OPGSL-AI step=(\d+)\s+\(([+-]?[\d.]+),\s*([+-]?[\d.]+),\s*[+-]?[\d.]+\)'
    steps = re.findall(pattern, content)
    
    if not steps:
        # Try Found the emission source
        found = re.search(r'Found the emission source', content)
        if found:
            return None, None, -1
        return None, None, None
    
    last = steps[-1]
    return float(last[1]), float(last[2]), int(last[0])  # ex, ey, step

def main():
    rows = []
    # Read existing CSV
    with open(CSV_IN, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row['method']
            house = row['house']
            seed = row['seed']
            
            # Try to get distance from CSV first
            dist_str = row.get('dist', '').strip()
            dist = None
            if dist_str:
                try:
                    dist = float(dist_str)
                except:
                    pass
            
            # If no distance, extract from log
            if dist is None:
                log_path = os.path.join(LOG_DIR, f"{method}_{house}_s{seed}.log")
                if os.path.exists(log_path):
                    ex, ey, step = extract_final_position(log_path)
                    if ex is not None and house in SOURCES:
                        sx, sy = SOURCES[house]
                        dist = round(((ex - sx)**2 + (ey - sy)**2)**0.5, 3)
                    elif step == -1:
                        # Found source but no coordinates
                        dist = -1  # Mark as found but no coords
            
            rows.append({
                'method': method,
                'house': house,
                'seed': seed,
                'dist': dist if dist is not None else '',
                'steps': row.get('steps', ''),
                'elapsed': row.get('elapsed', ''),
                'converge_type': row.get('converge_type', ''),
            })
    
    # Write updated CSV
    with open(CSV_OUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['method','house','seed','dist','steps','elapsed','converge_type'])
        writer.writeheader()
        writer.writerows(rows)
    
    # Print summary
    valid = [r for r in rows if r['dist'] and r['dist'] != '' and float(r['dist']) >= 0]
    print(f"Processed {len(rows)} rows, {len(valid)} with valid distance")
    
    # Quick stats
    from collections import defaultdict
    stats = defaultdict(list)
    for r in valid:
        stats[(r['method'], r['house'])].append(float(r['dist']))
    
    print(f"\n{'Method':<15} {'House01':>15} {'House02':>15} {'House03':>15}")
    print("-" * 65)
    methods = sorted(set(r['method'] for r in valid))
    for m in methods:
        vals = []
        for h in ['House01', 'House02', 'House03']:
            d = stats.get((m, h), [])
            if d:
                import numpy as np
                vals.append(f"{np.mean(d):.2f}±{np.std(d, ddof=1) if len(d)>1 else 0:.2f}(n={len(d)})")
            else:
                vals.append("—")
        print(f"{m:<15} {vals[0]:>15} {vals[1]:>15} {vals[2]:>15}")

if __name__ == "__main__":
    main()