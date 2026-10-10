from common import *
print(remote(r'''
from pathlib import Path
import json,subprocess,os
t=Path('/home/zyc/pmfs_e3_native_validation_20261009');c=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009');r5=Path('/home/zyc/pmfs_official_alignment_r5_20261009')
assert json.loads((t/'GATE1.json').read_text())['verdict']=='PASS' and json.loads((t/'GATE2.json').read_text())['verdict'].startswith('PASS')
assert not (t/'RUN_STARTED.json').exists() and not (t/'driver.stdout').exists()
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if b'ROS_DOMAIN_ID=76' in (p/'environ').read_bytes().split(b'\0'):active.append(p.name)
 except OSError:pass
assert not active,active
shell='source /opt/ros/humble/setup.bash; source /home/zyc/ros2_ws/install/setup.bash; source '+str(r5/'ws/install/setup.bash')+'; source '+str(c/'ws/install/setup.bash')+'; export AMENT_PREFIX_PATH='+str(t/'overlay')+':${AMENT_PREFIX_PATH}; export LD_LIBRARY_PATH='+str(c/'ws/install/gaden_common/lib')+':'+str(c/'ws/build/gaden_common/third_party/gaden_core/third_party/libbsc')+':${LD_LIBRARY_PATH}; export ROS_DOMAIN_ID=76 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1; exec python3 '+str(t/'runtime_driver.py')
(t/'RUN_SHELL.sh').write_text('#!/bin/bash\nset -e\n'+shell+'\n')
p=subprocess.Popen(['bash','-lc',shell],stdout=(t/'driver.stdout').open('w'),stderr=(t/'driver.stderr').open('w'),start_new_session=True)
(t/'RUNTIME_DRIVER_STARTED.json').write_text(json.dumps(dict(driver_pid=p.pid,driver_executions=1,native_goal_budget=1)))
print(json.dumps(dict(driver_pid=p.pid,native_goal_budget=1,preflight_gates_before_goal=True,search_budget_ROS_s=300.,new_gas_generations=0,B4=False)))
''','START_NATIVE',30))
