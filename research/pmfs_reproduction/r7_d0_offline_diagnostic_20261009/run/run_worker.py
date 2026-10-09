from pathlib import Path
import json,subprocess,time
t=Path(__file__).resolve().parent
assert not (t/'RUN_STARTED.json').exists()
(t/'RUN_STARTED.json').write_text(json.dumps(dict(classification='COUNTERFACTUAL_DIAGNOSTIC_NOT_NATIVE_RUN',shadow_budget=1,native_goals=0)))
shell='source /opt/ros/humble/setup.bash; source /home/zyc/ros2_ws/install/setup.bash; source /home/zyc/native_pmfs_recovery_v1/install/setup.bash; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1; '+str(t/'shadow_update')+' '+str(t/'input')+' '+str(t/'result')
start=time.time()
with (t/'diagnostic.log').open('w') as log:
 p=subprocess.run(['bash','-lc',shell],stdout=log,stderr=log,timeout=120)
(t/'RUN_RESULT.json').write_text(json.dumps(dict(exit_code=p.returncode,wall_seconds=time.time()-start,shadow_source_updates=1 if (t/'result/SOURCE_UPDATE_STARTED.json').exists() else 0,native_goals=0,ROS_nodes_started=0,new_gas_generations=0)))
