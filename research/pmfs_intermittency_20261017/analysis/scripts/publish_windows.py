"""Publish only this owned evidence directory, using bounded sequential packs."""
from pathlib import Path
import subprocess,shutil,json,time,sys,hashlib
R=Path(__file__).resolve().parents[1];D=R/'DELIVERY';repo=Path('D:/ZYC/UAV/.codex/worktrees/pmfs-intermittency-causal-20261017/A-gas');prefix='research/pmfs_intermittency_20261017';dest=repo/prefix;branch='codex/pmfs-intermittency-evidence-20261017';logs=[]
def git(*args,timeout=420):
 for attempt in range(3 if args[0] in ['push','ls-remote'] else 1):
  t=time.time();q=subprocess.run(['git','-c','core.longpaths=true','-c','gc.auto=0','-c','maintenance.auto=false','-c','http.version=HTTP/1.1','-c','http.lowSpeedLimit=1000','-c','http.lowSpeedTime=60',*args],cwd=repo,capture_output=True,text=True,timeout=timeout);logs.append(dict(command=list(args),returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.time()-t));(R/'logs/GIT_PUBLICATION.json').write_text(json.dumps(logs,indent=2))
  if q.returncode==0:return q.stdout.strip()
  if attempt<2:time.sleep(5*(attempt+1))
 raise RuntimeError((args,q.stderr))
assert git('branch','--show-current')==branch
assert git('remote','get-url','origin')=='https://github.com/kris-yun/uav-gsl-isj.git'
status=git('status','--porcelain','--untracked-files=all');assert all(v[3:].startswith(prefix+'/') for v in status.splitlines()),'Only this owned evidence tree may exist.'
git('merge-base','--is-ancestor','90067e72a9ce1f76759598727c8e4c3065f11246','HEAD')
(D/'.gitattributes').write_bytes(b'* -text\n')
manifest={p.relative_to(D).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'};(D/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))
dest.parent.mkdir(exist_ok=True);shutil.copytree(D,dest,dirs_exist_ok=True)
files=[p for p in dest.rglob('*') if p.is_file()];groups=[];group=[];size=0
for p in sorted(files):
 n=p.stat().st_size;assert n<40*1024**2
 if group and size+n>40*1024**2:groups.append(group);group=[];size=0
 group.append(p.relative_to(repo).as_posix());size+=n
if group:groups.append(group)
for i,group in enumerate(groups,1):
 paths=R/'git_stage_paths.nul';paths.write_bytes(b'\0'.join(n.encode('utf8') for n in group)+b'\0');git('add','-f','--pathspec-from-file='+str(paths),'--pathspec-file-nul');names=git('diff','--cached','--name-only').splitlines()
 if not names:continue
 assert all(n.startswith(prefix+'/') for n in names)
 git('commit','-m',f'Archive PMFS intermittent-observation causal audit ({i}/{len(groups)})')
 head=git('rev-parse','HEAD');print('COMMIT',i,len(groups),head,flush=True)
 git('push','-u','origin',f'HEAD:refs/heads/{branch}')
 remote=git('ls-remote','--heads','origin',branch).split()[0];assert remote==head;print('REMOTE_VERIFIED',i,head,flush=True)
head=git('rev-parse','HEAD');assert not git('diff','--name-only','90067e72a9ce1f76759598727c8e4c3065f11246','HEAD','--',':(exclude)'+prefix)
receipt=dict(status='PUSHED_AND_REMOTE_SHA_VERIFIED',branch=branch,commit=head,base='90067e72a9ce1f76759598727c8e4c3065f11246',groups=len(groups),url=f'https://github.com/kris-yun/uav-gsl-isj/tree/{head}/{prefix}',bytes=sum(p.stat().st_size for p in files));(R/'GITHUB_PUBLICATION.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
