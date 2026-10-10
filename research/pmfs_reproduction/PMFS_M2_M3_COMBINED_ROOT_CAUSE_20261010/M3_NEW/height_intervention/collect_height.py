import sys
sys.dont_write_bytecode=True
from remote import run,WORK
from pathlib import Path
import base64,json,hashlib,tarfile,io,shutil
code='''from pathlib import Path
import base64,json,hashlib,tarfile,io
t=Path('/home/zyc/pmfs_m3_root_discrimination_20261010/height_intervention');assert json.loads((t/'HEIGHT_EXECUTION_LEDGER.json').read_text())['completed_calls']==8
buff=io.BytesIO()
with tarfile.open(fileobj=buff,mode='w:gz') as ar:
 for p in t.rglob('*'):
  if p.is_file():ar.add(p,arcname=p.relative_to(t).as_posix())
b=buff.getvalue();print(json.dumps(dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())))
'''
r=json.loads(run(code,'HEIGHT_RAW_COLLECTION',90));b=base64.b64decode(r['base64']);assert hashlib.sha256(b).hexdigest()==r['sha256'];p=WORK/'RAW_HEIGHT_EVIDENCE.tar.gz';assert not p.exists();p.write_bytes(b)
dest=WORK.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/height_intervention'
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as ar:
 for m in ar.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  p=dest/m.name;data=ar.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data,m.name
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for n in ['execute_height.py','collect_height.py','HEIGHT_FROZEN_REMOTE_EXECUTION_VALIDATED.py','HEIGHT_FORWARD_EXECUTION.stdout']:
 p=dest/n;assert not p.exists();shutil.copy2(WORK/n,p)
(dest/'HEIGHT_RAW_COLLECTION.json').write_text(json.dumps(dict(raw_archive_bytes=len(b),raw_archive_sha256=r['sha256'],all_eight_forward_captures_collected=True),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(output=str(dest),bytes=len(b)),indent=2))
