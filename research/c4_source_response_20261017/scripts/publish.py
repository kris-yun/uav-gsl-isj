"""Publish only this research snapshot with a private index; never checkout or modify the user's index."""
from pathlib import Path
import subprocess,os,json,hashlib,time
R=Path(__file__).resolve().parents[1];repo=R.parent.parent
B=Path(r'C:\Users\50176\Downloads\C4_PRO_REVIEW_20261017');archive=B.with_name('C4_SOURCE_RESPONSE_ATTRIBUTION_20261017_VERIFIED.zip')
T=Path(r'C:\Users\50176\Downloads\D_DRIVE_SPACE_AUDIT_20261017');idx=T/'c4_publication.index';assert not idx.exists()
branch='codex/c4-source-response-20261017';prefix='research/c4_source_response_20261017/'
base='90067e72a9ce1f76759598727c8e4c3065f11246';env=dict(os.environ,GIT_INDEX_FILE=str(idx));commands=[]
def git(args,input=None,binary=False):
 cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','http.version=HTTP/1.1',*args]
 q=subprocess.run(cmd,cwd=repo,env=env,input=input,capture_output=True)
 commands.append(dict(command=cmd,exit_code=q.returncode,stderr=q.stderr.decode('utf-8','replace')[:8000]));(R/'PUBLICATION_COMMANDS.json').write_text(json.dumps(commands,indent=2))
 if q.returncode:raise RuntimeError(q.stderr.decode('utf-8','replace'))
 return q.stdout if binary else q.stdout.decode('utf-8').strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)==json.loads((R/'PACKAGE_VERIFY.json').read_text())['sha256']
remote=git(['ls-remote','origin','refs/heads/master']);assert remote.split()[0]==base,remote
assert not git(['ls-remote','origin','refs/heads/'+branch]),'Research branch already exists'
git_index=repo/'.git/index';index_before=sha(git_index);head_before=git(['rev-parse','HEAD'])
git(['read-tree',base])
parts=[]
with archive.open('rb') as src:
 number=0
 while block:=src.read(32*1024**2):
  p=T/(archive.name+f'.part{number:02d}');assert not p.exists();p.write_bytes(block)
  parts.append(dict(path='evidence/'+p.name,bytes=len(block),sha256=sha(p),local=str(p)));number+=1
parts_manifest=T/'C4_ARCHIVE_PARTS.json';parts_manifest.write_text(json.dumps(dict(filename=archive.name,total_bytes=archive.stat().st_size,whole_sha256=sha(archive),parts=[{k:v for k,v in p.items() if k!='local'} for p in parts]),indent=2))
selected={prefix+p['path']:Path(p['local']) for p in parts}
selected[prefix+'evidence/ARCHIVE_PARTS.json']=parts_manifest
selected[prefix+'evidence/'+archive.with_suffix('.zip.sha256').name]=archive.with_suffix('.zip.sha256')
assembler=R/'scripts/assemble_archive.py';selected[prefix+'assemble_archive.py']=assembler
readme=T/'c4_GITHUB_README.md';readme.write_text('# C4 source-response attribution\n\nHOLD: ordinary source refinement did not restore final C4 discrimination. Temporal convergence and observation-event/3D effects remain unseparated. No new ROS loops or gas worlds.\n\nRead `科学裁决_zh.md` and `results/FINAL_DECISION.json`. Full source/history/maps and all failures are in two lossless archive parts under `evidence/`. Run `python assemble_archive.py` in this directory to verify both part hashes and reconstruct the original upload ZIP. Then extract it and use its `reproduce.py`. The direct user download is a single ZIP; splitting is only for bounded GitHub uploads.\n','utf-8');selected[prefix+'README.md']=readme
for folder in ['code','readout_code','scripts','lineage']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:selected[prefix+p.relative_to(R).as_posix()]=p
for name in ['README_zh.md','科学裁决_zh.md','FROZEN_PLAN.json','POSTHOC_ORACLE_PLAN.json','EXECUTION.json','ORACLE_EXECUTION.json','PACKAGE_VERIFY.json']:
 selected[prefix+name]=R/name
for p in (R/'results').rglob('*'):
 if p.is_file() and p.suffix in ['.json','.csv'] and not any(s.startswith(('predictions','parity','oracle_')) for s in p.relative_to(R/'results').parts[:-1]):
  selected[prefix+p.relative_to(R).as_posix()]=p
for p in (R/'logs').glob('*'):
 if p.is_file() and p.stat().st_size<200000:selected[prefix+p.relative_to(R).as_posix()]=p
paths=sorted(selected)
blobs=git(['hash-object','-w','--no-filters','--stdin-paths'],input=('\n'.join(str(selected[p]) for p in paths)+'\n').encode('utf-8')).splitlines()
assert len(blobs)==len(paths)
blobmap=dict(zip(paths,blobs));errors=[];packs=[];commits=[];previous=base
partpaths=[prefix+p['path'] for p in parts]
for number,partpath in enumerate(partpaths):
 stage=([p for p in paths if p not in partpaths]+[partpath]) if number==0 else [partpath]
 git(['update-index','-z','--index-info'],input=b''.join(('100644 '+blobmap[p]+'\t'+p+'\0').encode('utf-8') for p in stage))
 tree=git(['write-tree']);body=T/f'c4_commit_message_{number}.txt';body.write_text(f'Preserve C4 forward attribution and bounded evidence part {number+1}/{len(parts)}\n\nFixed histories, native kernels, ordinary controls and all counterexamples. HOLD: no task benefit or main innovation established.\n','utf-8')
 commit=git(['commit-tree',tree,'-p',previous,'-F',str(body)]);commits.append(commit)
 assert all(p.startswith(prefix) for p in git(['diff','--name-only',previous,commit]).splitlines())
 pack=T/f'c4_push_preview_{number}.pack'
 with pack.open('wb') as out:q=subprocess.run(['git','-c','gc.auto=0','pack-objects','--stdout','--revs'],cwd=repo,env=env,input=(commit+'\n^'+previous+'\n').encode(),stdout=out,stderr=subprocess.PIPE)
 assert q.returncode==0,q.stderr
 assert pack.stat().st_size<40*1024**2,pack.stat().st_size
 packs.append(pack.stat().st_size);git(['update-ref','refs/heads/'+branch,commit,'0'*40 if number==0 else previous])
 for attempt in range(3):
  try:git(['push','--porcelain','origin',commit+':refs/heads/'+branch]);break
  except RuntimeError as e:
   errors.append(str(e))
   if attempt==2:raise
   time.sleep(2)
 assert git(['ls-remote','origin','refs/heads/'+branch]).split()[0]==commit
 previous=commit
assert sha(git_index)==index_before and git(['rev-parse','HEAD'])==head_before
# Read the actual committed blob rather than inferring success from push output alone.
for p in partpaths:assert git(['rev-parse',commit+':'+p])==blobmap[p]
receipt=dict(status='PASS_PUSHED_AND_REMOTE_COMMIT_VERIFIED',branch=branch,commit=commit,commits=commits,base=base,files=len(paths),pack_bytes=packs,archive_sha256=sha(archive),archive_parts=parts,root_head_and_index_unchanged=True,push_errors_retained=errors,url='https://github.com/kris-yun/uav-gsl-isj/tree/'+commit+'/'+prefix.rstrip('/'))
(R/'PUBLICATION.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
