"""Checkpointed, serial 12-run screen; never changes parameters after outcomes."""
from pathlib import Path
import csv,datetime,hashlib,json,os,shutil,subprocess,sys,time,traceback,zipfile
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from analyze_completed_case import analyze
from summarize_screen12 import summarize
P=R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json';plan=json.loads(P.read_text());initial_hash=hashlib.sha256(P.read_bytes()).hexdigest();archives=Path(plan['archive_destination']);archives.mkdir(parents=True,exist_ok=True);key='C:/Users/50176/.ssh/id_ed25519_vm';ssh=['ssh','-i',key,'-o','BatchMode=yes','-o','ConnectTimeout=8','zyc@192.168.111.128'];G='/mnt/hgfs/workspace/'+R.name
def put(p,x):
 temp=p.with_suffix(p.suffix+'.writing');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(temp,p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def archive(role,C):
 receipt=C/'ARCHIVE_RECEIPT.json'
 if receipt.exists():
  old=json.loads(receipt.read_text());assert sha(old['archive'])==old['archive_sha256'];return old
 dst=archives/((C.name if C.name!=role else role)+'_FULL.zip');assert not dst.exists();files=[p for p in C.rglob('*')if p.is_file()and p.name not in ['ARCHIVE_RECEIPT.json','ARCHIVE_PRUNE_PLAN.json','ARCHIVE_PRUNE_RECEIPT.json']];manifest=[dict(path=p.relative_to(C).as_posix(),bytes=p.stat().st_size,sha256=sha(p))for p in files];temp=dst.with_suffix('.zip.partial')
 with zipfile.ZipFile(temp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)as z:
  for p in files:z.write(p,p.relative_to(C).as_posix())
  z.writestr('ARCHIVE_MANIFEST_SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(temp)as z:
  for x in manifest:
   h=hashlib.sha256()
   with z.open(x['path'])as f:
    for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
   assert h.hexdigest()==x['sha256'],x['path']
 os.replace(temp,dst);record=dict(status='PASS_FULL_MEMBER_SHA_ROUNDTRIP',archive=str(dst),archive_sha256=sha(dst),source_case=str(C),files=len(files),raw_bytes=sum(x['bytes']for x in manifest),archive_bytes=dst.stat().st_size,all_unique_bytes_preserved=True);put(receipt,record)
 # Only verified duplicate large runtime exports may be pruned; configs/source/ELF stay.
 if shutil.disk_usage('D:/').free<1024**3:
  targets=[x for x in manifest if x['path'].startswith('runtime/')and x['bytes']>200000 and Path(x['path']).suffix in ['.f32','.csv','.log','.jsonl','.gz','.s8']];put(C/'ARCHIVE_PRUNE_PLAN.json',dict(archive=record,files=targets,rule='Only completed case; all child processes stopped and graph vacant; complete archive member SHA verified.'))
  removed=[]
  for x in targets:
   p=(C/x['path']).resolve();assert p.is_relative_to((C/'runtime').resolve())and sha(p)==x['sha256'];p.unlink();removed.append(x)
  put(C/'ARCHIVE_PRUNE_RECEIPT.json',dict(status='VERIFIED_ARCHIVE_DUPLICATES_ONLY',archive=record,removed=removed,restore='Extract exact recorded members to source_case after SHA check; no overwrite of different files'))
 return record
def table(records):
 out=[]
 for x in records:
  q=x['QA'];t=q.get('terminal',{});out.append(dict(role=x['role'],case=q['case'],qualification=q['qualification'],official_success=q.get('official_success'),stop_reason=q.get('stop_reason'),source_domain=q.get('source_domain_class','UNKNOWN'),Top5_error_m=t.get('Top5_error_m'),MAP_error_m=t.get('MAP_error_m'),mean_error_m=t.get('mean_error_m'),variance_m2=t.get('variance_m2'),true_rank=t.get('true_rank'),search_physical_s=q.get('search_physical_s'),search_wall_s=q.get('search_wall_s'),consumed_windows=q.get('consumed_windows'),positive_windows=q.get('positive_windows'),archive=x['archive']['archive'],independent_seed_claim=False))
 if out:
  temp=R/'EPISODE_RESULTS.csv.writing'
  with temp.open('w',newline='',encoding='utf-8-sig')as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
  os.replace(temp,R/'EPISODE_RESULTS.csv')
records=json.loads((R/'BATCH_LEDGER.json').read_text())if(R/'BATCH_LEDGER.json').exists()else[]
assert not(R/'BATCH_PROCESS_ACTIVE.json').exists(),'Inspect previous process identity before resuming; never launch duplicate batch'
put(R/'BATCH_PROCESS_ACTIVE.json',dict(pid=os.getpid(),started_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=initial_hash));stop=None
try:
 for role in plan['roles']:
  if any(x['role']==role['id']for x in records):continue
  assert sha(P)==initial_hash,'PREREGISTERED_PROTOCOL_CHANGED_DURING_BATCH';override=json.loads((R/'ROLE_EXECUTION_OVERRIDES_R6.json').read_text()).get(role['id'],{});C=Path(override.get('host_case',role['host_case']));put(R/'BATCH_CHECKPOINT.json',dict(stage='RUNNING'if not role['already_completed']else'ARCHIVING_VALIDATED_PILOT',completed=[x['role']for x in records],current=role['id'],total=12,host_free=shutil.disk_usage('D:/').free))
  if shutil.disk_usage('D:/').free<768*1024**2 or shutil.disk_usage('C:/').free<1024**3:raise RuntimeError('RESOURCE_PAUSE_KEEP_UNIQUE_EVIDENCE')
  if not role['already_completed']:
   assert sha(C/'CASE_META.json')==override.get('parameter_sha256',role['parameter_sha256']);assert sha(C/'PHYSICAL_FRAME_TIME.csv')==override.get('timeline_sha256',role['timeline_sha256'])
   if not(C/'EXECUTION_COMPLETE.json').exists():
    assert not(C/'EXECUTION_STARTED.json').exists(),'Interrupted role requires explicit owner/checkpoint recovery; do not duplicate a goal'
    with(C/'HOST_SSH_OUTPUT.log').open('wb')as f:q=subprocess.run([*ssh,'python3',G+'/run_case_guest_R6.py',role['id']],stdout=f,stderr=subprocess.STDOUT,timeout=1400)
    if q.returncode!=0:raise RuntimeError('GUEST_RUN_OR_INPUT_GATE_FAILED:'+role['id'])
   with(C/'CPP_QA_COMMAND.log').open('wb')as f:q=subprocess.run([*ssh,'python3',G+'/code/verify_cpp_readout_guest.py',override.get('shared_case',role['shared_case'])],stdout=f,stderr=subprocess.STDOUT,timeout=45)
   assert q.returncode==0,'CPP_READOUT_QA_FAILED'
  try:qa=analyze(C)
  except Exception:
   put(C/'QA_FAILURE.json',dict(traceback=traceback.format_exc(),role=role['id']));a=archive(role['id'],C);raise
  a=archive(role['id'],C);records.append(dict(role=role['id'],QA=qa,archive=a));put(R/'BATCH_LEDGER.json',records);table(records);summarize()
  if not qa['qualification'].startswith('PASS'):raise RuntimeError('TECHNICAL_CASE_FAILURE_RETAINED:'+role['id'])
  if(C/'EXECUTION_COMPLETE.json').exists():
   completed=json.loads((C/'EXECUTION_COMPLETE.json').read_text());assert not completed.get('forced')and completed['binary_unchanged']
 put(R/'BATCH_CHECKPOINT.json',dict(stage='TWELVE_PREREGISTERED_SLOTS_ACCOUNTED',completed=[x['role']for x in records],total=12,full_scientific_runs=sum(x['QA']['qualification'].startswith('PASS')for x in records),technical_abort_slots=sum(not x['QA']['qualification'].startswith('PASS')for x in records),independent_seed_claim=False))
except Exception as e:
 stop=dict(stage='PAUSED_AT_CONCRETE_GATE',error=str(e),traceback=traceback.format_exc(),completed=[x['role']for x in records],last_checkpoint=json.loads((R/'BATCH_CHECKPOINT.json').read_text()));put(R/'BATCH_STOP.json',stop);print(json.dumps(stop,ensure_ascii=False),flush=True)
finally:
 summarize()
 put(R/'BATCH_PROCESS_FINISHED.json',dict(pid=os.getpid(),completed=len(records),stop=stop,ended_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()));(R/'BATCH_PROCESS_ACTIVE.json').rename(R/('BATCH_PROCESS_ENDED_'+str(os.getpid())+'.json'))
