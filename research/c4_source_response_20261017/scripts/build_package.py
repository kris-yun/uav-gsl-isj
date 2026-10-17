"""Create an upload bundle without relocating canonical data. No file deletion."""
from pathlib import Path
import json,hashlib,zipfile,shutil,sys,csv
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
B=Path(r'C:\Users\50176\Downloads\C4_PRO_REVIEW_20261017')
Z=B.with_name('C4_SOURCE_RESPONSE_ATTRIBUTION_20261017.zip')
resume='--resume' in sys.argv
assert (B.exists() if resume else not B.exists()) and not Z.exists();assert (R/'results/FINAL_DECISION.json').exists()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest=json.loads((R/'INPUT_MANIFEST_SHA256.json').read_text())
for name,v in manifest.items():assert sha(P/name)==v['sha256'],name
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<200*1024**2
if not resume:
 B.mkdir();(B/'evidence').mkdir()
 shutil.copytree(R,B/'study',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copyfile(R/'README_zh.md',B/'README_zh.md');shutil.copyfile(R/'reproduce.py',B/'reproduce.py')
files=[]
for case in ['C4','C3']:
 files += [p for p in (P/f'cases/{case}/native_execution').rglob('*') if p.is_file()]
 for name in ['generation.yaml','PHYSICAL_FRAME_TIME.csv']:
  p=P/f'cases/{case}'/name
  if p.exists():files.append(p)
files.append(P/'CASE_INDEX.json')
physical=json.loads((R/'lineage/PHYSICAL_CONTEXT_ASSETS_SHA256.json').read_text())
for name,h in physical.items():assert sha(P/name)==h;files.append(P/name)
S=P/'native_pmfs/official_upstream/gsl_server/src/gsl_server'
for name in ['algorithms/Common/Grid2D.hpp','algorithms/Common/Utils/Math.cpp','algorithms/Common/Utils/Math.hpp','algorithms/PMFS/internal/Simulations.cpp','algorithms/PMFS/internal/HitProbability.hpp','algorithms/PMFS/internal/Settings.hpp']:
 files.append(S/name)
if not resume:
 with zipfile.ZipFile(B/'evidence/native_histories.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(set(files)):z.write(p,'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA/'+p.relative_to(P).as_posix())
  for name in ['native_analysis.py','cdr_grid.py','cdr_wind.py','portable_recompute.py']:
   z.write(P.parent/name,'NATIVE_PMFS_WIND_RECOVERY_20261014/'+name)
with zipfile.ZipFile(B/'evidence/native_histories.zip') as z:
 for name,v in manifest.items():
  b=z.read('NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA/'+name.replace('\\','/'));assert hashlib.sha256(b).hexdigest()==v['sha256']
allfiles=[p for p in B.rglob('*') if p.is_file()]
bundle={p.relative_to(B).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(allfiles)}
(B/'MANIFEST_SHA256.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2),'utf-8')
with zipfile.ZipFile(Z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted([p for p in B.rglob('*') if p.is_file()]):z.write(p,p.relative_to(B).as_posix())
with zipfile.ZipFile(Z) as z:
 assert len(z.infolist())==len(bundle)+1
 for name,v in bundle.items():
  with z.open(name) as f:got=hashlib.file_digest(f,'sha256').hexdigest()
  assert got==v['sha256'],name
receipt=dict(status='PASS_ALL_ARCHIVE_MEMBERS_CRC_AND_SHA256',members=len(bundle)+1,input_history_files_verified=len(manifest),archive=str(Z),bytes=Z.stat().st_size,sha256=sha(Z),new_ROS=0,new_gas_worlds=0)
Z.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+Z.name+'\n','utf-8')
(R/'PACKAGE_VERIFY.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,ensure_ascii=False),flush=True)
