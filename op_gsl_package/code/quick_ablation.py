# Quick ablation script - 3 configs x 1 seed x House01
# Tests: A0 (no altitude), A1 (GP only), A5 (full)
import subprocess, time, os, csv

VM = "zyc@192.168.111.128"
HOUSE = "/home/zyc/vgr_data_scenarios/House01"
BASE = "source /opt/ros/humble/setup.bash && source /home/zyc/gsl_ws/install/setup.bash"

configs = [
    ("A0_no_alt",  {"opgsl_alt_gp": "false", "opgsl_alt_levy": "false", "opgsl_alt_layer_scan": "false", "opgsl_alt_decay": "false"}),
    ("A1_gp_only", {"opgsl_alt_gp": "true",  "opgsl_alt_levy": "false", "opgsl_alt_layer_scan": "false", "opgsl_alt_decay": "false"}),
    ("A5_full",    {"opgsl_alt_gp": "true",  "opgsl_alt_levy": "false", "opgsl_alt_layer_scan": "true",  "opgsl_alt_decay": "true"}),
]

results = []
for cfg_name, params in configs:
    for seed in [0]:
        run_dir = f"/tmp/ablation_test/{cfg_name}_s{seed}"
        result_csv = f"{run_dir}/result.csv"
        
        # Kill old processes
        subprocess.run(f'ssh {VM} "pkill -9 -f ros2 2>/dev/null; pkill -9 -f gsl 2>/dev/null; pkill -9 -f vgr 2>/dev/null"', shell=True, capture_output=True)
        time.sleep(2)
        
        # Setup run dir
        subprocess.run(f'ssh {VM} "rm -rf {run_dir} && mkdir -p {run_dir}"', shell=True, capture_output=True)
        
        # Build launch command
        param_str = " ".join(f"{k}:={v}" for k, v in params.items())
        cmd = f'ssh {VM} "{BASE} && timeout 120 ros2 launch vgr_bridge vgr_opgsl3d_ablation.launch.py vgr_data_path:={HOUSE} algorithm:=OPGSL {param_str} seed:={seed} start_x:=-0.9 start_y:=0.15 flight_height:=0.3 timeout_sec:=120 resultsFile:={result_csv} run_dir:={run_dir} 2>&1"'
        
        print(f"\n{'='*60}")
        print(f"Running: {cfg_name} seed={seed}")
        print(f"{'='*60}")
        
        t0 = time.time()
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=150)
        elapsed = time.time() - t0
        
        # Extract key info from output
        output = proc.stdout + proc.stderr
        lines = output.split("\n")
        
        # Find final position and result
        final_info = ""
        for line in lines:
            if "OPGSL-3D RESULT" in line or "search complete" in line:
                final_info = line.strip()
            if "CONVERGED" in line:
                final_info = line.strip()
        
        # Find last OPGSL step
        last_step = ""
        for line in reversed(lines):
            if "OPGSL step=" in line:
                last_step = line.strip()
                break
        
        # Find last altitude info
        last_alt = ""
        for line in reversed(lines):
            if "OPGSL-3D: phase=" in line:
                last_alt = line.strip()
                break
        
        results.append({
            "config": cfg_name,
            "seed": seed,
            "elapsed": f"{elapsed:.1f}s",
            "final_info": final_info,
            "last_step": last_step[:120] if last_step else "N/A",
            "last_alt": last_alt[:120] if last_alt else "N/A",
        })
        
        print(f"  Elapsed: {elapsed:.1f}s")
        print(f"  Last step: {last_step[:120] if last_step else 'N/A'}")
        print(f"  Last alt: {last_alt[:120] if last_alt else 'N/A'}")
        print(f"  Result: {final_info[:120] if final_info else 'N/A'}")

print("\n\n" + "="*80)
print("ABLATION SUMMARY")
print("="*80)
for r in results:
    print(f"\n{r['config']} (seed={r['seed']}):")
    print(f"  Time: {r['elapsed']}")
    print(f"  Last: {r['last_step']}")
    print(f"  Alt:  {r['last_alt']}")
