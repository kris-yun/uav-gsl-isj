"""Restore only exact archived runtime duplicates, dry-run unless --execute."""
from pathlib import Path
import argparse,hashlib,json,zipfile
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--role',required=True);a.add_argument('--execute',action='store_true');x=a.parse_args();R=Path(__file__).resolve().parent;plan=json.loads((R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json').read_text());role=next(z for z in plan['roles']if z['id']==x.role);C=Path(role['host_case']);p=C/'ARCHIVE_PRUNE_RECEIPT.json'
 if not p.exists():print(json.dumps(dict(status='NO_PRUNED_WORKING_COPIES',role=x.role)));return
 q=json.loads(p.read_text());arc=q['archive'];assert digest(arc['archive'])==arc['archive_sha256'];count=0
 with zipfile.ZipFile(arc['archive'])as z:
  for r in q['removed']:
   t=(C/r['path']).resolve();assert t.is_relative_to((C/'runtime').resolve());b=z.read(r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256']
   if t.exists():assert digest(t)==r['sha256'];continue
   if x.execute:
    t.parent.mkdir(parents=True,exist_ok=True)
    with t.open('xb')as f:f.write(b)
   count+=1
 print(json.dumps(dict(status='RESTORED_EXACT_SHA'if x.execute else'DRY_RUN_VERIFIED_RESTORABLE',role=x.role,missing_working_copies=count)))
if __name__=='__main__':main()
