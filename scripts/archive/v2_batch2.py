#!/usr/bin/env python3
import subprocess, os, re, signal, time

OUT = "/tmp/v2_exp"
os.makedirs(OUT, exist_ok=True)
SRC_X, SRC_Y = -0.60, 1.95

def kill_ros():
    for name in ["gsl_actionserver_node", "vgr_sim_node", "gsl_benchmark_runner"]:
        try:
            subprocess.run(["pkill", "-9", "-f", name], capture_output=True, timeout=5)
        except:
            pass
    time.sleep(2)

csv_path = os.path.join(OUT, "results_v2.csv")
results = []

for seed in range(10):
    print(f"=== Seed {seed} ===", flush=True)
    kill_ros()
    log_path = os.path.join(OUT, f"v2_s{seed}.log")
    cmd = (
        "source /opt/ros/humble/setup.bash && "
        "source /home/zyc/gsl_ws/install/setup.bash && "
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        f"seed:={seed} timeout_sec:=300 config_id:=2,4-1_fast "
        "opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false "
        "opgsl.event_driven.enabled:=true"
    )
    try:
        with open(log_path, "w") as f:
            proc = subprocess.Popen(["bash", "-c", cmd], stdout=f, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
            try:
                proc.wait(timeout=400)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                time.sleep(3)
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception as e:
        print(f"  Error: {e}")
    kill_ros()
    with open(log_path) as f:
        content = f.read()
    fe = re.search(r"FAST EXIT:.*?map_dist=([\d.]+).*?step=(\d+)", content)
    res = re.search(r"OPGSL-SDNBV RESULT:.*?MAP=\(([-\d.]+),([-\d.]+),([-\d.]+)\).*?steps=(\d+).*?hits=(\d+)", content)
    if fe:
        err = float(fe.group(1))
        steps = int(fe.group(2))
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, f"{err:.3f}", 1, steps, "fast_exit"))
        print(f"  FAST EXIT: error={err:.3f}m steps={steps}", flush=True)
    elif res:
        mx, my = float(res.group(1)), float(res.group(2))
        steps = int(res.group(4))
        err = ((mx - SRC_X)**2 + (my - SRC_Y)**2)**0.5
        loc = 1 if err < 2.0 else 0
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, f"{err:.3f}", loc, steps, "timeout"))
        print(f"  TIMEOUT: MAP=({mx:.2f},{my:.2f}) error={err:.3f}m steps={steps}", flush=True)
    else:
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, "99.0", 0, 0, "failed"))
        print(f"  FAILED", flush=True)
    with open(csv_path, "w") as f:
        f.write("method,scenario,seed,final_error,localized,steps,type\n")
        for r in results:
            f.write(",".join(str(x) for x in r) + "\n")

errors = [float(r[3]) for r in results if float(r[3]) < 50]
localized = [r for r in results if r[4] == 1]
print(f"\n=== SUMMARY ===")
print(f"Total: {len(results)}, Localized: {len(localized)}/{len(results)}, Mean error: {sum(errors)/max(len(errors),1):.3f}m")