import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,tarfile,shutil
W=Path(__file__).resolve().parent;dest=W.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/height_intervention';archive=W/'RAW_HEIGHT_EVIDENCE.tar.gz';r=json.loads((W/'HEIGHT_RAW_COLLECTION.stdout').read_text());assert hashlib.sha256(archive.read_bytes()).hexdigest()==r['sha256']
with tarfile.open(archive,mode='r:gz') as ar:
 for m in ar.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  p=dest/m.name;data=ar.extractfile(m).read()
  if p.exists():
   if p.read_bytes()!=data:
    assert m.name=='HEIGHT_EXECUTION_LEDGER.json' and json.loads(p.read_bytes())==json.loads(data)
    q=dest/'HEIGHT_EXECUTION_LEDGER_REMOTE_EXACT.json';assert not q.exists();q.write_bytes(data)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for n in ['execute_height.py','collect_height.py','extract_height_archive.py','HEIGHT_FROZEN_REMOTE_EXECUTION_VALIDATED.py','HEIGHT_FORWARD_EXECUTION.stdout','analyse_height.py']:
 p=dest/n;assert not p.exists();shutil.copy2(W/n,p)
(dest/'HEIGHT_RAW_COLLECTION.json').write_text(json.dumps(dict(raw_archive_bytes=archive.stat().st_size,raw_archive_sha256=r['sha256'],all_eight_forward_captures_collected=True,local_ledger_remote_ledger_JSON_equal_bytes_differ_due_formatting=True),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(output=str(dest),bytes=archive.stat().st_size),indent=2))
