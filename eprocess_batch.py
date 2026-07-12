import re, math, csv, os, subprocess, sys, time, datetime

LOG_DIR = "/tmp/cp_sbd_exp/eprocess"
RESULTS_CSV = os.path.join(LOG_DIR, "results.csv")

SOURCES = {
    "House01": (-0.40, -2.90),
    "House02": (0.00, -1.00),
    "House03": (-0.45, 1.90),
}

def extract(log_file, sx, sy):
    try:
        with open(log_file, "r", errors="replace") as f:
            c = f.read()
    except FileNotFoundError:
        return None, 0, "missing"
    c = re.sub(r"\x1b\[[0-9;]*m", "", c)
    ctype = "other"
    if "MAXSTEPS-STOP" in c: ctype = "maxsteps"
    elif "EP-STOP" in c: ctype = "ep_stop"
    elif "CP-STOP" in c: ctype = "cp_stop"
    elif "Found the emission source" in c: ctype = "found"
    elif "TIMEOUT" in c: ctype = "timeout"
    elif "Could not find" in c: ctype = "not_found"
    dist = None; steps = 0
    m = re.search(r"MAXSTEPS-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)", c)
    if m:
        steps = int(m.group(1)); mx, my = float(m.group(2)), float(m.group(3))
        dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
    if dist is None:
        m = re.search(r"EP-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)", c)
        if m:
            steps = int(m.group(1)); mx, my = float(m.group(2)), float(m.group(3))
            dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
    if dist is None:
        m = re.search(r"final_error=([\d.]+)", c)
        if m: dist = float(m.group(1))
    if steps == 0:
        sm = re.findall(r"step=(\d+)", c)
        if sm: steps = int(sm[-1])
    return dist, steps, ctype

def run_one(label, house, cfg, sx, sy, sz, stx, sty, seed, maxsteps):
    tag = f"{label},{house},{seed},{maxsteps}"
    if os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV) as f:
            if tag in f.read():
                print(f"  [SKIP] {tag}"); return True
    log_file = os.path.join(LOG_DIR, f"{label}_{house}_s{seed}_st{maxsteps}.log")
    cmd = ["timeout","300","ros2","launch","vgr_bridge","vgr_ablation.launch.py",
        f"vgr_data_path:=/home/zyc/vgr_data_scenarios/{house}",
        f"config_id:={cfg}","algorithm:=OPGSL","method:=M7_full_saisc_pf",
        f"source_x:={sx}",f"source_y:={sy}",f"source_z:={sz}",
        f"start_x:={stx}",f"start_y:={sty}",f"seed:={seed}",
        "timeout_sec:=240","use_sbd:=true",
        "opgsl_ddm:=true","opgsl_wraig:=true","opgsl_cp:=true",
        "opgsl.event_driven.enabled:=true","opgsl.event_driven.eta_fixed:=-1.0",
        f"opgsl_max_steps:={maxsteps}"]
    t0 = time.time()
    subprocess.run(["killall","-9","gsl_actionserver_node","vgr_sim_node","gsl_benchmark_runner"],capture_output=True)
    time.sleep(2)
    with open(log_file,"w") as lf:
        subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, timeout=320)
    elapsed = int(time.time()-t0)
    src = SOURCES.get(house,(sx,sy))
    d, s, ct = extract(log_file, src[0], src[1])
    if d is None: d = float("nan")
    with open(RESULTS_CSV,"a") as f:
        f.write(f"{label},{house},{seed},{maxsteps},{d:.3f},{s},{elapsed},{ct}\n")
    print(f"  -> dist={d:.3f} steps={s} type={ct} time={elapsed}s")
    subprocess.run(["killall","-9","gsl_actionserver_node","vgr_sim_node","gsl_benchmark_runner"],capture_output=True)
    time.sleep(2)
    return True

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV,"w") as f: f.write("method,house,seed,max_steps,dist,steps,elapsed,converge_type\n")
    houses=["House01","House02","House03"]
    configs=["2,4-1_fast","3,5-1_fast","1-2,5_fast"]
    sx=[-0.40,0.00,-0.45]; sy=[-2.90,-1.00,1.90]; sz=[-0.30,0.20,-0.10]
    stx=[0.30,-0.50,2.00]; sty=[-1.20,-2.50,0.00]
    print("=== E-process Experiment (fixed extraction) ===")
    print(datetime.datetime.now())
    for ms in [10,20,30,50,100]:
        for hi in range(3):
            for seed in range(5):
                print(f"[{houses[hi]}] steps={ms} seed={seed}")
                run_one("FixedSteps",houses[hi],configs[hi],sx[hi],sy[hi],sz[hi],stx[hi],sty[hi],seed,ms)
    print("=== COMPLETE ===")
    print(datetime.datetime.now())
    with open(RESULTS_CSV) as f: print(f.read())

if __name__=="__main__": main()
