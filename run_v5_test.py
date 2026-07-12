#!/usr/bin/env python3
import subprocess, re, os

os.makedirs('/tmp/cp_sbd_exp/eprocess_v5', exist_ok=True)
out = '/tmp/cp_sbd_exp/eprocess_v5/results.csv'

with open(out, 'w') as f:
    f.write('method,house,seed,dist,ep_stop_step,eproc_value\n')

seeds = [0, 1, 2]
houses = ['House01', 'House02', 'House03']

env = os.environ.copy()
env['PATH'] = '/opt/ros/humble/bin:' + env.get('PATH', '')

for house in houses:
    for seed in seeds:
        print(f'=== Running {house} seed={seed} ===', flush=True)
        logfile = f'/tmp/cp_sbd_exp/eprocess_v5/Ours_{house}_s{seed}.log'
        cmd = (
            'source /opt/ros/humble/setup.bash && '
            'source /home/zyc/gsl_ws/install/setup.bash && '
            f'timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py '
            f'environment:={house} method:=M7_full_saisc_pf seed:={seed}'
        )
        with open(logfile, 'w') as lf:
            result = subprocess.run(
                ['bash', '-c', cmd],
                stdout=lf, stderr=subprocess.STDOUT, timeout=310
            )

        with open(logfile) as lf:
            log = lf.read()

        dist_m = re.findall(r'distance:\s*([0-9.]+)', log)
        dist = dist_m[-1] if dist_m else 'N/A'

        ep_lines = [l for l in log.split('\n') if 'EP-STOP' in l]
        ep_step = 'N/A'
        ep_val = 'N/A'
        if ep_lines:
            sm = re.search(r'step=(\d+)', ep_lines[0])
            vm = re.search(r'eproc=([0-9.]+)', ep_lines[0])
            if sm: ep_step = sm.group(1)
            if vm: ep_val = vm.group(1)

        print(f'  dist={dist} ep_stop_step={ep_step} eproc={ep_val}', flush=True)
        with open(out, 'a') as f:
            f.write(f'Ours,{house},{seed},{dist},{ep_step},{ep_val}\n')

print('\n=== RESULTS ===')
with open(out) as f:
    print(f.read())
