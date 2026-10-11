from common_n import *
import shutil,csv
CORE.mkdir();RAW.mkdir()
pro=WORK/'pro_handoff/PMFS_NATIVE_MECHANISM_CLOSURE_R1'
hashes=load(pro/'MANIFEST_SHA256.json');assert all(sha(pro/n)==h for n,h in hashes.items())
for p in pro.rglob('*'):
    if p.is_file():q=CORE/'authorization'/p.relative_to(pro);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
request=Path('D:/ZYC/UAV/.codex/attachments/7faf4501-5ce4-42b1-8bce-1865267fffcd/已粘贴的文本.txt')
shutil.copyfile(request,CORE/'authorization/USER_REQUEST.txt')
contract=load(pro/'campaign_contract.json');contract['status']='AUTHORIZED_PREFLIGHT';contract['entry_unix']=load(WORK/'ENTRY_TIME.json')['start_unix'];dump(CORE/'CAMPAIGN_CONTRACT.json',contract)
tail=r'''
import os,shutil,hashlib,subprocess
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  cmd=(p/'cmdline').read_bytes().split(bytes([0]));exe=Path(cmd[0].decode()).name
  if exe in ['filament_simulator','gsl_actionserver_node','gsl_server','simpleFoam','pimpleFoam','query_native']:active.append(dict(pid=int(p.name),exe=exe))
 except (OSError,UnicodeError):pass
assert not active,active
free=shutil.disk_usage(t).free;assert free>=4294967296+67108864,(free,'need4GiB +64MiB build allowance')
shared=shutil.disk_usage('/mnt/hgfs/workspace').free;assert shared>10737418240
items={}
roots=['/home/zyc/pmfs_native_capture_r4_20261009','/home/zyc/pmfs_b4_m1_source_representation_20261010',
 '/home/zyc/pmfs_m2_event_map_replay_20261010','/home/zyc/pmfs_m2_process_observation_20261010',
 '/home/zyc/pmfs_official_alignment_r5_20261009/ws','/home/zyc/pmfs_b4_official_terminal_namespaced_20261010',
 '/home/zyc/pmfs_e3_native_validation_20261009','/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws']
for name in roots:
 p=Path(name);items[name]=dict(exists=p.exists(),files=[q.name for q in p.iterdir() if q.is_file()] if p.exists() else [])
r=Path(roots[0]);objects={n:dict(exists=(r/n).exists(),SHA256=sh(r/n) if (r/n).exists() else None) for n in ['BUILD_CONTEXT.json','Simulations_capture.o','Simulations_replay.o','Math_accessors.o','PMFSLib.o','NQAQuadtree.o','HitProbability.o']}
for name in [roots[1]+'/candidate_forward',roots[2]+'/event_map_replay',roots[3]+'/libgaden.so',roots[3]+'/query_native']:
 p=Path(name);objects[name]=dict(exists=p.exists(),SHA256=sh(p) if p.exists() else None)
result=dict(status='PASS_EXISTING_VM_READONLY_PREFLIGHT',active_science_processes=active,root_free_bytes=free,shared_free_bytes=shared,
 actual_environment=items,objects=objects,ROS_DOMAIN_ID_selected=229,new_VM=False,existing_runtime_only=True)
(t/'PREFLIGHT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
'''
result=json.loads(upload({'CAMPAIGN_CONTRACT.json':(CORE/'CAMPAIGN_CONTRACT.json').read_bytes()},tail,'EXISTING_VM_PREFLIGHT',45))
dump(CORE/'PREFLIGHT.json',result)
dump(CORE/'PRO_HANDOFF_VERIFICATION.json',dict(status='PASS',manifest_entries=len(hashes),zip_SHA256=sha(Path('C:/Users/50176/Downloads/PMFS_RK2B_独立审核与原生机制闭合总计划_a5d93c9.zip'))))
print(json.dumps(result,indent=2))
