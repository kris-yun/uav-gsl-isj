from common import *
import subprocess,tarfile,io,hashlib,yaml
repo='D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923';pin='4e141e162551e674f2f30ddb8859136c72139aac'
base='Environment_config/PMFS/'
paths=['scenarios/E/_occupancy.pgm','scenarios/E/_occupancy.yaml','scenarios/E/basicSim/E3.yaml','scenarios/E/simulations/E3.yaml','scenarios/E/params/gaden_params.yaml','scenarios/E/params/preproc_params.yaml','navigation_config/nav2_launch.py','navigation_config/nav2_params.yaml','navigation_config/nav_to_pose_no_recovery.xml','navigation_config/nav_to_pose_with_recovery.xml','launch/main_simbot_launch.py']
paths+=['scenarios/E/cad_models/'+n for n in ['MAPIRlab_tables.stl','MAPIRlab_walls.stl','MAPIRlab_wardrobes.stl','MAPIRlab_windows.stl','MAPIRlab_doors.stl']]
paths+=['scenarios/E/wind_simulations/W1/wind_at_cell_centers_0.csv']
files={}
for n in paths:
 b=subprocess.check_output(['git','-C',repo,'show',pin+':'+base+n]);files['official_E3/'+n]=b
 p=OUT/'official'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
manifest={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
files['OFFICIAL_ASSETS_BEFORE.json']=json.dumps(manifest,indent=2).encode()
files['EXECUTION_CONTRACT.json']=json.dumps(dict(authorization='用户批准一次有界E3流程；逐关失败即停止；不批准B4、追加seed、CFD或PMFS核心修改',date='2026-10-09',GSL_pin=pin,GADEN_pin='ccb02e959a45a188e4b6c78792e197633fc64f1c',core_pin='1a20e35cd5f174ae9675a2ae3c796137a05c4ee5',source=[-4,-1.9,.7],preprocessing_budget=1,gas_generation_budget=1,native_goal_budget=1,search_sim_seconds=300,success_variance=1.5,normal_control='physical_PASS AND native_success AND MAP_error<=1m AND full_mean_error<=1m',B4_authorized=False),ensure_ascii=False,indent=2).encode()
setup='source /opt/ros/humble/setup.bash\nsource /home/zyc/ros2_ws/install/setup.bash\nsource '+C+'/ws/install/setup.bash\nexport LD_LIBRARY_PATH='+C+'/ws/install/gaden_common/lib:'+C+'/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH\nexport ROS_DOMAIN_ID=76 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1\nunset GADEN_RNG_SEED\n'
files['RUN_SETUP.sh']=('#!/bin/bash\nset -e\n'+setup).encode()
files['preprocess_worker.py']=r'''from pathlib import Path
import subprocess,time,json
t=Path(__file__).resolve().parent
assert not (t/'PREPROCESS_STARTED.json').exists()
start=time.time();(t/'PREPROCESS_STARTED.json').write_text(json.dumps(dict(preprocessing_executions=1,start_wall_time=start)))
try:
 with (t/'preprocessing.log').open('w') as f:q=subprocess.run(['bash',str(t/'preprocess.sh')],stdout=f,stderr=f,timeout=900)
 result=dict(exit_code=q.returncode,wall_seconds=time.time()-start,preprocessing_executions=1)
except Exception as e:result=dict(exit_code=None,error=str(e),wall_seconds=time.time()-start,preprocessing_executions=1)
(t/'PREPROCESSING_RESULT.json').write_text(json.dumps(result,indent=2))
'''.encode()
code=r'''
import shutil,yaml,subprocess,hashlib
assert not (t/'PREPROCESS_STARTED.json').exists()
inp=t/'preprocess_inputs';shutil.copytree(t/'official_E3/scenarios/E/cad_models',inp/'cad_models')
shutil.copytree(t/'official_E3/scenarios/E/wind_simulations/W1',inp/'wind/W1')
d=t/'derived_E3';d.mkdir()
p=yaml.safe_load((t/'official_E3/scenarios/E/params/preproc_params.yaml').read_text())['gaden_preprocessing']['ros__parameters']
s=yaml.safe_load((t/'official_E3/scenarios/E/simulations/E3.yaml').read_text())
for key in ['models','outlets_models']:p[key]=[str(inp/'cad_models'/Path(n).name) for n in s[key]]
p['wind_files']=str(inp/'wind'/s['wind_sim_path']);p['output_path']=str(d)
(t/'E3_preprocessing_RESOLVED.yaml').write_text(yaml.safe_dump({'/**':{'ros__parameters':p}},sort_keys=False))
c=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009')
exe=c/'ws/install/gaden_preprocessing/lib/gaden_preprocessing/preprocessing'
(t/'preprocess.sh').write_text('#!/bin/bash\nset -e\nsource '+str(t/'RUN_SETUP.sh')+'\n/usr/bin/time -v '+str(exe)+' --ros-args --params-file '+str(t/'E3_preprocessing_RESOLVED.yaml')+'\n')
for n,sha in json.loads((t/'OFFICIAL_ASSETS_BEFORE.json').read_text()).items():assert hashlib.sha256((t/n).read_bytes()).hexdigest()==sha
p=subprocess.Popen(['python3',str(t/'preprocess_worker.py')],stdout=(t/'preprocess_worker.stdout').open('w'),stderr=(t/'preprocess_worker.stderr').open('w'),start_new_session=True)
print(json.dumps(dict(preprocessing_started=True,worker_pid=p.pid,gas_generations=0,native_goals=0,isolated_root=str(t))))
'''
print(put(files,code,'STAGE_PREPROCESS',60))
