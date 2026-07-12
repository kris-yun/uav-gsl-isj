import re, math

def extract(log_file, sx, sy):
    with open(log_file, "r", errors="replace") as f:
        c = f.read()
    c = re.sub("\[[0-9;]*m", "", c)
    ctype = "other"
    if "MAXSTEPS-STOP" in c: ctype = "maxsteps"
    elif "EP-STOP" in c: ctype = "ep_stop"
    elif "Found the emission source" in c: ctype = "found"
    dist = None; steps = 0
    m = re.search(r"MAXSTEPS-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)", c)
    if m:
        steps = int(m.group(1)); mx = float(m.group(2)); my = float(m.group(3))
        dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
    if dist is None:
        m = re.search(r"EP-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)", c)
        if m:
            steps = int(m.group(1)); mx = float(m.group(2)); my = float(m.group(3))
            dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
    if dist is None:
        m = re.search(r"final_error=([\d.]+)", c)
        if m: dist = float(m.group(1))
    return dist, steps, ctype

for seed in range(5):
    log = f"/tmp/cp_sbd_exp/eprocess/FixedSteps_House01_s{seed}_st10.log"
    d, s, ct = extract(log, -0.40, -2.90)
    if d is not None:
        print(f"seed={seed}: dist={d:.3f} steps={s} type={ct}")
    else:
        print(f"seed={seed}: dist=None steps={s} type={ct}")
