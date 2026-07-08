#!/usr/bin/env python3
"""Sync experiment data from VM and organize locally.
Usage: python sync_data.py
"""
import subprocess, csv, os, sys, shutil

VM = "zyc@192.168.111.128"
VM_RESULTS = "/tmp/v8_exp/isj_full/results.csv"
VM_LOGS = "/tmp/v8_exp/isj_full/"
LOCAL_BASE = os.path.dirname(os.path.abspath(__file__))
LOCAL_RAW = os.path.join(LOCAL_BASE, "results_raw.csv")

def sync():
    print("Syncing results CSV from VM...")
    r = subprocess.run(["scp", f"{VM}:{VM_RESULTS}", LOCAL_RAW], capture_output=True)
    if r.returncode != 0:
        print(f"SCP failed: {r.stderr.decode()}")
        return False
    
    # Read results
    rows = []
    with open(LOCAL_RAW) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    
    print(f"Downloaded {len(rows)} results")
    
    # Organize by scenario/method
    for row in rows:
        sc = row['scenario']
        m = row['method']
        d = os.path.join(LOCAL_BASE, sc, m)
        os.makedirs(d, exist_ok=True)
    
    # Per-scenario CSVs
    scenarios = {}
    for row in rows:
        sc = row['scenario']
        if sc not in scenarios:
            scenarios[sc] = []
        scenarios[sc].append(row)
    
    for sc, sc_rows in scenarios.items():
        with open(os.path.join(LOCAL_BASE, sc, f'{sc}_all.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['method', 'seed', 'error_m', 'localized', 'elapsed_s'])
            for r in sc_rows:
                w.writerow([r['method'], r['seed'], r['error_m'], r['localized'], r['elapsed_s']])
        
        methods = {}
        for r in sc_rows:
            m = r['method']
            if m not in methods:
                methods[m] = []
            methods[m].append(r)
        
        for m, m_rows in methods.items():
            d = os.path.join(LOCAL_BASE, sc, m)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f'{m}_{sc}.csv'), 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['seed', 'error_m', 'localized', 'elapsed_s'])
                for r in m_rows:
                    w.writerow([r['seed'], r['error_m'], r['localized'], r['elapsed_s']])
    
    # Summary stats
    with open(os.path.join(LOCAL_BASE, 'summary_stats.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['scenario', 'method', 'n', 'mean_m', 'std_m', 'success_rate', 'best_m', 'worst_m'])
        for sc, sc_rows in scenarios.items():
            methods = {}
            for r in sc_rows:
                m = r['method']
                if m not in methods:
                    methods[m] = []
                if r['error_m'] != 'NA':
                    methods[m].append(float(r['error_m']))
            for m, vals in methods.items():
                if not vals:
                    continue
                n = len(vals)
                mean_v = sum(vals)/n
                std_v = (sum((x-mean_v)**2 for x in vals)/n)**0.5 if n > 1 else 0
                sr = sum(1 for x in vals if x < 2.0)/n
                w.writerow([sc, m, n, f'{mean_v:.3f}', f'{std_v:.3f}', f'{sr:.0%}', f'{min(vals):.3f}', f'{max(vals):.3f}'])
    
    print("Data organized and summary_stats.csv updated")
    return True

if __name__ == "__main__":
    sync()
