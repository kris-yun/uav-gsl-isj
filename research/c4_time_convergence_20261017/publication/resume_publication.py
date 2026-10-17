from pathlib import Path
import hashlib,json,os,subprocess,time
T=Path(__file__).resolve().parent;R=T.parent/'C4H17';repo=T.parent.parent
branch='codex/c4-time-convergence-20261017';prefix='research/c4_time_convergence_20261017/'
env=dict(os.environ,GIT_INDEX_FILE=str(T/'private.index'));commands=json.loads((R/'PUBLICATION_COMMANDS.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(args,input=None,binary=False,check=True):
 cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','http.version=HTTP/1.1','-c','core.quotepath=false',*args]
 q=subprocess.run(cmd,cwd=repo,env=env,input=input,capture_output=True)
 commands.append(dict(command=cmd,exit_code=q.returncode,stderr=q.stderr.decode('utf-8','replace')[:8000]))
 (R/'PUBLICATION_COMMANDS.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2),encoding='utf-8')
 if check and q.returncode:raise RuntimeError(q.stderr.decode('utf-8','replace'))
 return q.stdout if binary else q.stdout.decode('utf-8').strip()
def push(commit):
 for attempt in range(3):
  try:
   git(['push','--porcelain','origin',commit+':refs/heads/'+branch]);break
  except RuntimeError:
   if attempt==2:raise
   time.sleep(2)
 assert git(['ls-remote','origin','refs/heads/'+branch]).split()[0]==commit
head=git(['rev-parse','HEAD']);assert head=='126f786a42c2cbe9a7b03b43a5edda5231d872a7'
index_sha=sha(repo/'.git/index');first='665f5b495579f535621cd8e1c32ac1c47925b743'
base=git(['rev-parse',first+'^']);current=git(['rev-parse','refs/heads/'+branch])
assert current==first
assert git(['write-tree'])==git(['rev-parse',current+'^{tree}'])
assert git(['ls-remote','origin','refs/heads/'+branch]).split()[0]==first
manifest=json.loads((T/'ARCHIVE_PARTS.json').read_text(encoding='utf-8'))
commits=[first];packs=[(T/'preview_0.pack').stat().st_size]
for i,a in enumerate(manifest['parts'][1:],1):
 p=T/Path(a['path']).name;assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
 blob=git(['hash-object','-w','--no-filters',str(p)])
 path=prefix+a['path'];git(['update-index','-z','--index-info'],input=('100644 '+blob+'\t'+path+'\0').encode('utf-8'))
 tree=git(['write-tree']);body=T/f'commit_{i}.txt';body.write_text(f'Complete C4 time-convergence bounded evidence part {i+1}/3\n\nFrozen data, unchanged native kernels, HOLD convergence unresolved.\n',encoding='utf-8')
 commit=git(['commit-tree',tree,'-p',current,'-F',str(body)])
 assert all(x.startswith(prefix) for x in git(['diff','--name-only',current,commit]).splitlines())
 pack=T/f'preview_{i}.pack'
 with pack.open('wb') as out:q=subprocess.run(['git','-c','gc.auto=0','pack-objects','--stdout','--revs'],cwd=repo,env=env,input=(commit+'\n^'+current+'\n').encode(),stdout=out,stderr=subprocess.PIPE)
 assert q.returncode==0 and pack.stat().st_size<40*1024**2
 packs.append(pack.stat().st_size);git(['update-ref','refs/heads/'+branch,commit,current]);push(commit)
 commits.append(commit);current=commit;print('PUSHED_PART',i+1,commit,flush=True)
whole=hashlib.sha256()
for a in manifest['parts']:
 data=git(['show',current+':'+prefix+a['path']],binary=True)
 assert len(data)==a['bytes'] and hashlib.sha256(data).hexdigest()==a['sha256'];whole.update(data)
assert whole.hexdigest()==manifest['whole_sha256']
data_commit=current
network=T/'NETWORK_RECOVERY.json';network.write_text(json.dumps(dict(initial_failure='schannel TLS handshake failed before first push; preserved in PUBLICATION_COMMANDS.json',same_commit_retry='Succeeded pushing 665f5b495579f535621cd8e1c32ac1c47925b743',data_commit=data_commit,archive_sha256=whole.hexdigest(),all_three_committed_parts_verified=True),indent=2),encoding='utf-8')
for local,path in [(network,prefix+'publication/NETWORK_RECOVERY.json'),(Path(__file__),prefix+'publication/resume_publication.py')]:
 blob=git(['hash-object','-w','--no-filters',str(local)]);git(['update-index','-z','--index-info'],input=('100644 '+blob+'\t'+path+'\0').encode())
tree=git(['write-tree']);body=T/'receipt_commit.txt';body.write_text('Record verified C4 evidence publication and transient network recovery\n',encoding='utf-8')
receipt_commit=git(['commit-tree',tree,'-p',current,'-F',str(body)])
git(['update-ref','refs/heads/'+branch,receipt_commit,current]);push(receipt_commit)
assert sha(repo/'.git/index')==index_sha and git(['rev-parse','HEAD'])==head
result=dict(status='PASS_COMPLETE_REMOTE_BRANCH_AND_WHOLE_ARCHIVE_VERIFIED',branch=branch,base=base,commit=receipt_commit,data_commit=data_commit,commits=commits+[receipt_commit],pack_bytes=packs,
 archive_sha256=whole.hexdigest(),archive_bytes=manifest['total_bytes'],all_parts_committed_SHA_verified=True,root_head_preserved=head,root_index_SHA_unchanged_during_recovery=True,
 url='https://github.com/kris-yun/uav-gsl-isj/tree/'+receipt_commit+'/'+prefix.rstrip('/'))
(R/'PUBLICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
