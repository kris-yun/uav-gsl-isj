"""Bounded research-only Git publication; preserve root HEAD/index exactly."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];repo=R.parent.parent
T=R.parent/'C4H17_PUBLISH_SCRATCH';T.mkdir(exist_ok=False)
index=T/'private.index';branch='codex/c4-time-convergence-20261017';prefix='research/c4_time_convergence_20261017/'
package=json.loads((R/'PACKAGE_VERIFY.json').read_text(encoding='utf-8'));archive=Path(package['archive'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)==package['sha256']
env=dict(os.environ,GIT_INDEX_FILE=str(index));commands=[]
def git(args,input=None,binary=False):
    cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','http.version=HTTP/1.1','-c','core.quotepath=false',*args]
    q=subprocess.run(cmd,cwd=repo,env=env,input=input,capture_output=True)
    commands.append(dict(command=cmd,exit_code=q.returncode,stderr=q.stderr.decode('utf-8','replace')[:8000]))
    (R/'PUBLICATION_COMMANDS.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2),encoding='utf-8')
    if q.returncode:raise RuntimeError(q.stderr.decode('utf-8','replace'))
    return q.stdout if binary else q.stdout.decode('utf-8').strip()
base=git(['ls-remote','origin','refs/heads/master']).split()[0]
assert not git(['ls-remote','origin','refs/heads/'+branch]),'Existing branch: do not overwrite'
head=git(['rev-parse','HEAD']);root_index=repo/'.git/index';index_sha=sha(root_index)
git(['read-tree',base])
parts=[]
with archive.open('rb') as f:
    number=0
    while block:=f.read(24*1024**2):
        p=T/(archive.name+f'.part{number:02}');p.write_bytes(block)
        parts.append(dict(path='evidence/'+p.name,bytes=len(block),sha256=sha(p),local=str(p)));number+=1
manifest=T/'ARCHIVE_PARTS.json';manifest.write_text(json.dumps(dict(filename=archive.name,total_bytes=archive.stat().st_size,whole_sha256=package['sha256'],parts=[{k:v for k,v in p.items() if k!='local'} for p in parts]),indent=2),encoding='utf-8')
selected={prefix+p['path']:Path(p['local']) for p in parts}
selected[prefix+'evidence/ARCHIVE_PARTS.json']=manifest
selected[prefix+'assemble_archive.py']=R/'scripts/assemble_archive.py'
for folder in ['code','scripts','lineage','analysis','logs']:
    for p in (R/folder).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        # All bulky raw/failure states remain losslessly inside archive parts.
        if folder=='lineage' and any(a in p.parts for a in ['INTERRUPTED_C4u1_W360_state2','ONE_CALL_RECOVERY']):continue
        if p.suffix in ['.f32','.gz','.bin','.u32']:continue
        selected[prefix+p.relative_to(R).as_posix()]=p
for name in ['README_zh.md','科学裁决_zh.md','FINAL_DECISION.json','FROZEN_PLAN.json','INPUT_MANIFEST_SHA256.json','EXECUTION.json','CONTRASTS_COMPLETE.json','RUN_ORIGIN.json','PACKAGE_VERIFY.json','diagnostic.cpp','reproduce.py']:
    selected[prefix+name]=R/name
readme=T/'README.md';readme.write_text('# C4 native 2D time-convergence audit\n\nHOLD_CONVERGENCE_UNRESOLVED. Longer native warmup produces distant receptor responses, so earlier near-zero values do not establish missing 2D paths. The true source still loses every frozen final C4 pair comparison; response/population remain nonstationary at 360 seconds. C3 counterexamples retained. No new posterior, ROS, gas world, module or task gain.\n\nRead 科学裁决_zh.md and FINAL_DECISION.json. Run `python assemble_archive.py` here to verify bounded parts and reconstruct the self-contained verified ZIP. Extract it and use `python reproduce.py --verify-only` or `--analysis-out NEW`. An explicitly requested full offline rerun is also supported. All 1092 valid results, one incomplete driver-interrupted start, 27 retained source results and one same-state technical recovery are preserved. The proposed next diagnostic has not been run.\n',encoding='utf-8')
selected[prefix+'README.md']=readme
paths=sorted(selected);blobs=git(['hash-object','-w','--no-filters','--stdin-paths'],input=('\n'.join(str(selected[p]) for p in paths)+'\n').encode('utf-8')).splitlines();assert len(paths)==len(blobs)
mapping=dict(zip(paths,blobs));partpaths=[prefix+p['path'] for p in parts];previous=base;commits=[];sizes=[]
for number,part in enumerate(partpaths):
    stage=([p for p in paths if p not in partpaths]+[part]) if number==0 else [part]
    git(['update-index','-z','--index-info'],input=b''.join(('100644 '+mapping[p]+'\t'+p+'\0').encode('utf-8') for p in stage))
    tree=git(['write-tree']);body=T/f'commit_{number}.txt';body.write_text(f'Preserve bounded C4 time-convergence evidence part {number+1}/{len(parts)}\n\nLonger warmup affects response but final source-pair discrimination remains negative. Convergence unresolved; no task-gain or innovation claim. All counterexamples and driver recovery preserved.\n',encoding='utf-8')
    commit=git(['commit-tree',tree,'-p',previous,'-F',str(body)])
    assert all(p.startswith(prefix) for p in git(['diff','--name-only',previous,commit]).splitlines())
    pack=T/f'preview_{number}.pack'
    with pack.open('wb') as out:
        q=subprocess.run(['git','-c','gc.auto=0','pack-objects','--stdout','--revs'],cwd=repo,env=env,input=(commit+'\n^'+previous+'\n').encode(),stdout=out,stderr=subprocess.PIPE)
    assert q.returncode==0,q.stderr
    assert pack.stat().st_size<40*1024**2,pack.stat().st_size
    sizes.append(pack.stat().st_size);commits.append(commit)
    git(['update-ref','refs/heads/'+branch,commit,'0'*40 if number==0 else previous])
    git(['push','--porcelain','origin',commit+':refs/heads/'+branch])
    assert git(['ls-remote','origin','refs/heads/'+branch]).split()[0]==commit
    previous=commit
assert sha(root_index)==index_sha and git(['rev-parse','HEAD'])==head
for path in partpaths:
    blob=git(['show',previous+':'+path],binary=True);a=next(a for a in parts if prefix+a['path']==path)
    assert len(blob)==a['bytes'] and hashlib.sha256(blob).hexdigest()==a['sha256']
receipt=dict(status='PASS_PUSHED_REMOTE_HEAD_AND_COMMITTED_ARCHIVE_PARTS_VERIFIED',branch=branch,base=base,commit=previous,commits=commits,pack_bytes=sizes,
             archive_sha256=package['sha256'],archive_bytes=package['bytes'],published_files=len(paths),
             root_head_and_index_unchanged=True,url='https://github.com/kris-yun/uav-gsl-isj/tree/'+previous+'/'+prefix.rstrip('/'))
(R/'PUBLICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
