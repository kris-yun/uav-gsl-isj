import sys
sys.dont_write_bytecode=True
from remote import run,WORK
from pathlib import Path
import json
code='''from pathlib import Path
import json,os
t=Path('/home/zyc/pmfs_m3_root_discrimination_20261010');processes=[]
for z in Path('/proc').iterdir():
 if not z.name.isdigit():continue
 try:
  args=(z/'cmdline').read_bytes().split(b'\\0');first=args[0].decode(errors='replace')
  if first.startswith(str(t)) and Path(first).name in ['candidate_domain','candidate_forward']:processes.append(dict(pid=int(z.name),exe=first))
 except (FileNotFoundError,PermissionError):pass
sizes={str(p.relative_to(t)):sum(z.stat().st_size for z in p.rglob('*') if z.is_file()) for p in t.iterdir() if p.is_dir()}
print(json.dumps(dict(own_experiment_candidate_processes=processes,own_process_count=len(processes),new_domain_disk_bytes=sizes.get('domain_support_intervention'),new_m3_disk_by_folder=sizes,available_bytes=os.statvfs('/home/zyc').f_bavail*os.statvfs('/home/zyc').f_frsize),indent=2))
'''
r=json.loads(run(code,'DOMAIN_FINAL_READONLY',45));p=WORK.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/domain_support_intervention/DOMAIN_FINAL_PROCESS_RESOURCE_CHECK.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
