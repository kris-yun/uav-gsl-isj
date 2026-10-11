from common_n import *
proposal=load(CORE/'CROSS_TASK_RESOURCE_RELOCATION_PROPOSAL.json')
code='''from pathlib import Path
import os,json,hashlib,shutil,time
files=PROPOSAL
root=Path('/home/zyc/ros2_ws/fsr_s2_r15_autonomous_20261011T070129Z').resolve()
dest=Path('/mnt/hgfs/workspace/FSR_APPROVED_BINARY_PRESERVATION_20261011')
assert not dest.exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def active():
 found=[]
 for p in Path('/proc').glob('[0-9]*/exe'):
  try:
   target=p.resolve()
   if target.parent==root:found.append(str(target))
  except OSError:pass
 return found
assert not active(),active()
for row in files:
 p=Path(row['path']);assert p.parent.resolve()==root and p.is_file() and not p.is_symlink()
 assert p.stat().st_size==row['bytes'] and sha(p)==row['SHA256']
dest.mkdir(parents=True)
proof={'authorization':'user approved transfer of these three inactive binaries with SHA verification and original-path links','before_root_free':shutil.disk_usage(root).free,'records':[]}
for row in files:
 p=Path(row['path']);q=dest/p.name;shutil.copy2(p,q)
 assert sha(q)==row['SHA256'] and sha(p)==row['SHA256'] and not active()
 backup=p.with_name(p.name+'.approved_relocation_backup');assert not backup.exists()
 p.rename(backup)
 try:p.symlink_to(q)
 except Exception:backup.rename(p);raise
 assert p.resolve()==q.resolve() and sha(p)==row['SHA256']
 backup.unlink()
 proof['records'].append(dict(row,destination=str(q),original_path_symlink=str(p),verified_SHA256=sha(q)))
proof['after_root_free']=shutil.disk_usage(root).free
proof['bytes']=sum(x['bytes'] for x in files)
proof['reserve_pass']=proof['after_root_free']>=4294967296
(dest/'RELOCATION_PROOF.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof))
'''.replace('PROPOSAL',repr(proposal['files']))
proof=json.loads(run_remote(code,'approved_external_3_relocation',timeout=120))
dump(CORE/'APPROVED_EXTERNAL_BINARY_RELOCATION.json',proof)
assert proof['reserve_pass']
print(json.dumps({'reserve_pass':True,'root_free':proof['after_root_free'],'preserved_bytes':proof['bytes']}))
