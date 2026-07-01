#!/usr/bin/env python3
"""Run GSL experiment on VM via SSH."""
import subprocess, sys, time

SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
HOST = "zyc@192.168.111.128"

def ssh(cmd, timeout=30):
    r = subprocess.run(
        [SSH, "-o", "StrictHostKeyChecking=no", "-o", "ControlMaster=no",
         "-o", "ConnectTimeout=10", HOST, cmd],
        capture_output=True, timeout=timeout, errors="replace"
    )
    return r.stdout, r.stderr

def run(method, house, seed, timeout=360):
    cmd = "bash /tmp/run_gsl.sh {} {} {} {}".format(method, house, seed, timeout)
    try:
        out, err = ssh(cmd, timeout=timeout+120)
    except subprocess.TimeoutExpired:
        # Kill everything on VM
        ssh("pkill -9 -f vgr_sim_node; pkill -9 -f gsl_actionserver; pkill -9 -f ros2", timeout=10)
        return None, True, "SSH_TIMEOUT"
    
    # Parse result
    d = None
    in_result = False
    for line in out.split("\n"):
        if "=== RESULT ===" in line:
            in_result = True
            continue
        if "=== END ===" in line:
            in_result = False
            continue
        if in_result:
            line = line.strip()
            if line and not line.startswith("-") and line != "NO_RESULT_FILE":
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        d = float(parts[1])
                    except:
                        pass
    return d, False, out

if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "OPGSL"
    h = sys.argv[2] if len(sys.argv) > 2 else "H01"
    s = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    t = int(sys.argv[4]) if len(sys.argv) > 4 else 360
    print("Running {} {} seed={} timeout={}s".format(m, h, s, t))
    d, to, raw = run(m, h, s, t)
    if d is not None:
        print("Distance: {:.3f}m  Timeout: {}".format(d, to))
    else:
        print("FAILED  Timeout: {}".format(to))
    # Print last few lines of raw for debugging
    lines = raw.split("\n")
    for l in lines[-30:]:
        print(l)
