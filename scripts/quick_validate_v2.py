#!/usr/bin/env python3
import subprocess, time, csv, os, re, signal

HOUSES = [
    {"name":"House01","path":"/home/zyc/vgr_data_scenarios/House01","sx":-0.40,"sy":-2.90,"sz":-0.30},
    {"name":"House02","path":"/home/zyc/vgr_data_scenarios/House02","sx":0.0,"sy":-1.0,"sz":0.2},
    {"name":"House03","path":"/home/zyc/vgr_data_scenarios/House03","sx":-0.45,"sy":1.9,"sz":-0.1},
]
SEEDS = [0, 1, 2]
TIMEOUT = 300

def kill_all():
    subprocess.run("pkill -9 -f gsl_actionserver; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(2)

def run_one(house, seed):
    label = house["name"] + "_s" + str(seed)
    log_file = "/tmp/cp_sbd_quick/" + label + ".log"
    kill_all()
    subprocess.run("rm -f /tmp/gsl_result.csv", shell=True)

    cmd = (
        "cd /home/zyc/gsl_ws; source install/setup.bash; "
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        "vgr_data_path:=" + house["path"] + " "
        "config_id:=2,4-1_fast algorithm:=OPGSL "
        "source_x:=" + str(house["sx"]) + " source_y:=" + str(house["sy"]) + " source_z:=" + str(house["sz"]) + " "
        "start_x:=-0.9 start_y:=0.15 seed:=" + str(seed) + " "
        "timeout_sec:=" + str(TIMEOUT) + " use_sbd:=true resultsFile:=/tmp/gsl_result.csv"
    )

    proc = subprocess.Popen(["bash", "-c", cmd], stdout=open(log_file, "w"), stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    result = {"house": house["name"], "seed": seed, "map_dist": "N/A", "steps": "N/A", "elapsed": "0", "converge_type": "N/A"}

    # Wait for result or timeout
    while time.time() - t0 < TIMEOUT + 60:
        time.sleep(5)
        # Check CSV result
        if os.path.exists("/tmp/gsl_result.csv"):
            try:
                with open("/tmp/gsl_result.csv") as f:
                    c = f.read().strip()
                    if c and len(c.split("\n")) > 1:
                        for row in csv.DictReader(open("/tmp/gsl_result.csv")):
                            for k in ["map_dist", "search_d", "final_distance", "distance_to_source"]:
                                if k in row and row[k]:
                                    result["map_dist"] = row[k]
                                    break
                            if "steps" in row: result["steps"] = row["steps"]
                        result["converge_type"] = "csv_result"
                        break
            except:
                pass

        # Also check log for convergence
        try:
            with open(log_file) as f:
                content = f.read()
                if "Found the emission source" in content:
                    # Extract final distance from log
                    for line in content.split("\n"):
                        # Look for distance info
                        m = re.search(r"distance[=:]\s*([0-9.]+)", line, re.I)
                        if m:
                            result["map_dist"] = m.group(1)
                        m = re.search(r"estimate=\(([0-9.-]+),\s*([0-9.-]+)", line)
                        if m:
                            est_x, est_y = float(m.group(1)), float(m.group(2))
                            sx, sy = house["sx"], house["sy"]
                            dist = ((est_x - sx)**2 + (est_y - sy)**2)**0.5
                            result["map_dist"] = "%.3f" % dist
                            result["converge_type"] = "log_estimate"
                    # Count steps
                    step_matches = re.findall(r"OPGSL-AI step=(\d+)", content)
                    if step_matches:
                        result["steps"] = step_matches[-1]
                    # Check timeout
                    if "timeout" in content.lower() or time.time() - t0 > TIMEOUT:
                        result["converge_type"] = "timeout"
                    break
                if time.time() - t0 > TIMEOUT + 30:
                    result["converge_type"] = "timeout"
                    break
        except:
            pass

        if proc.poll() is not None:
            time.sleep(5)
            # Final check
            try:
                with open(log_file) as f:
                    content = f.read()
                    for line in content.split("\n"):
                        m = re.search(r"estimate=\(([0-9.-]+),\s*([0-9.-]+)", line)
                        if m:
                            est_x, est_y = float(m.group(1)), float(m.group(2))
                            sx, sy = house["sx"], house["sy"]
                            dist = ((est_x - sx)**2 + (est_y - sy)**2)**0.5
                            result["map_dist"] = "%.3f" % dist
                    step_matches = re.findall(r"OPGSL-AI step=(\d+)", content)
                    if step_matches:
                        result["steps"] = step_matches[-1]
            except:
                pass
            break

    result["elapsed"] = "%.1f" % (time.time() - t0)
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

with open("/tmp/cp_sbd_quick/summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["house", "seed", "map_dist", "steps", "elapsed", "converge_type"])
    w.writeheader()
    w.writerows(results)

print("\n=== Summary ===")
for hn in ["House01", "House02", "House03"]:
    ds = [float(r["map_dist"]) for r in results if r["house"] == hn and r["map_dist"] != "N/A"]
    if ds:
        print("%s: n=%d median=%.2fm mean=%.2fm" % (hn, len(ds), sorted(ds)[len(ds)//2], sum(ds)/len(ds)))
    else:
        print("%s: no valid results" % hn)
