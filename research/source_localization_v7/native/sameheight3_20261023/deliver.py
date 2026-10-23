"""Full bounded evidence ZIP including all eight new native gas archives."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile,shutil
from protocol import PROJECT,OUT,sha,write
DEST=Path('D:/ZYC/A-gas/_deliverables')
NAME='V7_SAME_HEIGHT_THREE_SOURCE_MIRROR_TEST_20261023'

def package():
 DEST.mkdir(exist_ok=True);zip_path=DEST/(NAME+'.zip')
 assert not zip_path.exists();assert shutil.disk_usage(DEST).free>=2147483648
 assert json.loads((OUT/'INDEPENDENT_QA.json').read_text())['status'].startswith('PASS_')
 files=[];skip={'.venv','local_assets','__pycache__','.pytest_cache','.git','scratch'}
 for base,dirs,names in os.walk(PROJECT):
  dirs[:]=sorted(d for d in dirs if d not in skip)
  for n in sorted(names):
   p=Path(base)/n;rel=p.relative_to(PROJECT)
   if p.suffix in ('.obj','.lib','.exp'):continue
   if len(rel.parts)==1 and n.endswith('.log'):continue
   files.append(p)
 entries={p.relative_to(PROJECT).as_posix():sha(p) for p in files}
 receipt={'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
 'branch':subprocess.check_output(['git','branch','--show-current'],cwd=PROJECT,text=True).strip(),
 'parent_commit':'7fdcf236e60debaf4cab344c6771d431ec3af5bf','payloads':len(entries),
 'new_gas_worlds':8,'all_new_raw_archives_included':True,'original_A_raw_worlds_duplicated':False,
 'shared_wind_one_copy_included':True,'original_generator_ELF_included':True,
 'original_O24_or_M1_modified':False,'new_robot_ROS_closed_loops':0,'M2_M3_runs':0,
 'no_additional_DEV_pair_or_window_queried':True,'next_mirror_proposal_not_executed':True}
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:
   z.write(p,NAME+'/'+p.relative_to(PROJECT).as_posix(),compress_type=zipfile.ZIP_STORED if p.name.endswith('.tar.gz') else zipfile.ZIP_DEFLATED)
  z.writestr(NAME+'/MANIFEST_SHA256.json',json.dumps(entries,indent=2))
  z.writestr(NAME+'/DELIVERY_RECEIPT.json',json.dumps(receipt,indent=2))
 receipt.update(zip_path=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path))
 (DEST/(NAME+'.receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (DEST/(NAME+'.sha256')).write_text(receipt['zip_sha256']+'  '+zip_path.name+'\n',encoding='ascii')
 (DEST/(NAME+'_中文报告.md')).write_bytes((PROJECT/'SAME_HEIGHT_THREE_SOURCE_REPORT_zh.md').read_bytes())
 # The compact Pro package retains every scored response, protocol, model,
 # full-world metadata and executable replay; only large physical snapshots
 # and the duplicate runtime/input blobs stay in the full companion ZIP.
 compact=DEST/(NAME+'_PRO_COMPACT.zip');assert not compact.exists()
 small=[p for p in files if '/raw_archives/' not in '/'+p.relative_to(PROJECT).as_posix()
  and '/native_generator/' not in '/'+p.relative_to(PROJECT).as_posix()
  and not ('/shared_inputs/' in '/'+p.relative_to(PROJECT).as_posix() and p.name.startswith('wind_iteration_'))]
 small_entries={p.relative_to(PROJECT).as_posix():sha(p) for p in small}
 with zipfile.ZipFile(compact,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in small:z.write(p,NAME+'/'+p.relative_to(PROJECT).as_posix())
  z.writestr(NAME+'/MANIFEST_SHA256.json',json.dumps(small_entries,indent=2))
  z.writestr(NAME+'/DELIVERY_RECEIPT.json',json.dumps({**receipt,'package_kind':'compact_scored_evidence',
   'payloads':len(small),'all_new_raw_archives_included':False,'shared_wind_one_copy_included':False,
   'original_generator_ELF_included':False,'full_companion_zip':zip_path.name},indent=2))
 with zipfile.ZipFile(compact) as z:
  assert z.testzip() is None
  for name,h in small_entries.items():assert hashlib.sha256(z.read(NAME+'/'+name)).hexdigest()==h
 (DEST/(NAME+'_PRO_COMPACT.receipt.json')).write_text(json.dumps({'zip_path':str(compact),
  'zip_sha256':sha(compact),'zip_bytes':compact.stat().st_size,'payloads':len(small),'SHA_verification':'PASS'},indent=2)+'\n',encoding='utf8')
 print('COMPACT_PRO_READY',compact.stat().st_size,sha(compact))
 print(json.dumps(receipt,ensure_ascii=False,indent=2))

def verify():
 zip_path=DEST/(NAME+'.zip');root=DEST/('_qa_'+NAME);assert not root.exists();root.mkdir()
 with zipfile.ZipFile(zip_path) as z:
  assert z.testzip() is None
  entries=json.loads(z.read(NAME+'/MANIFEST_SHA256.json'))
  for n in z.namelist():assert (root/n).resolve().is_relative_to(root.resolve())
  # Hash all payloads, including native gas tar files. Extract the small
  # runnable evidence only; raw files are already SHA-audited and need not
  # consume a second ~300MB QA directory.
  for n,h in entries.items():
   digest=hashlib.sha256()
   with z.open(NAME+'/'+n) as f:
    for b in iter(lambda:f.read(1<<20),b''):digest.update(b)
   assert digest.hexdigest()==h,n
   if '/raw_archives/' not in n:z.extract(NAME+'/'+n,root)
  for n in ('MANIFEST_SHA256.json','DELIVERY_RECEIPT.json'):z.extract(NAME+'/'+n,root)
 project=root/NAME;commands=[]
 for name in ('verify.py','degeneracy.py','portable_score_replay.py'):
  cmd=[sys.executable,str(project/'native/sameheight3_20261023'/name)]
  p=subprocess.run(cmd,cwd=project,capture_output=True,text=True)
  (root/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
  commands.append({'command':cmd,'exit_code':p.returncode,'output':p.stdout.strip()})
 receipt={'status':'PASS_FULL_PAYLOAD_HASH_AND_FRESH_SMALL_EVIDENCE_REPLAY','payloads':len(entries),
 'zip_sha256':sha(zip_path),'commands':commands,'raw_archives_all_hashed_but_not_duplicated_into_QA':True}
 (DEST/(NAME+'.fresh_qa.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
 if sys.argv[1:]==['package']:package()
 elif sys.argv[1:]==['verify']:verify()
 else:raise SystemExit('package|verify')
