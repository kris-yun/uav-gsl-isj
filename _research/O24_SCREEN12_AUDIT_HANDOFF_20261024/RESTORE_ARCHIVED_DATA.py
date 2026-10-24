"""Restore verified duplicate removals. Defaults to check-only; no overwrite.

python RESTORE_ARCHIVED_DATA.py --path ORIGINAL_PATH [--execute]
Only paths in SAFE_CLEANUP_ACTION_RECEIPTS.json can be restored.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--path',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--receipt');a=p.parse_args()
 root=Path(__file__).resolve().parent;data=json.loads(Path(a.receipt or root/'99_SAFE_CLEANUP_RECEIPTS/SAFE_CLEANUP_ACTION_RECEIPTS.json').read_text(encoding='utf8'))
 candidates=data.get('actions',data.get('receipts',[]))
 target=Path(a.path).resolve();rows=[x for x in candidates if Path(x['path']).resolve()==target and x['status']=='DELETED_VERIFIED_DUPLICATE']
 assert len(rows)==1,'Path not uniquely recorded as a removed verified duplicate'
 row=rows[0];expected=row['expected_sha256']
 if target.exists():
  assert sha(target)==expected,'Existing different file; refusing overwrite'
  print(json.dumps(dict(status='ALREADY_PRESENT_SHA_MATCH',path=str(target))));return
 if row['kind']=='EXACT_ARCHIVE_COPY':
  keeper=Path(row['keeper']);assert keeper.is_file()and sha(keeper)==expected,'Keeper missing or SHA mismatch'
  if a.execute:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(keeper,target)
 else:
  archive=Path(row['archive']);assert sha(archive)==row['archive_sha256'],'Archive SHA mismatch'
  # No archive extractall: write exactly one recorded member to one recorded path.
  with zipfile.ZipFile(archive)as z:
   assert hashlib.sha256(z.read(row['member'])).hexdigest()==expected,'Member SHA mismatch'
   if a.execute:
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb')as f,z.open(row['member'])as src:shutil.copyfileobj(src,f)
 if a.execute:assert sha(target)==expected,'Restored SHA mismatch'
 print(json.dumps(dict(status='RESTORED_SHA_MATCH'if a.execute else'DRY_RUN_VERIFIED_RESTORABLE',path=str(target),bytes=row['bytes'])))

if __name__=='__main__':main()
