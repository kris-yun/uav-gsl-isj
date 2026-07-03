#!/usr/bin/env python3
"""Robust validation v4: direct node launch, parse results from log."""
import subprocess, time, os, re, signal, sys

HOUSES = [
    {"name":"House01","path":"/home/zyc/vgr_data_scenarios/House01","sx":-0.40,"sy":-2.90,"sz":-0.30},
    {"name":"House02","path":"/home/zyc/vgr_data_scenarios/House02","sx":0.0,"sy":-1.0,"sz":0.2},
    {"name":"House03","path":"/home/zyc/vgr_data_scenarios/House03","sx":-0.45,"sy":1.9,"sz":-0.1},
]
SEEDS = [0, 1, 2]
TIMEOUT = 300

def kill_all():
    subprocess.run("pkill -9 -f gsl_actionserver; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark; pkill -9 -f ros2", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(3)

def run_one(house, seed):
    label = house["name"] + "_s" + str(seed)
    log_file = "/tmp/cp_sbd_quick/" + label + ".log"
    kill_all()

    cmd = (
        "cd /home/zyc/gsl_ws; source install/setup.bash; "
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        "vgr_data_path:=" + house["path"] + " "
        "config_id:=2,4-1_fast algorithm:=OPGSL "
        "source_x:=" + str(house["sx"]) + " source_y:=" + str(house["sy"]) + " source_z:=" + str(house["sz"]) + " "
        "start_x:=-0.9 start_y:=0.15 seed:=" + str(seed) + " "
        "timeout_sec:=" + str(TIMEOUT) + " use_sbd:=true resultsFile:=/tmp/gsl_result.csv"
    )

    lf = open(log_file, "w")
    proc = subprocess.Popen(["bash", "-c", cmd], stdout=lf, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    result = {"house": house["name"], "seed": seed, "map_dist": "N/A", "steps": "N/A", "elapsed": "0", "converge_type": "N/A"}

    while time.time() - t0 < TIMEOUT + 30:
        time.sleep(5)
        if proc.poll() is not None:
            break

    # Process ended - parse log
    lf.close()
    elapsed = time.time() - t0
    result["elapsed"] = "%.1f" % elapsed

    try:
        with open(log_file) as f:
            content = f.read()
    except:
        result["converge_type"] = "read_error"
        kill_all()
        return result

    # Extract final position from OPGSL-AI step lines
    step_lines = re.findall(r"OPGSL-AI step=(\d+) \(([-0-9.]+),([-0-9.]+),([-0-9.]+)\)", content)
    if step_lines:
        last = step_lines[-1]
        result["steps"] = last[0]
        ex, ey = float(last[1]), float(last[2])
        dist = ((ex - house["sx"])**2 + (ey - house["sy"])**2)**0.5
        result["map_dist"] = "%.3f" % dist

    # Check if source was found
    if "Found the emission source" in content:
        result["converge_type"] = "found"
    elif "DONE, CLOSING" in content:
        result["converge_type"] = "closed"
    elif elapsed > TIMEOUT:
        result["converge_type"] = "timeout"
    else:
        result["converge_type"] = "process_died"

    # Also try CSV
    if os.path.exists("/tmp/gsl_result.csv"):
        try:
            import csv
            with open("/tmp/gsl_result.csv") as f:
                for row in csv.DictReader(f):
                    for k in ["map_dist", "search_d", "final_distance", "distance_to_source"]:
                        if k in row and row[k]:
                            result["map_dist"] = row[k]
                            result["converge_type"] = "csv_result"
                            break
        except:
            pass

    kill_all()
    return result

os.makedirs("/tmp/cp_sbd_quick", exist_ok=True)
results = []
print("house,seed,map_dist,steps,elapsed,converge_type", flush=True)

for house in HOUSES:
    for seed in SEEDS:
        r = run_one(house, seed)
        results.append(r)
        print("%s,%s,%s,%s,%s,%s" % (r["house"], r["seed"], r["map_dist"], r["steps"], r["elapsed"], r["converge_type"]), flush=True)
        sys.stdout.flush()

# Write summary
with open("/tmp/cp_sbd_quick/summary.csv", "w") as f:
    f.write("house,seed,map_dist,steps,elapsed,converge_type\n")
    for r in results:
        f.write("%s,%s,%s,%s,%s,%s\n" % (r["house"], r["seed"], r["map_dist"], r["steps"], r["elapsed"], r["converge_type"]))

print("\n=== Summary ===")
for hn in ["House01", "House02", "House03"]:
    ds = [float(r["map_dist"]) for r in results if r["house"] == hn and r["map_dist"] != "N/A"]
    if ds:
        print("%s: n=%d median=%.2fm mean=%.2fm" % (hn, len(ds), sorted(ds)[len(ds)//2], sum(ds)/len(ds)))
    else:
        print("%s: no valid results" % hn)
