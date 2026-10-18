from pathlib import Path
import hashlib,json,os,psutil,shutil,signal,subprocess,sys,time
S=Path('/mnt/hgfs/workspace/PMFS_PAPER_FIRST_ROS_QUAL_20261017');V=Path('/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017')
plan_name=os.environ.get('QUAL_RUN_PLAN','RUN_PRECOMMIT.json')
plan=json.loads((S/plan_name).read_text());output_suffix=''if plan_name=='RUN_PRECOMMIT.json'else '_FINAL'if plan_name=='RUN_PRECOMMIT_FINAL.json'else '_NEXT'
build=json.loads((S/'BUILD_RESULT.json').read_text());assert json.loads((S/'WORLD_INPUT_GATE.json').read_text())['status'].startswith('PASS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
assert sha(Path(build['binary']))==build['binary_sha256']
dependencies=[('/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/install_paper_gmrf_tfqualified_2024/lib/gmrf_wind_mapping/gmrf_wind_mapping_node','6882e2e60440c5d5cb600eed454d160ded227fbbc8ed3c55a7fcf9572ad4efe2'),('/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/public_clock_player','ca8989091885fe920957e977bf7efac382633c9b4862dc968e5ca4cfbed9d80c')]
for path,h in dependencies:assert sha(Path(path))==h,(path,'dependency changed')
put(S/'LIVE_BINARY_AND_DEPENDENCY_IDENTITY.json',dict(baseline=build['binary_sha256'],dependencies=[dict(path=p,sha256=h)for p,h in dependencies]))
requested=sys.argv[1:];roles=[r for r in plan['roles']if not requested or r['id']in requested];assert roles
receipts=[]
for role in roles:
 T=Path(role['guest_path']);F=S/'cases'/role['id'];runtime=Path(role['runtime_shared']);runtime.mkdir(exist_ok=True)
 assert not T.exists(),('Existing guest role never overwritten',str(T))
 T.mkdir(parents=True)
 for name in ['N1_launch.py','runtime_driver.py','RUN_SHELL.sh','CASE_META.json','AUTHOR_WALL_FILE_CADENCE.csv']:shutil.copyfile(F/name,T/name)
 assert shutil.disk_usage(V).free>5*2**30 and shutil.disk_usage(S).free>2*2**30
 # No competing participant may share this isolated domain.
 for p in psutil.process_iter(['pid','cmdline']):
  if p.pid==os.getpid():continue
  try:
   env=p.environ();cmd=' '.join(p.info['cmdline']or[])
   if env.get('ROS_DOMAIN_ID')==str(role['domain']) and any(x in cmd for x in ['ros2','gsl_actionserver','gmrf_wind','gaden_player','basic_sim','runtime_driver.py']):raise RuntimeError('Domain occupied:'+str(p.pid))
  except (psutil.NoSuchProcess,psutil.AccessDenied):pass
 start=time.monotonic()
 with (F/'driver.log').open('wb')as log:
  proc=subprocess.Popen(['bash',str(T/'RUN_SHELL.sh')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  while proc.poll()is None:
   elapsed=time.monotonic()-start
   try:status=json.loads((T/'RUNTIME_STATUS.json').read_text())if (T/'RUNTIME_STATUS.json').exists()else{}
   except json.JSONDecodeError:status={}
   put(S/'RUNTIME_PROGRESS.json',dict(active_role=role['id'],pid=proc.pid,elapsed_s=elapsed,preflight=status.get('preflight'),native_goal_count=status.get('native_goal_count'),pose_samples=status.get('pose_samples'),completed_roles=receipts))
   if elapsed>520:
    os.killpg(proc.pid,signal.SIGINT)
    try:proc.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=10)
    break
   time.sleep(2)
 for name in ['RUN_STARTED.json','RUN_RESULT.json','RUNTIME_STATUS.json']:
  if (T/name).exists():shutil.copyfile(T/name,F/name)
 result=json.loads((T/'RUN_RESULT.json').read_text())if (T/'RUN_RESULT.json').exists()else dict(result='NO_RESULT_RECEIVED')
 receipt=dict(id=role['id'],case=role['case'],controller_exit_code=proc.returncode,wall_s=time.monotonic()-start,result=result)
 receipts.append(receipt);put(S/('RUN_RESULTS'+output_suffix+'.json'),dict(status='PRIMARY_CASES_RECORDED',rows=receipts))
 print(json.dumps(dict(id=role['id'],wall_s=receipt['wall_s'],result=result.get('result'),localization_success=result.get('localization_success'),error=result.get('error'))),flush=True)
 if result.get('result')not in ['NATIVE_ACTION_RETURNED']:break
put(S/('RUN_CONTROLLER_COMPLETE'+output_suffix+'.json'),dict(recorded_roles=len(receipts),requested=len(roles),rows=receipts))
