#!/usr/bin/env python3
import subprocess, os, re

OUT = "/tmp/v2_exp"
os.makedirs(OUT, exist_ok=True)
SRC_X, SRC_Y = -0.60, 1.95

results = []
for seed in range(10):
    print(f"=== Seed {seed} ===", flush=True)
    log_path = os.path.join(OUT, f"v2_s{seed}.log")
    cmd = (
        "source /opt/ros/humble/setup.bash && "
        "source /home/zyc/gsl_ws/install/setup.bash && "
        "timeout 360 ros2 launch vgr_bridge vgr_ablation.launch.py "
        f"seed:={seed} timeout_sec:=300 config_id:=2,4-1_fast "
        "opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false "
        "opgsl.event_driven.enabled:=true"
    )
    with open(log_path, "w") as f:
        proc = subprocess.run(["bash", "-c", cmd], stdout=f, stderr=subprocess.STDOUT, timeout=400)
    with open(log_path) as f:
        content = f.read()
    fe = re.search(r"FAST EXIT:.*?map_dist=([\d.]+).*?step=(\d+)", content)
    res = re.search(r"OPGSL-SDNBV RESULT:.*?MAP=\(([-\d.]+),([-\d.]+),([-\d.]+)\).*?steps=(\d+).*?hits=(\d+)", content)
    if fe:
        err = float(fe.group(1))
        steps = int(fe.group(2))
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, f"{err:.3f}", 1, steps, "fast_exit"))
        print(f"  FAST EXIT: error={err:.3f}m steps={steps}")
    elif res:
        mx, my = float(res.group(1)), float(res.group(2))
        steps = int(res.group(4))
        err = ((mx - SRC_X)**2 + (my - SRC_Y)**2)**0.5
        loc = 1 if err < 2.0 else 0
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, f"{err:.3f}", loc, steps, "timeout"))
        print(f"  MAP=({mx:.2f},{my:.2f}) error={err:.3f}m steps={steps}")
    else:
        results.append(("ED_Bayes_V2", "2,4-1_fast", seed, "99.0", 0, 0, "failed"))
        print(f"  FAILED")

csv_path = os.path.join(OUT, "results.csv")
with open(csv_path, "w") as f:
    f.write("method,scenario,seed,final_error,localized,steps,type\n")
    for r in results:
        f.write(",".join(str(x) for x in r) + "\n")

errors = [float(r[3]) for r in results if float(r[3]) < 50]
localized = [r for r in results if r[4] == 1]
print(f"\n=== SUMMARY ===")
print(f"Total: {len(results)}, Localized: {len(localized)}/{len(results)}, Mean error: {sum(errors)/max(len(errors),1):.3f}m")