#!/usr/bin/env python3
import subprocess, os, re, time

os.makedirs("/tmp/edbayes_exp", exist_ok=True)
csv_path = "/tmp/edbayes_exp/results.csv"

with open(csv_path, "w") as f:
    f.write("method,seed,final_error,localized2,steps,type\n")

def run_one(method, seed, extra):
    log = f"/tmp/edbayes_exp/{method}_s{seed}.log"
    subprocess.run(["pkill", "-9", "-f", "gsl_actionserver"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "vgr_sim"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "benchmark_runner"], capture_output=True)
    time.sleep(2)
    
    env = os.environ.copy()
    bash_cmd = (
        "source /opt/ros/humble/setup.bash && "
        "source /home/zyc/gsl_ws/install/setup.bash && "
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        "vgr_data_path:=/home/zyc/enva_vgr config_id:=A1_fast "
        "algorithm:=OPGSL method:=M7_full_saisc_pf "
        "source_x:=5.00 source_y:=6.20 source_z:=0.50 "
        "start_x:=4.0 start_y:=4.0 seed:=" + str(seed) + " "
        "timeout_sec:=120 use_sbd:=true "
        "opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false "
        + extra
    )
    
    t0 = time.time()
    with open(log, "w") as lf:
        proc = subprocess.Popen(
            ["bash", "-c", bash_cmd],
            stdout=lf, stderr=subprocess.STDOUT, env=env
        )
    
    for _ in range(36):
        time.sleep(5)
        if proc.poll() is not None:
            break
        try:
            with open(log) as lf:
                if "DONE, CLOSING" in lf.read():
                    time.sleep(3)
                    break
        except:
            pass
    
    try:
        proc.wait(timeout=10)
    except:
        proc.kill()
    
    elapsed = int(time.time() - t0)
    subprocess.run(["pkill", "-9", "-f", "gsl_actionserver"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "vgr_sim"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "benchmark_runner"], capture_output=True)
    
    with open(log) as lf:
        content = lf.read()
    
    fe = ""
    m = re.findall(r"final_error=([0-9.]+)", content)
    if m: fe = m[-1]
    
    l2 = ""
    m = re.findall(r"localized2=([0-9]+)", content)
    if m: l2 = m[-1]
    
    steps = str(content.count("SDNBV"))
    
    ctype = "other"
    if "Found the emission" in content: ctype = "found"
    elif "action_failure" in content: ctype = "timeout"
    
    line = f"{method},{seed},{fe},{l2},{steps},{ctype}"
    print(line, flush=True)
    with open(csv_path, "a") as f:
        f.write(line + "\n")
    time.sleep(2)

print("=== ED-Bayes (event-driven) 10 seeds ===", flush=True)
for s in range(10):
    run_one("ED_Bayes", s, "opgsl.event_driven.enabled:=true")

print("=== Baseline (continuous) 10 seeds ===", flush=True)
for s in range(10):
    run_one("Baseline", s, "opgsl.event_driven.enabled:=false")

print("=== Summary ===", flush=True)
with open(csv_path) as f:
    print(f.read(), flush=True)
