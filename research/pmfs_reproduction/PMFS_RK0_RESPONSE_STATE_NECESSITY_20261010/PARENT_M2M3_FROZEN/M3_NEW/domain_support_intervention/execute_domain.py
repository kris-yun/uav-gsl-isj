import sys
sys.dont_write_bytecode=True
from pathlib import Path
import base64,hashlib,json,csv,io,numpy as np
from remote import run,WORK
ROOT=WORK.parents[2];O=ROOT/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/domain_support_intervention'
q=json.loads((O/'DOMAIN_INPUT_QUALIFICATION.json').read_text());parent=O/'DOMAIN_SUPPORT_FROZEN_CONTRACT.json';assert hashlib.sha256(parent.read_bytes()).hexdigest()==q['contract_SHA256']=='a5acfa58fcc28f6300abe1a263213122cc0cf7dfe91922d71ac8dc5afd71b42e'
newinput=O/'COMPLETE_COLUMN_MEAN_input.csv';maskfile=O/'GAS_TRANSPORT_MASK.csv';assert hashlib.sha256(newinput.read_bytes()).hexdigest()==q['input_SHA256'];assert hashlib.sha256(maskfile.read_bytes()).hexdigest()==q['mask_SHA256']
old=list(csv.DictReader((ROOT/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/height_intervention/COLUMN_FREE_UNIFORM_MEAN_input.csv').open(encoding='utf-8')));new=list(csv.DictReader(newinput.open(encoding='utf-8')));mask=list(csv.DictReader(maskfile.open(encoding='utf-8')));assert len(old)==len(new)==len(mask)==1530
for a,b,m in zip(old,new,mask):
 assert a.keys()==b.keys()
 for k in a:
  if k not in ['u','v']:assert a[k]==b[k],k
 if a['occupancy']=='1':
  for k in ['u','v']:assert np.float32(a[k]).tobytes()==np.float32(b[k]).tobytes(),k
 assert int(m['gas_transport_free'])==1 and int(m['free_voxel_count'])>0
build=json.loads((O/'DOMAIN_BUILD_RESULT.json').read_text());base=json.loads((WORK/'PREPARED_CONTRACT.json').read_text());jobs=[]
for bundle,cand in [('T','C7'),('W','K2')]:
 j=next(x for x in base['jobs'] if x['bundle']==bundle and x['candidate']==cand and x['source_form']=='point' and x['boundary']=='native').copy();j['job']='anchor_'+bundle+'_'+cand;j['gas_domain']='native_nav';j['is_anchor']=True;j['expected_height_job']='COLUMN_FREE_UNIFORM_MEAN_'+bundle+'_'+cand;jobs.append(j)
for bundle in ['T','W']:
 for cand in ['C7','K2']:
  j=next(x for x in base['jobs'] if x['bundle']==bundle and x['candidate']==cand and x['source_form']=='point' and x['boundary']=='native').copy();j['job']='union_'+bundle+'_'+cand;j['gas_domain']='column_union';j['is_anchor']=False;jobs.append(j)
c=dict(parent_SHA256=q['contract_SHA256'],input_SHA256=q['input_SHA256'],mask_SHA256=q['mask_SHA256'],executable_SHA256=build['executable_SHA256'],source_SHA256=build['source_SHA256'],jobs=jobs,old_447_uv_float32_exact=True,nonwind_columns_exact=True,maximum_new_calls=6,scientific_calls=4,parity_calls=2)
p=O/'DOMAIN_EXECUTION_CONTRACT.json';assert not p.exists();p.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8');digest=hashlib.sha256(p.read_bytes()).hexdigest();(O/'DOMAIN_EXECUTION_CONTRACT_SHA256.txt').write_text(digest+'\n')
files={p.name:base64.b64encode(p.read_bytes()).decode(),'snapshot/input.csv':base64.b64encode(newinput.read_bytes()).decode(),'snapshot/gas_mask.csv':base64.b64encode(maskfile.read_bytes()).decode()}
for j in jobs:
 vals={k:v for k,v in j.items() if k not in ['is_anchor','expected_height_job']};s=io.StringIO();w=csv.DictWriter(s,list(vals),lineterminator='\n');w.writeheader();w.writerow(vals);files['jobs/'+j['job']+'.csv']=base64.b64encode(s.getvalue().encode()).decode()
code='''from pathlib import Path
import base64,csv,hashlib,json,math,os,signal,subprocess,time,traceback
t=Path('/home/zyc/pmfs_m3_root_discrimination_20261010/domain_support_intervention')
for n,b in @@FILES@@.items():
 p=t/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
assert hashlib.sha256((t/'DOMAIN_EXECUTION_CONTRACT.json').read_bytes()).hexdigest()==@@DIGEST@@
c=json.loads((t/'DOMAIN_EXECUTION_CONTRACT.json').read_text());assert hashlib.sha256((t/'candidate_domain').read_bytes()).hexdigest()==c['executable_SHA256']
for n,d in c['source_SHA256'].items():assert hashlib.sha256((t/n).read_bytes()).hexdigest()==d,n
m1=Path('/home/zyc/pmfs_b4_m1_representation_20261010');snapshot=t/'snapshot'
for n in ['metadata.csv','metadata.json','gaussian_cache.f32','simulation_parameters.csv']:(snapshot/n).write_bytes((m1/'snapshot'/n).read_bytes())
assert hashlib.sha256((snapshot/'input.csv').read_bytes()).hexdigest()==c['input_SHA256'];assert hashlib.sha256((snapshot/'gas_mask.csv').read_bytes()).hexdigest()==c['mask_SHA256']
mask=[x['occupancy']=='1' for x in csv.DictReader((snapshot/'input.csv').open())]
env=os.environ.copy();env.update(LD_LIBRARY_PATH='/opt/ros/humble/lib:/home/zyc/ros2_ws/install/gaden_common/lib:/home/zyc/ros2_ws/install/gaden_msgs/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gmrf_wind_mapping/lib:/home/zyc/ros2_ws/install/gsl_actions/lib:/home/zyc/ros2_ws/install/gsl_server/lib:/home/zyc/ros2_ws/install/olfaction_msgs/lib:/home/zyc/ros2_ws/install/vgr_bridge/lib',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen')
out=t/'forward_calls';assert not out.exists();out.mkdir()
l=dict(status='RUNNING_DOMAIN_FROZEN_ONE_SHOT',entered_calls=0,completed_calls=0,scientific_calls=0,anchors=[],records=[],wall_seconds=0.,RSS_bytes=0,new_GADEN=0,new_CFD=0,new_ROS_init=0,new_navigation=0)
def save():(t/'DOMAIN_EXECUTION_LEDGER.json').write_text(json.dumps(l,indent=2))
def parity(j,p):
 old=Path('/home/zyc/pmfs_m3_root_discrimination_20261010/height_intervention/forward_calls')/j['expected_height_job']
 a=json.loads((old/'RESULT.json').read_text());b=json.loads((p/'RESULT.json').read_text())
 for k in ['rng_before','rng_after','gaussian_index_before','gaussian_index_after','release_points']:assert a[k]==b[k],k
 checks=[]
 for x in list((old/'maps').glob('*.f32'))+list((old/'points').glob('*.f32')):
  new=p/x.relative_to(old);assert x.read_bytes()==new.read_bytes(),str(new)
  checks.append(dict(file=new.relative_to(p).as_posix(),SHA256=hashlib.sha256(new.read_bytes()).hexdigest(),byte_equal=True))
 assert math.isclose(a['score'],b['score'],rel_tol=1e-13,abs_tol=1e-300)
 return dict(job=j['job'],verdict='PASS_OLD_NAV_MASK_COMPLETE_WIND_BYTE_PARITY',checks=checks)
try:
 for i,j in enumerate(c['jobs']):
  if i>=2:assert len(l['anchors'])==2
  assert l['entered_calls']<6;new=out/j['job'];assert not new.exists();l['entered_calls']+=1;save();start=time.monotonic();peak=0;reason=None
  with (out/(j['job']+'.stdout')).open('w') as so,(out/(j['job']+'.stderr')).open('w') as se:
   p=subprocess.Popen([str(t/'candidate_domain'),str(snapshot),str(t/'jobs'/(j['job']+'.csv')),str(new)],env=env,stdout=so,stderr=se,start_new_session=True)
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
  elapsed=time.monotonic()-start;l['wall_seconds']+=elapsed;l['RSS_bytes']=max(l['RSS_bytes'],peak);l['records'].append(dict(job=j['job'],wall_seconds=elapsed,RSS_bytes=peak,exit_code=exit,resource_stop=reason));save();assert exit==0 and reason is None,j
  r=json.loads((new/'RESULT.json').read_text());counts=json.loads((new/'GAS_DOMAIN_COUNTERS.json').read_text())
  assert r['forward_calls']==1 and r['native_updates']==r['ROS_nodes']==0 and r['source_form']=='point' and r['boundary']=='native'
  assert counts['enabled']==(j['gas_domain']=='column_union')
  import array
  raw=array.array('f');raw.frombytes(next((new/'maps').glob('*_unblurred.f32')).read_bytes());assert all(v==0 for m,v in zip(mask,raw) if not m),'nonnav beforeblur not zero'
  if j['is_anchor']:l['anchors'].append(parity(j,new))
  else:l['scientific_calls']+=1
  l['completed_calls']+=1;save()
 l['status']='PASS_2_OLD_MASK_PARITY_4_TRANSPORT_DOMAIN_FORWARDS'
except Exception as e:l['status']='STOP_FIRST_FAILURE_NO_RETRY';l['error']=repr(e);l['traceback']=traceback.format_exc()
finally:save()
print(json.dumps(l,indent=2))
'''.replace('@@DIGEST@@',repr(digest)).replace('@@FILES@@',repr(files))
(WORK/'DOMAIN_FROZEN_REMOTE_EXECUTION.py').write_text(code,encoding='utf-8',newline='\n')
print('Frozen child executable/input contract SHA256',digest)
if '--execute' in sys.argv:
 r=json.loads(run(code,'DOMAIN_FORWARD_EXECUTION',110));(O/'DOMAIN_EXECUTION_LEDGER_LOCAL.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
