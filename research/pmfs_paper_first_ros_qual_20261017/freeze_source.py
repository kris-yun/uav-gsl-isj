from pathlib import Path
import hashlib,json,subprocess,time,os,shutil
import requests
R=Path(__file__).resolve().parent;P=R.parents[1]
COMMIT='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533'
repo=R/'official_repo';out=R/'official_exact';out.mkdir(exist_ok=True)
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
actual=subprocess.check_output(['git','-C',str(repo),'rev-parse',COMMIT+'^{tree}'],text=True).strip();assert actual=='bbb303fa43d1f2f7a67fb76c7352e43a7e35bb0a'
raw=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',COMMIT])
entries=[];links=[]
for line in raw.split(b'\0'):
 if not line:continue
 h,n=line.split(b'\t',1);mode,kind,gitid=h.decode().split();name=n.decode()
 if kind=='commit':links.append(dict(path=name,commit=gitid));continue
 selected=name.startswith(('gsl_server/','gsl_actions/'))or name in ['.gitmodules','README.md']or(name.startswith('Environment_config/PMFS/')and Path(name).suffix in ['.yaml','.xml','.py','.pgm','.txt'])
 if selected:assert mode in ['100644','100755'],(mode,name);entries.append(dict(path=name,git_blob_oid=gitid,git_mode=mode))
roots=[P/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016/paper_baseline_2024/original',P/'_staging/FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018/source/AUTHOR_FIX_20240918',P/'workspace/PMFS_SHARED_BASELINE_AUDIT_20261017/official_sources']
cache={}
for root in roots:
 for f in root.rglob('*'):
  if f.is_file():b=f.read_bytes();cache.setdefault(oid(b),f)
session=requests.Session();receipts=[];start=time.monotonic()
for row in entries:
 target=out/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
 if row['git_blob_oid']in cache:
  src=cache[row['git_blob_oid']];b=src.read_bytes();origin='local exact-Git-blob reuse';source=str(src)
 else:
  url='https://raw.githubusercontent.com/MAPIRlab/GasSourceLocalization/'+COMMIT+'/'+row['path'];errors=[]
  for attempt in range(1,4):
   try:q=session.get(url,timeout=(8,25));q.raise_for_status();b=q.content;assert oid(b)==row['git_blob_oid'];break
   except Exception as e:
    errors.append(dict(attempt=attempt,error=repr(e)));put(R/'FETCH_ERRORS.json',errors)
    if attempt==3:raise
  origin='official pinned raw source';source=url
 assert oid(b)==row['git_blob_oid']
 if target.exists():assert target.read_bytes()==b
 else:target.write_bytes(b)
 receipts.append(dict(**row,sha256=sha(b),bytes=len(b),origin=origin,source=source))
 put(R/'SOURCE_FETCH_PROGRESS.json',dict(completed=len(receipts),planned=len(entries),last=row['path'],elapsed_s=time.monotonic()-start))
put(R/'SOURCE_LOCK.json',dict(status='PASS_COMPLETE_SELECTED_SERVER_ACTIONS_PMFS_CONFIG_BLOBS',commit=COMMIT,tree=actual,files=receipts,gitlinks=links,bytes=sum(x['bytes']for x in receipts),downloaded_files=sum(x['origin'].startswith('official')for x in receipts),local_reused_files=sum(x['origin'].startswith('local')for x in receipts),wall_s=time.monotonic()-start,source_scope='Complete gsl_server and gsl_actions committed files; PMFS yaml/xml/py/pgm/txt assets; gitlinks separately fixed. Large worlds are existing independently qualified data.'))
print(json.dumps(dict(status='SOURCE_LOCK_PASS',files=len(receipts),downloaded=sum(x['origin'].startswith('official')for x in receipts),wall_s=time.monotonic()-start)),flush=True)
