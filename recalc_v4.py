#!/usr/bin/env python3
import re, os, math

sources = {
    'House01': [-0.40, -2.90, -0.30],
    'House02': [0.0, -1.0, 0.2],
    'House03': [-0.45, 1.90, -0.10],
}

print('method,house,seed,dist,steps,ep_stop_step')
for house in ['House01','House02','House03']:
    for seed in range(5):
        logfile = f'/tmp/cp_sbd_exp/final_v4/Ours_{house}_s{seed}.log'
        if not os.path.exists(logfile):
            continue
        with open(logfile) as f:
            log = f.read()
        
        result = re.findall(r'SDNBV RESULT:.*?MAP=\(([-\d.,]+)\).*?steps=(\d+)', log)
        if result:
            coords = [float(x) for x in result[0][0].split(',')]
            steps = result[0][1]
            src = sources[house]
            dist = math.sqrt(sum((a-b)**2 for a,b in zip(coords, src)))
        else:
            dist = 999
            steps = 'N/A'
        
        ep_lines = [l for l in log.split('\n') if 'EP-STOP' in l]
        ep_step = 'N/A'
        if ep_lines:
            sm = re.search(r'step=(\d+)', ep_lines[0])
            if sm: ep_step = sm.group(1)
        
        print(f'Ours,{house},{seed},{dist:.3f},{steps},{ep_step}')
