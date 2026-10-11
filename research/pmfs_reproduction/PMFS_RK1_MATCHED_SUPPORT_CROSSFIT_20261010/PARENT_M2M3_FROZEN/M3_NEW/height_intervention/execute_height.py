import sys
sys.dont_write_bytecode=True
from pathlib import Path
import base64,hashlib,json,csv,io
from remote import run,WORK,REMOTE
ROOT=WORK.parents[2];O=ROOT/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/height_intervention'
contract=O/'HEIGHT_FROZEN_CONTRACT.json';digest='f47b4a2028f9b79fc81c947c5e4c78beadb6c55a83d80c930c8b3a7b065d4f63';assert hashlib.sha256(contract.read_bytes()).hexdigest()==digest
q=json.loads((O/'HEIGHT_INPUT_FIELD_QUALIFICATION.json').read_text());old=list(csv.DictReader((ROOT/'work/pmfs_b4_m1/snapshot/input.csv').open(encoding='utf-8')))
files={'HEIGHT_FROZEN_CONTRACT.json':base64.b64encode(contract.read_bytes()).decode()};checks=[]
for field in q['actual_fields']:
 p=O/(field['name']+'_input.csv');assert hashlib.sha256(p.read_bytes()).hexdigest()==field['SHA256'];new=list(csv.DictReader(p.open(encoding='utf-8')));assert len(new)==len(old)==1530
 for a,b in zip(old,new):
  assert a.keys()==b.keys()
  for k in a:
   if k not in ['u','v']:assert a[k]==b[k],(field['name'],k)
 checks.append(dict(field=field['name'],sha256=field['SHA256'],all_other_columns_exact_equal=True))
 files['inputs/'+field['name']+'_input.csv']=base64.b64encode(p.read_bytes()).decode()
base=json.loads((WORK/'PREPARED_CONTRACT.json').read_text())
jobs=[]
for field in [x['name'] for x in q['actual_fields']]:
 for job in base['jobs']:
  if job['source_form']=='point' and job['boundary']=='native':
   j={k:v for k,v in job.items() if k!='is_anchor'};j['job']=field+'_'+job['bundle']+'_'+job['candidate'];j['field']=field;keys=list(j);s=io.StringIO();w=csv.DictWriter(s,keys,lineterminator='\n');w.writeheader();w.writerow(j);files['jobs/'+j['job']+'.csv']=base64.b64encode(s.getvalue().encode()).decode();jobs.append(j)
