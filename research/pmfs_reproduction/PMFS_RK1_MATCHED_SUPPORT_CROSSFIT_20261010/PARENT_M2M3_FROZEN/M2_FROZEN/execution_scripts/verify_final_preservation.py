from common import *
import hashlib
parents=[]
for name in ['PMFS_B4_M1_SOURCE_REPRESENTATION_20261010','PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010']:
    folder=ROOT/'outputs'/name
    manifest=json.loads((folder/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
    for path,digest in manifest.items():assert hashlib.sha256((folder/path).read_bytes()).hexdigest()==digest,(name,path)
    z=ROOT/'outputs'/(name+'_SMALL.zip')
    parents.append(dict(parent=name,unchanged_manifest_members=len(manifest),zip_exists=z.exists(),zip_SHA256=hashlib.sha256(z.read_bytes()).hexdigest() if z.exists() else None))
(OUT/'PARENT_PRESERVATION_CHECK.json').write_text(json.dumps(parents,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
code=r'''
import json,hashlib,shutil,csv,os
from pathlib import Path
t=Path('/home/zyc/pmfs_m2_process_observation_20261010')
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode(errors='replace')
 except (FileNotFoundError,PermissionError):continue
 if 'filament_simulator' in cmd and 'pmfs_m2_process_observation_20261010' in cmd:active.append(dict(pid=int(p.name),cmd=cmd))
checked=0
for folder in (t/'realizations').iterdir():
 for row in csv.DictReader((folder/'ALL_FRAME_SHA256_AND_TIME.csv').open()):
  p=folder/'bank'/('iteration_'+row['frame']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['SHA256'];checked+=1
assert checked==14424 and not active
guard=json.loads((t/'EIGHT_REFERENCE_CAPTURE_SUMMARY.json').read_text())
for entry in guard['protected_hashes']:assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['SHA256']
print(json.dumps(dict(verdict='FINAL_FULL_BANK_INTEGRITY_AND_NO_OWN_GENERATORS_PASS',original_VM_only=True,active_own_generator_processes=active,full_generated_frame_hashes_rechecked=checked,old_protected_assets_unchanged=len(guard['protected_hashes']),task_disk_bytes=sum(p.stat().st_size for p in t.rglob('*') if p.is_file()),home_free_bytes=shutil.disk_usage(t).free),indent=2))
'''
result=json.loads(run(code,'FINAL_VM_PRESERVATION_CHECK',60))
(OUT/'FINAL_VM_PROCESS_AND_PRESERVATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(local_parents=parents,VM=result),ensure_ascii=False,indent=2))
