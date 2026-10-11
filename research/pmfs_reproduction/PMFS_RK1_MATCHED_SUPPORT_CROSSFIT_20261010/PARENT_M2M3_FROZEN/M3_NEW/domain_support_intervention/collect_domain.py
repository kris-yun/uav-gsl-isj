import sys
sys.dont_write_bytecode=True
from remote import run,WORK
from pathlib import Path
import base64,json,hashlib,tarfile,io,shutil
code='''from pathlib import Path
import base64,json,hashlib,tarfile,io
t=Path('/home/zyc/pmfs_m3_root_discrimination_20261010/domain_support_intervention');assert json.loads((t/'DOMAIN_EXECUTION_LEDGER.json').read_text())['completed_calls']==6
buff=io.BytesIO()
with tarfile.open(fileobj=buff,mode='w:gz') as ar:
 for p in t.rglob('*'):
  if p.is_file() and p.name not in ['candidate_domain','entry.o','Simulations.o']:ar.add(p,arcname=p.relative_to(t).as_posix())
b=buff.getvalue();print(json.dumps(dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())))
'''
r=json.loads(run(code,'DOMAIN_RAW_COLLECTION',90));b=base64.b64decode(r['base64']);assert hashlib.sha256(b).hexdigest()==r['sha256'];p=WORK/'RAW_DOMAIN_EVIDENCE.tar.gz';assert not p.exists();p.write_bytes(b)
dest=WORK.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/domain_support_intervention'
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as ar:
 for m in ar.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  p=dest/m.name;data=ar.extractfile(m).read()
  if p.exists():
   if p.read_bytes()!=data:
    assert p.suffix=='.json' and json.loads(p.read_bytes())==json.loads(data),m.name
    new=p.with_name('REMOTE_EXACT_'+p.name);assert not new.exists();new.write_bytes(data)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for n in ['GasDomain.hpp','candidate_domain.cpp','Simulations_gas_domain.cpp','M3Audit.hpp','prepare_domain_sources.py','build_domain.py','execute_domain.py','collect_domain.py','DOMAIN_FROZEN_REMOTE_EXECUTION.py','DOMAIN_FORWARD_EXECUTION.stdout','DOMAIN_ISOLATED_BUILD.stdout']:
 p=dest/n
 if not p.exists():shutil.copy2(WORK/n,p)
 else:assert p.read_bytes()==(WORK/n).read_bytes()
(dest/'DOMAIN_RAW_COLLECTION.json').write_text(json.dumps(dict(raw_archive_bytes=len(b),raw_archive_SHA256=r['sha256'],all_six_forwards_captured=True),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(output=str(dest),bytes=len(b)),indent=2))
