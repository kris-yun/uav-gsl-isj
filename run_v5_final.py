#!/usr/bin/env python3
import subprocess, re, os

os.makedirs('/tmp/cp_sbd_exp/v5_final', exist_ok=True)
out = '/tmp/cp_sbd_exp/v5_final/results.csv'

with open(out, 'w') as f:
    f.write('method,house,seed,dist,steps,ep_stop_step,eproc_value\n')

seeds = list(range(10))
houses = ['House01', 'House02', 'House03']

sources = {
    'House01': [-0.40, -2.90, -0.30],
    'House02': [0.0, -1.0, 0.2],
    'House03': [-0.45, 1.90, -0.10],
}

for house in houses:
    for seed in seeds:
        print(f'=== {house} seed={seed} ===', flush=True)
        logfile = f'/tmp/cp_sbd_exp/v5_final/{house}_s{seed}.log'
        cmd = (
            'source /opt/ros/humble/setup.bash && '
            'source /home/zyc/gsl_ws/install/setup.bash && '
            f'timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py '
            f'environment:={house} method:=M7_full_saisc_pf seed:={seed}'
        )
        with open(logfile, 'w') as lf:
            subprocess.run(['bash', '-c', cmd], stdout=lf, stderr=subprocess.STDOUT, timeout=310)

        with open(logfile) as lf:
            log = lf.read()

        result = re.findall(r'SDNBV RESULT:.*?MAP=\(([-\d.,]+)\).*?steps=(\d+)', log)
        if result:
            coords = [float(x) for x in result[0][0].split(',')]
            steps = result[0][1]
            src = sources[house]
            dist = sum((a-b)**2 for a,b in zip(coords, src))**0.5
        else:
            dist = 999
            steps = 'N/A'

        ep_lines = [l for l in log.split('\n') if 'EP-STOP' in l]
        ep_step = 'N/A'
        ep_val = 'N/A'
        if ep_lines:
            sm = re.search(r'step=(\d+)', ep_lines[0])
            vm = re.search(r'eproc=([0-9.]+)', ep_lines[0])
            if sm: ep_step = sm.group(1)
            if vm: ep_val = vm.group(1)

        print(f'  dist={dist:.3f}m steps={steps} ep_stop={ep_step}', flush=True)
        with open(out, 'a') as f:
            f.write(f'Ours,{house},{seed},{dist:.3f},{steps},{ep_step},{ep_val}\n')

print('\n=== RESULTS ===')
with open(out) as f:
    print(f.read())
