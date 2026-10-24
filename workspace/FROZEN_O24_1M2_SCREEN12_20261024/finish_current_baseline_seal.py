"""Resume the metadata seal after a Windows argument-length packaging failure."""
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess,sys,zipfile
BASE=Path(__file__).resolve().parent
REPO=BASE.parent.parent
FREEZE=REPO/'workspace/FROZEN_O24_1M2_SCREEN12_20261024'
METHOD=REPO/'workspace/METHOD_COMPARISON_O24_1M2_20261024'
DOWNLOADS=Path('C:/Users/50176/Downloads')
def sha(b):return hashlib.sha256(b).hexdigest()
assert FREEZE.is_dir() and METHOD.is_dir()
lock=json.loads((FREEZE/'BASELINE_LOCK.json').read_text(encoding='utf-8'))
for name in ['freeze_current_baseline.py','finish_current_baseline_seal.py']:
 shutil.copyfile(BASE/name,FREEZE/name)
files=[]
for p in sorted(FREEZE.rglob('*')):
 if p.is_file() and p.name!='FREEZE_MANIFEST_SHA256.json':
  b=p.read_bytes();files.append({'path':p.relative_to(FREEZE).as_posix(),'bytes':len(b),'sha256':sha(b)})
(FREEZE/'FREEZE_MANIFEST_SHA256.json').write_text(json.dumps({'freeze_identity':lock['freeze_identity'],'scope':'All frozen files except this self-referential manifest; no method output in freeze','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
verify=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py')],check=True,text=True,capture_output=True)
bad=BASE/'freeze_negative_controls/WRONG_STOP_1P5.json'
neg=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py'),'--method-manifest',str(bad)],text=True,capture_output=True)
assert neg.returncode==2 and 'STOP_PROTOCOL_MISMATCH' in neg.stderr
pending=subprocess.run([sys.executable,str(FREEZE/'verify_frozen_baseline.py'),'--method-manifest',str(METHOD/'METHOD_SUBMISSION_TEMPLATE.json')],text=True,capture_output=True)
assert pending.returncode==2 and 'METHOD_NOT_SUBMITTED_AND_FROZEN' in pending.stderr
index_file=BASE/'freeze_git_index'
env=dict(os.environ,GIT_INDEX_FILE=str(index_file))
def git(*args,**kw):return subprocess.run(['git',*args],cwd=REPO,env=env,text=True,capture_output=True,check=True,**kw).stdout.strip()
parent='120bb2e833bfc6aa96a356101203570b476b6b9f'
git('read-tree',parent)
tracked=[p.relative_to(REPO).as_posix() for p in FREEZE.rglob('*') if p.is_file() and 'payload' not in p.relative_to(FREEZE).parts and 'binaries' not in p.relative_to(FREEZE).parts]
pathspec=BASE/'freeze_git_pathspec.nul'
pathspec.write_bytes(b'\0'.join(p.encode('utf-8') for p in tracked)+b'\0')
git('add','-f','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
tree=git('write-tree')
commit=git('commit-tree',tree,'-p',parent,input='Freeze O24 actual source/config and SCREEN12 evidence under 1m2 declaration protocol\n')
branch='research/o24-1m2-frozen-20261024';tag='freeze/o24-1m2-screen12-20261024'
git('update-ref','refs/heads/'+branch,commit,'0'*40)
git('update-ref','refs/tags/'+tag,commit,'0'*40)
gr={'status':'LOCAL_FREEZE_COMMIT_AND_TAG_NO_CHECKOUT','commit':commit,'branch':branch,'tag':tag,'parent_evidence_commit':parent,'active_worktree_and_index_unchanged':True,'payload_binary_archive_identity_recorded_not_git_uploaded':True}
(BASE/'FROZEN_1M2_GIT_RECEIPT.json').write_text(json.dumps(gr,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in FREEZE.rglob('*'):
 if p.is_file():os.chmod(p,stat.S_IREAD)
archive=DOWNLOADS/'O24_1M2_SCREEN12_FROZEN_BASELINE_20261024.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(FREEZE.rglob('*')):
  if p.is_file():z.write(p,'baseline/'+p.relative_to(FREEZE).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix=='.zip' else zipfile.ZIP_DEFLATED)
 z.writestr('GIT_FREEZE_RECEIPT.json',json.dumps(gr,ensure_ascii=False,indent=2))
 z.writestr('VERIFY_RECEIPT.txt',verify.stdout)
qa=BASE/'freeze_portable_qa';assert not qa.exists();qa.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;z.extractall(qa)
fresh=subprocess.run([sys.executable,str(qa/'baseline/verify_frozen_baseline.py')],text=True,capture_output=True,check=True)
receipt={'status':'FROZEN_AND_ISOLATED_PASS','freeze_identity':lock['freeze_identity'],'canonical_baseline':str(FREEZE),'separate_method_workspace':str(METHOD),'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'manifest_files':len(files),'freeze_git':gr,'verify_stdout':verify.stdout,'fresh_unzip_verify_stdout':fresh.stdout,'wrong_1p5_stop_rejected':True,'unsubmitted_method_rejected':True,'canonical_files_readonly':all(not(p.stat().st_mode & stat.S_IWRITE) for p in FREEZE.rglob('*') if p.is_file()),'new_builds':0,'new_ROS_runs':0,'new_worlds':0}
(BASE/'FROZEN_1M2_DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+archive.name+'\n',encoding='ascii')
archive.with_suffix('.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
