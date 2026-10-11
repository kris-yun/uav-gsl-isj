from common_r2 import *
import shutil,csv
plan=WORK/'pro_plan';m=load(plan/'MANIFEST_SHA256.json')
for p,v in m.items():assert sha(plan/p)==v,p
assert sha(CORE/'authorization/01_Codex_R2_全域候选与创新必要性连续任务书.md')==m['01_Codex_R2_全域候选与创新必要性连续任务书.md']
dump(CORE/'PRO_PLAN_VERIFICATION.json',dict(status='PASS',files=len(m),ZIP_SHA256='ba400e48690065dff509f0c704e87482661f94a9d9243cdaf39d646d77a2b815'))
for p in plan.rglob('*'):
 if p.is_file():
  dest=CORE/'authorization/pro_plan'/p.relative_to(plan);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
request=Path('D:/ZYC/UAV/.codex/attachments/e4356552-f6df-41c7-9fc5-8bb67bceff59/已粘贴的文本.txt');shutil.copy2(request,CORE/'authorization/USER_REQUEST.txt')
code=r'''from pathlib import Path
import json,subprocess,shutil,os,hashlib
t=Path(REMOTE);data=Path(DATA);assert not t.exists();assert not data.exists();t.mkdir();data.mkdir()
ps=subprocess.run(['ps','-eo','pid,ppid,pgid,etimes,pcpu,pmem,args'],capture_output=True,text=True,check=True).stdout
interesting=[r for r in ps.splitlines() if any(x in r for x in ['filament_simulator','native_entry','native_cold_entry','fsr_s2','gsl_server','gmrf_node']) and 'python3 -' not in r]
elf=Path('/dev/shm/nmc_cold/native_cold_entry');point=Path('/dev/shm/nmc_point/native_point_entry')
libs=Path('/home/zyc/pmfs_m2_process_observation_20261010/libgaden.so')
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
stat=os.statvfs('/dev/shm');mem=dict(r.split(':',1) for r in Path('/proc/meminfo').read_text().splitlines())
print(json.dumps({'existing_processes':interesting,'root_free':shutil.disk_usage(t).free,'shared_free':shutil.disk_usage(data).free,'RAM_disk_free':stat.f_bavail*stat.f_frsize,'MemAvailable':mem['MemAvailable'].strip(),'cold_binary_SHA256':sh(elf),'point_binary_exists':point.exists(),'world_library_SHA256':sh(libs),'RAM_own_new_directory':False}))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(remote(code,'r2_entry_vm_resource_probe',30));assert r['root_free']>=4294967296 and r['shared_free']>=4294967296
assert r['cold_binary_SHA256']==load(R1/'COLD_ENTRY_PROVENANCE.json')['SHA256'] if 'SHA256' in load(R1/'COLD_ENTRY_PROVENANCE.json') else r['cold_binary_SHA256']=='490114422d661bbbe3ed6173f36b800b4880ac80812a16513124988ae3ba5c06'
assert r['world_library_SHA256']=='ed042a1c317a0350e3e1bd701c3ac1e1ab3df23a9807612fd6e91f9234be76c6'
dump(CORE/'ENTRY_VM_PREFLIGHT.json',r)
print(json.dumps(r))
