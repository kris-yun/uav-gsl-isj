import re, math, sys

def extract(log_file, sx, sy):
    with open(log_file, "r", errors="replace") as fh:
        c = fh.read()
    # strip ANSI
    clean = ""
    i = 0
    while i < len(c):
        if c[i] == "\x1b":
            i += 1
            while i < len(c) and c[i] in "0123456789;":
                i += 1
            if i < len(c) and c[i] == "m":
                i += 1
        else:
            clean += c[i]
            i += 1
    c = clean
    ctype = "other"
    if "MAXSTEPS-STOP" in c: ctype = "maxsteps"
    elif "EP-STOP" in c: ctype = "ep_stop"
    elif "CP-STOP" in c: ctype = "cp_stop"
    elif "Found the emission source" in c: ctype = "found"
    elif "TIMEOUT" in c: ctype = "timeout"
    elif "Could not find" in c: ctype = "not_found"
    dist = None; steps = 0
    for pattern in [r"MAXSTEPS-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)",
                    r"EP-STOP: step=(\d+) MAP=\(([-\d.]+),([-\d.]+)"]:
        m = re.search(pattern, c)
        if m:
            steps = int(m.group(1))
            mx = float(m.group(2)); my = float(m.group(3))
            dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
            break
    if dist is None:
        m = re.search(r"final_error=([\d.]+)", c)
        if m: dist = float(m.group(1))
    if steps == 0:
        sm = re.findall(r"step=(\d+)", c)
        if sm: steps = int(sm[-1])
    return dist, steps, ctype

if __name__ == "__main__":
    log = sys.argv[1]
    sx = float(sys.argv[2])
    sy = float(sys.argv[3])
    d, s, ct = extract(log, sx, sy)
    if d is not None:
        print(f"{d:.3f}|{s}|{ct}")
    else:
        print(f"None|{s}|{ct}")
