#!/usr/bin/env python3
"""Single-run launcher: launch, wait for completion, extract result, kill."""
import subprocess, time, os, re, sys, signal

def run_single(house_name, house_path, sx, sy, sz, seed, timeout=300):
    label = house_name + "_s" + str(seed)
    log_file = "/tmp/cp_sbd_quick/" + label + ".log"
    
    # Kill everything first
    subprocess.run("pkill -9 -f ros2", shell=True, stderr=subprocess.DEVNULL)
    subprocess.run("pkill -9 -f gsl_action", shell=True, stderr=subprocess.DEVNULL)
    subprocess.run("pkill -9 -f vgr_sim", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(4)
    
    cmd = (
        "cd /home/zyc/gsl_ws; source install/setup.bash; "
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        "vgr_data_path:=" + house_path + " "
        "config_id:=2,4-1_fast algorithm:=OPGSL "
        "source_x:=" + str(sx) + " source_y:=" + str(sy) + " source_z:=" + str(sz) + " "
        "start_x:=-0.9 start_y:=0.15 seed:=" + str(seed) + " "
        "timeout_sec:=" + str(timeout) + " use_sbd:=true resultsFile:=/tmp/gsl_result.csv"
    )
    
    lf = open(log_file, "w")
    proc = subprocess.Popen(["bash", "-c", cmd], stdout=lf, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    
    # Wait for process to finish
    while time.time() - t0 < timeout + 60:
        time.sleep(10)
        if proc.poll() is not None:
            break
    lf.close()
    
    elapsed = time.time() - t0
    
    # Parse log
    result = {"house": house_name, "seed": seed, "map_dist": "N/A", "steps": "N/A", "elapsed": "%.1f" % elapsed, "converge_type": "N/A"}
    
    try:
        with open(log_file) as f:
            content = f.read()
    except:
        return result
    
    # Extract final position
    step_lines = re.findall(r"OPGSL-AI step=(\d+) \(([-0-9.]+),([-0-9.]+),([-0-9.]+)\)", content)
    if step_lines:
        last = step_lines[-1]
        result["steps"] = last[0]
        ex, ey = float(last[1]), float(last[2])
        dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
        result["map_dist"] = "%.3f" % dist
    
    if "Found the emission source" in content:
        result["converge_type"] = "found"
    elif "DONE, CLOSING" in content:
        result["converge_type"] = "closed"
    elif elapsed > timeout:
        result["converge_type"] = "timeout"
    else:
        result["converge_type"] = "died"
    
    # Kill
    subprocess.run("pkill -9 -f ros2", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    return result

if __name__ == "__main__":
    house_name = sys.argv[1]
    seed = int(sys.argv[2])
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    
    houses = {
        "House01": ("/home/zyc/vgr_data_scenarios/House01", -0.40, -2.90, -0.30),
        "House02": ("/home/zyc/vgr_data_scenarios/House02", 0.0, -1.0, 0.2),
        "House03": ("/home/zyc/vgr_data_scenarios/House03", -0.45, 1.9, -0.1),
    }
    
    path, sx, sy, sz = houses[house_name]
    os.makedirs("/tmp/cp_sbd_quick", exist_ok=True)
    r = run_single(house_name, path, sx, sy, sz, seed, timeout)
    print("%s,%s,%s,%s,%s,%s" % (r["house"], r["seed"], r["map_dist"], r["steps"], r["elapsed"], r["converge_type"]))
