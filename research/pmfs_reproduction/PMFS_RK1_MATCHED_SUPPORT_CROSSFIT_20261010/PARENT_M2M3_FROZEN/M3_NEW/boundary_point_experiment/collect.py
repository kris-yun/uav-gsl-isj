import sys
sys.dont_write_bytecode=True
from remote import run,WORK,REMOTE
from pathlib import Path
import base64,json,hashlib,tarfile,io,shutil
code='''from pathlib import Path
import base64,json,hashlib,tarfile,io
t=Path(REMOTE);m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010');assert json.loads((t/'EXECUTION_LEDGER.json').read_text())['status']=='PASS_2_ANCHORS_12_NEW_FORWARD_FACTORIAL_COMPLETE'
buff=io.BytesIO()
with tarfile.open(fileobj=buff,mode='w:gz') as ar:
 for p in t.rglob('*'):
  if p.is_file() and p.name not in ['candidate_forward','entry.o','Simulations.o']:ar.add(p,arcname=p.relative_to(t).as_posix())
 for name in ['input.csv','metadata.csv','metadata.json','gaussian_cache.f32','simulation_parameters.csv']:
  ar.add(m1/'snapshot'/name,arcname='snapshot/'+name)
 for job in ['T_true_fine','T_wrong_fine','W_true_fine','anchor_W_fine']:
  root=m1/'forward_calls_after_input_parser_fix'/job
  for p in root.rglob('*'):
   if p.is_file():ar.add(p,arcname='reused_M1/'+job+'/'+p.relative_to(root).as_posix())
b=buff.getvalue()
print(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),base64=base64.b64encode(b).decode())))
'''.replace('REMOTE',repr(REMOTE))
r=json.loads(run(code,'RAW_COLLECTION_AFTER_ARCHIVE_CLOSE_FIX',90));b=base64.b64decode(r['base64']);assert hashlib.sha256(b).hexdigest()==r['sha256']
archive=WORK/'RAW_BOUNDARY_POINT_EVIDENCE_COMPLETE.tar.gz';assert not archive.exists();archive.write_bytes(b)
dest=WORK.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/boundary_point_experiment';dest.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as ar:
 for m in ar.getmembers():
  p=dest/m.name
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(ar.extractfile(m).read())
for n in ['remote.py','prepare_sources.py','build.py','execute.py','collect.py','READONLY_PREFLIGHT.stdout','ISOLATED_BUILD.stdout','FORWARD_EXECUTION.stdout','EXECUTION_CONTRACT_SHA256.txt','FROZEN_REMOTE_EXECUTION.py']:
 p=dest/n
 if not p.exists():shutil.copy2(WORK/n,p)
source=WORK.parents[2]/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010/frozen_M0/evidence/source/gaden/src/RunningSimulation.cpp'
shutil.copy2(source,dest/'GADEN_RunningSimulation_original.cpp')
(dest/'COLLECTION.json').write_text(json.dumps(dict(raw_archive_bytes=len(b),raw_archive_sha256=r['sha256'],all_14_forward_outputs_captured=True,old_uniform_4_copied_without_rerun=True),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(bytes=len(b),sha256=r['sha256'],output=str(dest)),indent=2))
