import os, re
log_dir = "/tmp/cp_sbd_exp/eprocess"
results = []
for f in sorted(os.listdir(log_dir)):
    if not f.endswith(".log"):
        continue
    log = open(f"{log_dir}/{f}").read()
    # Extract max_steps from filename
    m = re.search(r"_st(\d+)\.log", f)
    max_steps = int(m.group(1)) if m else -1
    # Extract seed
    m2 = re.search(r"_s(\d+)_", f)
    seed = int(m2.group(1)) if m2 else -1
    # Try OPGSL-SDNBV RESULT first
    rl = re.findall(r"OPGSL-SDNBV RESULT:.*?posterior_MAP=\(([-\d.]+),([-\d.]+)", log)
    if rl:
        mx, my = float(rl[-1][0]), float(rl[-1][1])
        steps_m = re.findall(r"steps=(\d+)", log)
        steps = int(steps_m[-1]) if steps_m else 0
    else:
        # Fallback: final_error
        fe = re.findall(r"final_error=([\d.]+)", log)
        mx, my = None, None
        if fe:
            mx = float(fe[-1])  # This is actually distance, not MX
        steps_m = re.findall(r"MAXSTEPS-STOP: step=(\d+)", log)
        steps = int(steps_m[-1]) if steps_m else 0
    # Convergence type
    if "MAXSTEPS-STOP" in log:
        ctype = "maxsteps"
    elif "EP-STOP" in log:
        ctype = "ep_stop"
    elif "TIMEOUT" in log:
        ctype = "timeout"
    else:
        ctype = "other"
    dist = mx if mx is not None else "NaN"
    results.append(f"FixedSteps,House01,{seed},{max_steps},{dist},{steps},,{ctype}")

print("Extracted from logs:")
for r in results:
    print(f"  {r}")
