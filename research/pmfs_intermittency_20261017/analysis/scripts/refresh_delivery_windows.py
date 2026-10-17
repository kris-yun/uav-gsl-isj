from pathlib import Path
import shutil,json,zipfile,hashlib,collections,csv
R=Path(__file__).resolve().parents[1];D=R/'DELIVERY';A=D/'analysis';old=D/'evidence/native20_shared.zip'
if old.exists():
 with zipfile.ZipFile(old) as z:
  groups=collections.defaultdict(list)
  for n in z.namelist():
   key=n.split('/physical_assets/')[1].split('/')[0] if '/physical_assets/' in n else 'meta'
   groups[key].append(n)
  seen=[]
  for key,names in groups.items():
   q=D/'evidence'/('native20_shared_'+key+'.zip')
   with zipfile.ZipFile(q,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as out:
    for n in names:out.writestr(n,z.read(n));seen.append(n)
   with zipfile.ZipFile(q) as out:assert out.testzip() is None
   assert q.stat().st_size<45*1024**2,(key,q.stat().st_size)
  assert sorted(seen)==sorted(z.namelist())
 # This is only this turn's generated oversized distribution archive.
 assert old.resolve().parent==(R/'DELIVERY/evidence').resolve();old.unlink()
for name in ['scripts','cpp','lineage']:shutil.copytree(R/name,A/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for n in ['diagnostic.png','diagnostic.svg','EVIDENCE_MATRIX.csv','03_OPERATOR_TO_SOURCE_SCORE_TRACE.csv','FINAL_DECISION.json']:shutil.copyfile(R/'results'/n,A/'results'/n)
for n in ['EXECUTION_CONTRACT.md','PROTOCOL_FROZEN.md','CAUSAL_CHAIN_DECISION.md','DATA_IDENTITY_AND_ORIGINAL_RELEASE.md','MINIMUM_SUPPLEMENT.md','IMPLEMENTATION_AND_EVENT_SEMANTICS.md','FAILED_ATTEMPTS_AND_LIMITATIONS.md']:shutil.copyfile(R/n,A/n)
shutil.copyfile(R/'reproduce_all.py',D/'reproduce_all.py');shutil.copyfile(R/'README_给Pro先读.md',D/'README.md')
manifest={}
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='MANIFEST_SHA256.json':manifest[p.relative_to(D).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(D/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2));print(len(manifest),'files,',sum(v['bytes'] for v in manifest.values()),'bytes; max file',max(v['bytes'] for v in manifest.values()))
