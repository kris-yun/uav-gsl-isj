"""C1 interface/resource qualification only. No ROS, build, simulator or goal calls."""
import hashlib,json,pathlib,subprocess,shutil,sys
from datetime import datetime,timezone
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_C1_CLOSED_LOOP_INTERFACE_QUALIFICATION_20261011'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    remote=r'''import pathlib,json,shutil,os
roots=['/home/zyc/ros2_ws','/home/zyc/pmfs_official_alignment_r5_20261009/ws','/home/zyc/pmfs_b4_native_validation_20261009','/home/zyc/pmfs_b4_official_terminal_namespaced_20261010']
d={'UTC':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'root_disk_free_bytes':shutil.disk_usage('/home/zyc').free,'paths':{r:pathlib.Path(r).exists() for r in roots},'memory':{},'ROS_processes':[],'build_flags':{},'source_package_names':{}}
for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
 if line.split(':')[0] in ['MemAvailable','MemTotal','SwapFree']:d['memory'][line.split(':')[0]]=int(line.split()[1])*1024
for root in roots[:2]:
 p=pathlib.Path(root)/'build/gsl_server/CMakeCache.txt'
 if p.exists():d['build_flags'][str(p)]=[line for line in p.read_text(errors='replace').splitlines() if any(line.startswith(k+':') for k in ['USE_GADEN','DISABLE_NAVIGATION','USE_GUI'])]
 p=pathlib.Path(root)/'src'
 if p.exists():d['source_package_names'][root]=[x.name for x in list(p.iterdir())[:35]]
for x in pathlib.Path('/proc').iterdir():
 if not x.name.isdigit():continue
 try:
  cmd=(x/'cmdline').read_bytes().replace(b'\x00',b' ').decode(errors='replace')
  if any(k in cmd for k in ['gsl_actionserver_node','gmrf_wind_mapping_node','gaden_player/lib','nav2_controller','nav2_bt_navigator','gzserver']):
   if 'python3 -' in cmd:continue
   environ=(x/'environ').read_bytes().split(b'\x00');domain=[e.decode(errors='replace').split('=',1)[1] for e in environ if e.startswith(b'ROS_DOMAIN_ID=')]
   d['ROS_processes'].append({'pid':int(x.name),'program':cmd.split()[0],'ROS_DOMAIN_ID':domain})
 except (OSError,IndexError):pass
print(json.dumps(d))
'''
    cmd=['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128','python3 -']
    r=subprocess.run(cmd,input=remote,capture_output=True,text=True,encoding='utf-8',timeout=30)
    vm={'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'processes_managed':0,'purpose':'read-only inventory and resources; no ROS launch or service requests'}
    if r.returncode==0:vm['parsed']=json.loads(r.stdout)
    (OUT/'C1_VM_READONLY_PREFLIGHT.json').write_text(json.dumps(vm,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    src=BASE/'work/pmfs_r3_r5_checkout/research/pmfs_reproduction/b4_official_terminal_resumed_20261010/source/gsl/PMFS'
    evidence={}
    for name,terms in {'PMFS.cpp':['processGasAndWindMeasurements','timeToSimulate','sourceProbability','updateSourceProbability'],'MovingStatePMFS.cpp':['chooseGoalAndMove','varianceOfHitProb','confidence','indexToGoal','NavigateToPose'],'PMFS_utils.cpp':['startTime','maxSearchTime','Variance','ExpectedValue','saveResultsToFile']}.items():
        p=src/name;lines=p.read_text(encoding='utf-8-sig').splitlines();evidence[name]={'path':str(p),'sha256':sha(p),'selected_lines':{str(i+1):line for i,line in enumerate(lines) if any(k in line for k in terms)}}
    launch=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/N1_B4_launch.py'
    evidence['N1_B4_launch.py']={'path':str(launch),'sha256':sha(launch),'wind_permission':"{'useWindGroundTruth': True}",'author_budget_sim_s':300,'success_variance_threshold':1.5}
    (OUT/'C1_SOURCE_INTERFACE_EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    runtime=json.loads((BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011/R4_BATCH_RECEIPT.json').read_text())
    state={'stage':'READONLY_QUALIFICATION','UTC':datetime.now(timezone.utc).isoformat(),'R4_used_wall_s':runtime['wall_s'],'remaining_4h_compute_s':14400-runtime['wall_s'],'original_physics_batch_used':1,'new_physics_batches':0,'new_native_goals':0,'new_builds':0,'host_disk_free_bytes':shutil.disk_usage(BASE).free,'source_inputs':{str(p.relative_to(BASE)):sha(p) for p in [launch,BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/B4_TERMINAL_RESULT.json',BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011/R4_PREREGISTRATION_REV1.json',BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011/R4_BATCH_RECEIPT.json']},'original_VM_preserved':True,'authorization_scope':'read-only continuation qualification; upstream reports human conditional closed-loop objective. This qualification does not consume new simulation authorization or treat scientific necessity STOP as global project completion.'}
    (OUT/'C1_QUALIFICATION_LEDGER.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(OUT),'VM':vm.get('parsed',vm),'remaining_compute_s':state['remaining_4h_compute_s']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
