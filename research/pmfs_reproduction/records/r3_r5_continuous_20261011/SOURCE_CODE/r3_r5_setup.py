import ast, csv, hashlib, json, os, platform, shutil, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import psutil

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
REPO=BASE/'work/pmfs_r3_r5_checkout'
OUT.mkdir(exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
zpath=Path(r'C:\Users\50176\Downloads\Codex_R3_R5_%E8%BF%9E%E7%BB%AD%E7%A0%94%E7%A9%B6%E4%B8%8E%E6%96%B9%E6%B3%95%E7%A0%94%E5%8F%91%E6%80%BB%E5%8C%85_20261011.zip')
assert sha(zpath)=='1f67cfdb3903979b80a67a58ee3e1dd5c10a238bf37f0c687fb17d62473df680'
auth=OUT/'authorization';auth.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    for i in z.infolist():
        p=auth/i.filename
        assert p.resolve().is_relative_to(auth.resolve()) and not i.is_dir()
        if p.exists(): assert p.read_bytes()==z.read(i.filename)
        else:p.write_bytes(z.read(i.filename))
    for line in z.read('SHA256SUMS.txt').decode().splitlines():
        h,n=line.split(maxsplit=1);assert sha(auth/n.strip())==h
    for n in ['r2_triage.py','transport_reference.py']:ast.parse(z.read(n).decode())
parent=BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_CORE'
manifest=json.loads((parent/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
bad=[n for n,h in manifest.items() if sha(parent/n)!=h]
assert not bad,bad
inputs={str((parent/n).resolve()):h for n,h in manifest.items()}
for p in [zpath,BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_CORE.zip',BASE/'outputs/PMFS_R2_失效机制解释补充包_20261011.zip']:
    inputs[str(p.resolve())]=sha(p)
dump('ALL_INPUT_SHA256.json',inputs)
vmcode="""import json,os,shutil
from pathlib import Path
roots=[Path('/home/zyc/ros2_ws'),Path('/home/zyc/pmfs_full_domain_r2_20261011'),Path('/home/zyc/pmfs_b4_native_validation_20261009')]
print(json.dumps({'roots':{str(p):p.exists() for p in roots},'disk_free':shutil.disk_usage('/home/zyc').free,'load':os.getloadavg(),'ROS_domain':'not_started','dynamic_asset_qualification':'No supplied new synchronized dynamic record; existing R2 observation period CFD10'}))
"""
cmd=['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128','python3 -']
try:
    p=subprocess.run(cmd,input=vmcode,text=True,capture_output=True,timeout=20)
    vm={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'operation':'read-only preflight; no VM processes managed'}
except Exception as e:vm={'error':repr(e),'operation':'read-only preflight'}
dump('VM_READONLY_PREFLIGHT.json',vm)
contract={'stage':'AUTHORIZED_PREPARATION','parent_commit':'7600731844bea2b1a5253518ef4e9dbbda70383e',
 'branch':'research/r3-r5-posterior-dynamic-gap-20261011','user_authorization':'Direct async reply: 按合同连续执行',
 'UTC':datetime.now(timezone.utc).isoformat(),'user_timezone':'America/Los_Angeles',
 'host':platform.platform(),'python':sys.version,'python_binary_sha256':sha(Path(sys.executable)),
 'permissions':{'R3':'Read only','R4':'One controlled CPU dynamic batch <=4h','R5':'Only qualified necessity gate; CPU only within remaining batch','CFD':False,'new_GPU_training':False,'paid_resources':False,'new_native_navigation':False},
 'limits':{'R3_wall_s':1800,'literature_interface_wall_s':7200,'one_physics_batch_wall_s':14400,'process_RSS_bytes':1073741824,'new_output_bytes':8589934592,'minimum_free_disk_bytes':4294967296},
 'science':{'scope':'2D periodic controlled advection-diffusion; not lakeshore/3D/real sensor','R2_role':'All inspected; descriptive development only','main_R4_decision':'minimum posterior Euclidean-risk action constrained to complete 25-source catalog','no_native_PMFS_success_claim':True},
 'current_resources':{'disk_free_C':shutil.disk_usage(OUT).free,'RAM_available':psutil.virtual_memory().available},
 'stage_status':{'R3':'NOT_STARTED','R4':'NOT_STARTED','R5':'CONDITIONAL_NOT_STARTED'},
 'technical_faults':[{'class':'remote quoting','attempt':1,'error':'SyntaxError during read-only shell preflight','repair':'standalone Python sent through SSH stdin; unchanged science'}],
 'closed_loop_budget':'No new ROS/GADEN/navigation authorization in exact R3-R5 contract; bounded fixed source-blind route numerical tasks only. Any later ROS closed-loop needs separate frozen count/budget.'}
dump('RUN_CONTRACT.json',contract)
with (OUT/'EXECUTION_LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'UTC':contract['UTC'],'phase':'prepare','parent_hashes_verified':len(manifest),'new_physics_calls':0,'vm_preflight':vm['returncode'] if 'returncode' in vm else 'error'},ensure_ascii=False)+'\n')
print(json.dumps({'OUT':str(OUT),'parent_hashes':len(manifest),'vm_status':vm.get('returncode'),'disk_free_GiB':contract['current_resources']['disk_free_C']/2**30},ensure_ascii=False))
