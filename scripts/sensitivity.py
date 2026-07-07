#!/usr/bin/env python3
"""
Poisson model sensitivity analysis.
Run the GSL algorithm with different Poisson parameters on seed=0 to find optimal settings.
"""
import subprocess, csv, os, glob, time

# Parameter grid
configs = [
    # (lambda0, ell, alpha_w, dt, det_thresh, label)
    (0.10, 4.0, 0.10, 0.3, 0.001, "very_weak"),
    (0.20, 3.5, 0.15, 0.3, 0.001, "weak"),
    (0.30, 3.0, 0.20, 0.5, 0.001, "moderate"),
    (0.50, 2.5, 0.30, 0.5, 0.001, "strong"),
    (1.00, 2.0, 0.50, 1.0, 0.01, "original"),
]

results = []
for lam, ell, aw, dt, thresh, label in configs:
    print("Running: %s (lambda0=%.2f, ell=%.1f, aw=%.2f, dt=%.1f, thresh=%.3f)" % (label, lam, ell, aw, dt, thresh))
    
    # Build command
    cmd = [
        "timeout", "150",
        "ros2", "launch", "vgr_bridge", "vgr_ablation.launch.py",
        "seed:=0", "timeout_sec:=120",
        "opgsl_cp:=false", "opgsl_ddm:=false",
    ]
    
    env = os.environ.copy()
    env["POISSON_LAMBDA0"] = str(lam)
    env["POISSON_ELL"] = str(ell)
    env["POISSON_ALPHA_W"] = str(aw)
    env["POISSON_DT"] = str(dt)
    env["POISSON_DET_THRESH"] = str(thresh)
    
    # Run
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    
    # Get result
    csvs = sorted(glob.glob("/tmp/gsl_runs_v4/results/raw/*_s0_*record.csv"))
    if csvs:
        with open(csvs[-1]) as f:
            r = csv.DictReader(f).__next__()
            err = float(r["final_error_m"])
            md = float(r["min_distance_m"])
            results.append((label, lam, ell, aw, dt, thresh, err, md))
            print("  -> error=%.2fm min_dist=%.2fm" % (err, md))
    else:
        print("  -> NO RESULT")
        results.append((label, lam, ell, aw, dt, thresh, 999, 999))

print("\n=== SENSITIVITY ANALYSIS ===")
print("%-12s %8s %6s %6s %5s %7s %8s %8s" % ("label", "lam0", "ell", "aw", "dt", "thresh", "error", "min_d"))
for r in results:
    print("%-12s %8.2f %6.1f %6.2f %5.1f %7.3f %8.2f %8.2f" % r)