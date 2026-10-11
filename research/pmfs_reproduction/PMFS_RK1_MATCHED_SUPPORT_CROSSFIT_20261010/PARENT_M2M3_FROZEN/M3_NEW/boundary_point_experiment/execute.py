import sys
sys.dont_write_bytecode=True
from remote import run,WORK,REMOTE
from pathlib import Path
import base64,json,hashlib
ROOT=WORK.parents[2]
main=ROOT/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/M3_FROZEN_CONTRACT.json'
assert hashlib.sha256(main.read_bytes()).hexdigest()=='daf2f5e5a151d78513ebf5576799e7a9bc0d1c48e1f069dbeabaf34dc35d4856'
prepared=json.loads((WORK/'PREPARED_CONTRACT.json').read_text())
build=json.loads((WORK/'BUILD_RESULT.json').read_text())
frozen=dict(main_contract_sha256=hashlib.sha256(main.read_bytes()).hexdigest(),prepared_contract_sha256=hashlib.sha256((WORK/'PREPARED_CONTRACT.json').read_bytes()).hexdigest(),executable_sha256=build['executable_sha256'],source_sha256=build['source_sha256'],jobs=prepared['jobs'],forward_wall_s=120,forward_RSS_bytes=536870912,disk_bytes=200000000)
dest=WORK/'EXECUTION_CONTRACT.json';assert not dest.exists();dest.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
digest=hashlib.sha256(dest.read_bytes()).hexdigest();(WORK/'EXECUTION_CONTRACT_SHA256.txt').write_text(digest+'\n',encoding='utf-8')
code='''from pathlib import Path
import base64,csv,hashlib,json,math,os,signal,subprocess,time,traceback
t=Path(REMOTE);m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010');snapshot=m1/'snapshot'
contract_bytes=base64.b64decode(BLOB);assert hashlib.sha256(contract_bytes).hexdigest()==CONTRACT_SHA
assert not (t/'EXECUTION_CONTRACT.json').exists();(t/'EXECUTION_CONTRACT.json').write_bytes(contract_bytes)
contract=json.loads(contract_bytes)
assert hashlib.sha256((t/'candidate_forward').read_bytes()).hexdigest()==contract['executable_sha256']
for n,d in contract['source_sha256'].items():assert hashlib.sha256((t/n).read_bytes()).hexdigest()==d,n
old_budget=json.loads((m1/'FROZEN_FORWARD_BUDGET.json').read_text())
for n,d in old_budget['snapshot_file_hashes'].items():assert hashlib.sha256((snapshot/n).read_bytes()).hexdigest()==d,n
out=t/'forward_calls';assert not out.exists();out.mkdir()
env=os.environ.copy();env.update(LD_LIBRARY_PATH='/opt/ros/humble/lib:/home/zyc/ros2_ws/install/gaden_common/lib:/home/zyc/ros2_ws/install/gaden_msgs/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/home/zyc/ros2_ws/install/gsl_actions/lib:/home/zyc/ros2_ws/install/gsl_server/lib:/home/zyc/ros2_ws/install/olfaction_msgs/lib:/home/zyc/ros2_ws/install/vgr_bridge/lib',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen')
ledger=dict(status='RUNNING_M3_FROZEN_ONE_SHOT',entered_calls=0,completed_calls=0,new_science_calls=0,anchors=[],records=[],forward_wall_seconds=0.,peak_RSS_bytes=0,ros_init=0,new_GADEN=0,new_navigation=0)
def save():
 (t/'EXECUTION_LEDGER.json').write_text(json.dumps(ledger,indent=2))
def parity(job,new):
 old=m1/'forward_calls_after_input_parser_fix'/job['expected_M1_job']
 r0=json.loads((old/'RESULT.json').read_text());r1=json.loads((new/'RESULT.json').read_text())
 for n in ['rng_before','rng_after','gaussian_index_before','gaussian_index_after','release_points']:assert r0[n]==r1[n],n
 checks=[]
 for p in list((old/'maps').glob('*.f32'))+list((old/'points').glob('*.f32')):
  q=new/p.relative_to(old);assert q.read_bytes()==p.read_bytes(),str(q)
  checks.append(dict(file=q.relative_to(new).as_posix(),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),byte_equal=True))
 assert math.isclose(r0['score'],r1['score'],rel_tol=1e-13,abs_tol=1e-300)
 return dict(job=job['job'],verdict='PASS_NATIVE_UNIFORM_MAP_POINT_RNG_SCORE_PARITY',checks=checks)
try:
 for index,job in enumerate(contract['jobs']):
  if index>=2:assert len(ledger['anchors'])==2
  assert ledger['entered_calls']<14
  new=out/job['job'];assert not new.exists()
  ledger['entered_calls']+=1;save();start=time.monotonic();peak=0;reason=None
  with (out/(job['job']+'.stdout')).open('w') as so,(out/(job['job']+'.stderr')).open('w') as se:
   p=subprocess.Popen([str(t/'candidate_forward'),str(snapshot),str(t/'jobs'/(job['job']+'.csv')),str(new)],env=env,stdout=so,stderr=se,start_new_session=True)
   while p.poll() is None:
    rss=0
    for z in Path('/proc').iterdir():
     if not z.name.isdigit():continue
     try:
      if os.getpgid(int(z.name))!=p.pid:continue
      for l in (z/'status').read_text().splitlines():
       if l.startswith('VmRSS:'):rss+=int(l.split()[1])*1024
     except (ProcessLookupError,PermissionError,FileNotFoundError):pass
    peak=max(peak,rss)
    if rss>536870912:reason='RSS_CAP'
    if ledger['forward_wall_seconds']+time.monotonic()-start>120:reason='TOTAL_FORWARD_WALL_CAP'
    if reason:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=3)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     break
    time.sleep(.01)
   exit=p.wait()
  elapsed=time.monotonic()-start;ledger['forward_wall_seconds']+=elapsed;ledger['peak_RSS_bytes']=max(ledger['peak_RSS_bytes'],peak)
  rec=dict(job=job['job'],wall_seconds=elapsed,peak_RSS_bytes=peak,exit_code=exit,resource_stop=reason)
  ledger['records'].append(rec);save()
  assert exit==0 and reason is None,rec
  r=json.loads((new/'RESULT.json').read_text());counter=json.loads((new/'MOVEMENT_COUNTERS.json').read_text())
  assert r['forward_calls']==1 and r['native_updates']==r['ROS_nodes']==0
  assert counter['recursion_guard_hits']==counter['invalid_start_cell']==0,counter
  if job['is_anchor']:ledger['anchors'].append(parity(job,new))
  else:ledger['new_science_calls']+=1
  ledger['completed_calls']+=1
  disk=sum(x.stat().st_size for x in t.rglob('*') if x.is_file());assert disk<200000000,disk
  save()
 ledger['status']='PASS_2_ANCHORS_12_NEW_FORWARD_FACTORIAL_COMPLETE'
except Exception as e:
 ledger['status']='STOP_FIRST_PARITY_TECHNICAL_OR_RESOURCE_FAILURE_NO_RETRY';ledger['error']=repr(e);ledger['traceback']=traceback.format_exc()
finally:
 ledger['new_remote_disk_bytes']=sum(x.stat().st_size for x in t.rglob('*') if x.is_file());save()
print(json.dumps(ledger,indent=2))
'''.replace('REMOTE',repr(REMOTE)).replace('BLOB',repr(base64.b64encode(dest.read_bytes()).decode())).replace('CONTRACT_SHA',repr(digest))
(WORK/'FROZEN_REMOTE_EXECUTION.py').write_text(code,encoding='utf-8',newline='\n')
result=json.loads(run(code,'FORWARD_EXECUTION',170));(WORK/'EXECUTION_LEDGER.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
