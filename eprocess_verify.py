import re, math

def extract_result(log_file, source_x, source_y):
    try:
        with open(log_file, "r", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        return None, None, "missing"
    content = re.sub(r"\x1b\[[0-9;]*m", "", content)
    ctype = "other"
    if "Found the emission source" in content: ctype = "found"
    elif "EP-STOP" in content: ctype = "ep_stop"
    elif "MAXSTEPS-STOP" in content: ctype = "maxsteps"
    elif "CP-STOP" in content: ctype = "cp_stop"
    elif "TIMEOUT" in content: ctype = "timeout"
    elif "Could not find" in content: ctype = "not_found"
    dist = None; steps = None
    m = re.search(r"OPGSL-SDNBV RESULT:.*?posterior_MAP=\(([-\d.]+),([-\d.]+)\).*?steps=(\d+)", content)
    if m:
        mx, my = float(m.group(1)), float(m.group(2))
        steps = int(m.group(3))
        dist = math.sqrt((mx - source_x)**2 + (my - source_y)**2)
    if dist is None:
        m2 = re.search(r"final_error=([\d.]+)", content)
        if m2: dist = float(m2.group(1))
    if dist is None:
        m3 = re.search(r"MAXSTEPS-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)", content)
        if m3:
            steps = int(m3.group(1))
            mx, my = float(m3.group(2)), float(m3.group(3))
            dist = math.sqrt((mx - source_x)**2 + (my - source_y)**2)
    if steps is None:
        sm = re.findall(r"step=(\d+)", content)
        steps = int(sm[-1]) if sm else 0
    return dist, steps, ctype

for seed in range(5):
    log = f"/tmp/cp_sbd_exp/eprocess/FixedSteps_House01_s{seed}_st10.log"
    d, s, c = extract_result(log, -0.40, -2.90)
    print(f"seed={seed}: dist={d} steps={s} type={c}")