execution=dict(contract_sha256=digest,executable_sha256=json.loads((WORK/'BUILD_RESULT.json').read_text())['executable_sha256'],field_checks=checks,jobs=jobs,all_forward_calls_cap=8,wall_cap_s=60,RSS_cap_bytes=536870912)
p=O/'HEIGHT_EXECUTION_CONTRACT.json';serialized=(json.dumps(execution,indent=2)+'\n').encode()
if p.exists():assert json.loads(p.read_bytes())==execution
else:p.write_bytes(serialized)
files[p.name]=base64.b64encode(p.read_bytes()).decode();edigest=hashlib.sha256(p.read_bytes()).hexdigest();hashfile=O/'HEIGHT_EXECUTION_CONTRACT_SHA256.txt'
if hashfile.exists():assert hashfile.read_text().strip()==edigest
else:hashfile.write_text(edigest+'\n')
remote_height='/home/zyc/pmfs_m3_root_discrimination_20261010/height_intervention'
code='''from pathlib import Path
import base64,hashlib,json,os,signal,subprocess,time,traceback
t=Path(@@HEIGHT_ROOT@@);assert not t.exists();t.mkdir(parents=True)
for n,b in @@FILES@@.items():
 p=t/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
assert hashlib.sha256((t/'HEIGHT_EXECUTION_CONTRACT.json').read_bytes()).hexdigest()==@@EXECUTION_SHA@@
c=json.loads((t/'HEIGHT_EXECUTION_CONTRACT.json').read_text());exe=Path(@@EXE@@)
assert hashlib.sha256(exe.read_bytes()).hexdigest()==c['executable_sha256']
m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010');expected=json.loads((m1/'FROZEN_FORWARD_BUDGET.json').read_text())['snapshot_file_hashes']
for n,d in expected.items():assert hashlib.sha256((m1/'snapshot'/n).read_bytes()).hexdigest()==d,n
for field in c['field_checks']:
 p=t/'inputs'/(field['field']+'_input.csv');assert hashlib.sha256(p.read_bytes()).hexdigest()==field['sha256']
 snapshot=t/'snapshots'/field['field'];snapshot.mkdir(parents=True)
 for name in ['metadata.csv','metadata.json','gaussian_cache.f32','simulation_parameters.csv']:(snapshot/name).write_bytes((m1/'snapshot'/name).read_bytes())
 (snapshot/'input.csv').write_bytes(p.read_bytes())
out=t/'forward_calls';out.mkdir()
env=os.environ.copy();env.update(LD_LIBRARY_PATH='/opt/ros/humble/lib:/home/zyc/ros2_ws/install/gaden_common/lib:/home/zyc/ros2_ws/install/gaden_msgs/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/home/zyc/ros2_ws/install/gsl_actions/lib:/home/zyc/ros2_ws/install/gsl_server/lib:/home/zyc/ros2_ws/install/olfaction_msgs/lib:/home/zyc/ros2_ws/install/vgr_bridge/lib',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen')
l=dict(status='RUNNING_FROZEN_HEIGHT_ONE_SHOT',entered_calls=0,completed_calls=0,wall_seconds=0.,peak_RSS_bytes=0,records=[],new_GADEN=0,new_CFD=0,ROS_init=0,new_navigation=0,baseline_reruns=0)
def save():(t/'HEIGHT_EXECUTION_LEDGER.json').write_text(json.dumps(l,indent=2))
try:
 for j in c['jobs']:
  assert l['entered_calls']<8;new=out/j['job'];assert not new.exists();l['entered_calls']+=1;save();start=time.monotonic();peak=0;reason=None
  with (out/(j['job']+'.stdout')).open('w') as so,(out/(j['job']+'.stderr')).open('w') as se:
   p=subprocess.Popen([str(exe),str(t/'snapshots'/j['field']),str(t/'jobs'/(j['job']+'.csv')),str(new)],env=env,stdout=so,stderr=se,start_new_session=True)
   while p.poll() is None:
    rss=0
    for z in Path('/proc').iterdir():
     if not z.name.isdigit():continue
     try:
      if os.getpgid(int(z.name))!=p.pid:continue
      for line in (z/'status').read_text().splitlines():
       if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
     except (ProcessLookupError,PermissionError,FileNotFoundError):pass
    peak=max(peak,rss)
    if rss>536870912:reason='RSS_CAP'
    if l['wall_seconds']+time.monotonic()-start>60:reason='COMBINED_WALL_CAP'
    if reason:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=3)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     break
    time.sleep(.01)
   exit=p.wait()
  elapsed=time.monotonic()-start;l['wall_seconds']+=elapsed;l['peak_RSS_bytes']=max(l['peak_RSS_bytes'],peak);l['records'].append(dict(job=j['job'],wall_seconds=elapsed,RSS_bytes=peak,exit_code=exit,resource_stop=reason));save()
  assert exit==0 and reason is None,j
  r=json.loads((new/'RESULT.json').read_text());counter=json.loads((new/'MOVEMENT_COUNTERS.json').read_text())
  assert r['forward_calls']==1 and r['native_updates']==r['ROS_nodes']==0 and r['source_form']=='point' and r['boundary']=='native'
  assert counter['recursion_guard_hits']==counter['slide_attempts']==0
  l['completed_calls']+=1;save()
 l['status']='PASS_EIGHT_INPUT_ONLY_HEIGHT_FORWARDS_NO_RERUN'
except Exception as e:l['status']='STOP_FIRST_FAILURE_NO_RETRY';l['error']=repr(e);l['traceback']=traceback.format_exc()
finally:save()
print(json.dumps(l,indent=2))
'''.replace('@@HEIGHT_ROOT@@',repr(remote_height)).replace('@@EXECUTION_SHA@@',repr(edigest)).replace('@@EXE@@',repr(REMOTE+'/candidate_forward')).replace('@@FILES@@',repr(files))
(WORK/'HEIGHT_FROZEN_REMOTE_EXECUTION_VALIDATED.py').write_text(code,encoding='utf-8',newline='\n')
r=json.loads(run(code,'HEIGHT_FORWARD_EXECUTION',110));(O/'HEIGHT_EXECUTION_LEDGER.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
