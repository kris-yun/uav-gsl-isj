#!/usr/bin/env python3
import os, stat
lines = [
    '#!/bin/bash',
    'source /opt/ros/humble/setup.bash',
    'source /home/zyc/gsl_ws/install/setup.bash',
    '',
    'SEEDS=(0 1 2)',
    'HOUSES=(House01 House02 House03)',
    'OUT=/tmp/cp_sbd_exp/eprocess_v5/results.csv',
    'mkdir -p /tmp/cp_sbd_exp/eprocess_v5',
    'printf  method,house,seed,dist,ep_stop_step,eproc_value\n > ',
    '',
    'for house in ; do',
    '  for seed in ; do',
    '    echo === Running seed= ===',
    '    LOGFILE=/tmp/cp_sbd_exp/eprocess_v5/Ours__s.log',
    '    timeout 300 ros2 launch vgr_bridge vgr_ablation.launch.py \\',
    '      environment:= \\',
    '      method:=M7_full_saisc_pf \\',
    '      seed:= \\',
    '      2>&1 > ',
    '',
    '    DIST=',
    '    EP_STEP=',
    '    EPROC=',
    '    echo  dist=',
    '    printf Ours,%s,%s,%s\n    >> ',
    '  done',
    'done',
    '',
    'echo === RESULTS ===',
    'cat ',
]
with open('/tmp/quick_test_v5.sh', 'w') as f:
    f.write('\n'.join(lines))
os.chmod('/tmp/quick_test_v5.sh', stat.S_IRWXU)
print('OK')
