#!/usr/bin/env python3
"""Run clean experiments: PMFS baseline vs WRANF on House01.
Uses restored original MAPIRlab PMFS + WRANF supervisor only.
"""
import subprocess, time, csv, os, json, signal, sys

VGR_DATA = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios"
HOUSE = "House01"
CONFIG = "2,4-1_fast"
SOURCE = (-0.4, -2.9, -0.3)
START = (-5.0, -5.0)
RESULTS_DIR = "/tmp/gsl_clean_results"
SCALE = 25
TIMEOUT = 150  # seconds per run

os.makedirs(RESULTS_DIR, exist_ok=True)

def clean_ros2():
    subprocess.run("pkill -9 -f ros2; pkill -9 -f gsl_; pkill -9 -f vgr_; rm -rf /dev/shm/fastrtps_*; sleep 2", shell=True)

def run_single(method, seed, use_wranf, extra_params=None):
    """Run a single experiment and return results."""
    clean_ros2()
    time.sleep(1)
    
    vgr_path = f"{VGR_DATA}/{HOUSE}"
    out_csv = f"{RESULTS_DIR}/{HOUSE}_{method}_s{seed}.csv"
    srv_csv = f"{RESULTS_DIR}/{HOUSE}_{method}_s{seed}_server.csv"
    
    wranf_str = "True" if use_wranf else "False"
    
    # Build launch command
    cmd = f"""source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
ros2 launch vgr_bridge vgr_gsl_wranf.launch.py \
    vgr_data_path:={vgr_path} \
    config_id:={CONFIG} \
    source_x:={SOURCE[0]} \
    source_y:={SOURCE[1]} \
    source_z:={SOURCE[2]} \
    start_x:={START[0]} \
    start_y:={START[1]} \
    seed:={seed} \
    output_csv:={out_csv} \
    server_results_file:={srv_csv} \
    dataset:=VGR_{HOUSE}"""
    
    # For PMFS baseline, override use_wranf_supervisor
    # The wranf launch has it hardcoded to True, so we use ablation_noWRANF
    if not use_wranf:
        cmd = f"""source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
ros2 launch vgr_bridge vgr_gsl_ablation_noWRANF.launch.py \
    vgr_data_path:={vgr_path} \
    config_id:={CONFIG} \
    source_x:={SOURCE[0]} \
    source_y:={SOURCE[1]} \
    source_z:={SOURCE[2]} \
    start_x:={START[0]} \
    start_y:={START[1]} \
    seed:={seed} \
    output_csv:={out_csv} \
    server_results_file:={srv_csv} \
    dataset:=VGR_{HOUSE}"""
    
    print(f"  Running {method} seed {seed}...")
    proc = subprocess.Popen(cmd, shell=True, executable="/bin/bash",
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)
    
    try:
        stdout, stderr = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        time.sleep(2)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except:
            pass
        print(f"  TIMEOUT after {TIMEOUT}s")
        return None
    
    # Parse result
    if os.path.exists(out_csv):
        with open(out_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                return {
                    "method": method,
                    "seed": seed,
                    "min_distance": float(row.get("min_distance_to_source", 0)),
                    "success_at_1m": int(row.get("success_at_1m", 0)),
                    "success_at_2m": int(row.get("success_at_2m", 0)),
                    "elapsed": float(row.get("elapsed_sec", 0)),
                    "path_length": float(row.get("path_length", 0)),
                }
    return None

# ============================================
# EXPERIMENT 1: PMFS baseline (no WRANF) x 10 seeds
# ============================================
print("=" * 60)
print("EXPERIMENT 1: PMFS Baseline (clean, no WRANF) x 10 seeds")
print("=" * 60)

pmfs_results = []
for seed in range(10):
    r = run_single("PMFS_baseline", seed, use_wranf=False)
    if r:
        pmfs_results.append(r)
        print(f"  seed={seed}: min_dist={r['min_distance']:.3f}m")
    else:
        print(f"  seed={seed}: FAILED")

print(f"\nPMFS Baseline: n={len(pmfs_results)}")
if pmfs_results:
    avg = sum(r['min_distance'] for r in pmfs_results) / len(pmfs_results)
    print(f"  avg min_dist = {avg:.3f}m")

# ============================================
# EXPERIMENT 2: WRANF (FUSED) x 10 seeds  
# ============================================
print("\n" + "=" * 60)
print("EXPERIMENT 2: WRANF (SENPAI+GRACE+ESSA) x 10 seeds")
print("=" * 60)

wranf_results = []
for seed in range(10):
    r = run_single("WRANF", seed, use_wranf=True)
    if r:
        wranf_results.append(r)
        print(f"  seed={seed}: min_dist={r['min_distance']:.3f}m")
    else:
        print(f"  seed={seed}: FAILED")

print(f"\nWRANF: n={len(wranf_results)}")
if wranf_results:
    avg = sum(r['min_distance'] for r in wranf_results) / len(wranf_results)
    print(f"  avg min_dist = {avg:.3f}m")

# Save summary
summary = {"PMFS_baseline": pmfs_results, "WRANF": wranf_results}
with open(f"{RESULTS_DIR}/summary_House01_clean.json", 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nResults saved to {RESULTS_DIR}/summary_House01_clean.json")
