from pathlib import Path
import datetime,hashlib,json,shutil,zipfile
R=Path(__file__).resolve().parent
W=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas')
T=W/'research/pmfs_o24_ros_qual_20261018'
D=Path(r'C:\Users\50176\Downloads')
Z=D/'PMFS_O24_ROS与随机状态验收_A2B2四回合_含隔离HOLD_20261018.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not T.exists()and not Z.exists()
T.mkdir(parents=True)
skip={'build','install','__pycache__','offline_qa'}
for p in R.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(R)
 if any(x in skip for x in rel.parts):continue
 target=T/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
P=T/'p24_reference/analysis';P.mkdir(parents=True)
shutil.copyfile(R.parent/'PMFS_EARLY_DECLARATION_AUDIT_20261018/analysis/EPISODES.csv',P/'EPISODES.csv')
B=T/'build_provenance';B.mkdir()
for name in ['CMakeCache.txt','compile_commands.json','CMakeFiles/gsl_actionserver_node.dir/link.txt']:
 p=R/'build'/name
 if p.is_file():q=B/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
obj=R/'build/CMakeFiles/GSL_common.dir/src/gsl_server/algorithms/Common/Utils/Math.cpp.o'
shutil.copyfile(obj,T/'binaries/production_Math.cpp.o')
assert sha(obj)==json.loads((R/'RNG_RECORDING_QUALIFICATION.json').read_text())['production_Math_object_sha256']
S=D/'PMFS_O24_官方源码身份冻结_阶段0只读预检_20261018.zip'
assert sha(S)=='ad1402d13ac87fdfd8cd539dc134070b334c0aa924133c7affb2e8805cfa9844'
shutil.copyfile(S,T/'baseline_stage0.zip')
batch=json.loads((R/'BATCH_COMPLETE.json').read_text());start=json.loads((R/'BATCH_STARTED.json').read_text())['wall_time'];build_start=json.loads((R/'EXECUTION_STARTED.json').read_text())['wall_time']
identity=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),branch='codex/pmfs-o24-ros-qualification-20261018',parent_commit='6e46fa2d54a9d691867a4a7e90be74d3cd4844e6',evidence_identity='PMFS-O24-PORT-GMRF',runtime_qualification='HOLD_DOMAIN225_PREEXISTING_LIFECYCLE_MANAGER',baseline_stage0_sha256=sha(S),scope='Four actual ROS episodes and all raw evidence. No complete gas frame archive or entire ROS installation. Offline QA can replay maps and RNG without worlds.',build_to_last_goal_completion_wall_s=start-build_start+batch['wall_s'],science_wall_budget_s=2400,goal_count=4,technical_retry_count=0,new_worlds=0,AIMMD=0)
(T/'DELIVERY_IDENTITY.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[dict(path=p.relative_to(T).as_posix(),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(T.rglob('*'))if p.is_file()]
(T/'MANIFEST_SHA256.json').write_text(json.dumps(dict(algorithm='SHA256',files=files,exclusions=['MANIFEST_SHA256.json itself','new offline QA outputs generated after verification']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(T.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(T).as_posix())
with zipfile.ZipFile(Z)as z:
 assert z.testzip()is None
 for row in files:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
receipt=dict(archive=str(Z),archive_sha256=sha(Z),archive_bytes=Z.stat().st_size,payload_files=len(files),research_root=str(T),scope=identity['scope'],scientific_verdict=identity['runtime_qualification'])
(D/'PMFS_O24_四回合_交付回执_20261018.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
