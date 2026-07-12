#!/usr/bin/env python3
import subprocess, re, os

os.makedirs('/tmp/cp_sbd_exp/v5_quick', exist_ok=True)
logfile = '/tmp/cp_sbd_exp/v5_quick/test.log'

cmd = (
    'source /opt/ros/humble/setup.bash && '
    'source /home/zyc/gsl_ws/install/setup.bash && '
    'timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py '
    'environment:=House01 method:=M7_full_saisc_pf seed:=0'
)
with open(logfile, 'w') as lf:
    subprocess.run(['bash', '-c', cmd], stdout=lf, stderr=subprocess.STDOUT, timeout=310)

with open(logfile) as f:
    log = f.read()

# Find all EP-STEP and EP-STOP lines
for line in log.split(chr(10)):
    if 'EP-STEP' in line or 'EP-STOP' in line:
        # Extract key info
        step = re.search(r'step=(\d+)', line)
        eproc = re.search(r'eproc=([0-9.]+)', line)
        logm = re.search(r'logM=([0-9.-]+)', line)
        postn = re.search(r'postN=(\d+)', line)
        radius = re.search(r'radius=([0-9.]+)', line)
        s = step.group(1) if step else '?'
        e = eproc.group(1) if eproc else '?'
        l = logm.group(1) if logm else '?'
        p = postn.group(1) if postn else '?'
        r = radius.group(1) if radius else '?'
        print(f'step={s} eproc={e} logM={l} postN={p} radius={r}')

# Extract distance
dist_m = re.findall(r'distance:\s*([0-9.]+)', log)
if dist_m:
    print(f'Final distance: {dist_m[-1]}m')
