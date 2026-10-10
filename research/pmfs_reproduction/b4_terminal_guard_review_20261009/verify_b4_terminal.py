"""Read-only audit of saved B4 replacement evidence. Python + numpy + PyYAML + Pillow. No ROS/simulation/training.
Run: python verify_b4_terminal.py [--write-summary] [--no-manifest]
Optional summaries are written beside evidence; raw files are never altered.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,gzip,math,struct,hashlib,zlib,io
import numpy as np
import yaml
from PIL import Image
P=Path(__file__).resolve().parent
def ep(n):
 p=P/n
 return p if p.exists() else P/'input_evidence'/n
def js(n):return json.loads(ep(n).read_text(encoding='utf-8'))
def rows(n):
 with ep(n).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def jsonlines(n):
 with gzip.open(P/n,'rt',encoding='utf-8') as f:
  for line in f:yield json.loads(line)
def a(n,d):
 b=ep(n).read_bytes();x=np.frombuffer(b,dtype=d);assert np.isfinite(x).all(),n;return x
g1=js('run/GATE1.json');g2=js('run/GATE2.json');run=js('run/RUN_RESULT.json');pre=js('runtime/PREFLIGHT.json')
assert g1['verdict']=='PASS' and g2['verdict'].startswith('PASS')
assert run['native_goal_count']==1 and run['goal_accepted'] is True
assert run['result']=='RUNTIME_ERROR' and run['resource_stop_reason']=='ROS_CLOCK_FORWARD_JUMP'
assert run['cancellation_requested'] is True and 'localization_success' not in run
assert run['generated_gas_data']==0 and run['fixture_messages_injected']==0
assert pre['ROS_DOMAIN_ID']==78 and pre['gas_types']==['smoke']
assert all(x=='active' for x in pre['lifecycle'].values())
assert np.allclose(pre['sensor_xyz'],[-.9,.15,-.2],atol=1e-12,rtol=0)
assert pre['PID_model']==30 and pre['PID_units']=='ppm' and pre['probe_is_input_to_algorithm'] is False
assert js('run/NEW_EXECUTION_LEDGER.json')['new_gas_generation']==0
assert js('run/PRESERVATION_AND_DOMAIN.json')['remaining_pids']==[]
pref=js('run/REPLACEMENT_PREFLIGHT.json');assert pref['GSL_core_unchanged'] and pref['all_gas_frame_hashes_verified']==1803
assert pref['all_wind_hashes_verified']==11 and pref['official_maxSearchTime']==300
assert js('OLD_B4_FROZEN_AFTER.json')['all_match'] and js('OLD_B4_FROZEN_AFTER.json')['files']==1323
for n,h in js('run/OFFICIAL_RUNTIME_ASSETS.json').items():
 p=P/'input_evidence/official_B4'/n
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==h,n
 else:assert 'wind_simulations/' in n and not n.endswith('_10.csv')
assert (P/'N1_B4_launch.py').read_text().replace('/home/zyc/pmfs_b4_official_terminal_completion_20261009','/home/zyc/pmfs_b4_native_validation_20261009')==(P/'first_B4_reference/N1_B4_launch.py').read_text()
assert "SIMULATION_SEARCH_BUDGET_300S" not in (P/'run/runtime_driver.py').read_text()
assert not (P/'runtime/native_results.csv').exists()
assert not list((P/'runtime/updates').glob('update_*'))
assert (P/'runtime/resolved_GSL_parameters.yaml').read_bytes()==b''
binding=js('run/PARAMETER_BINDING.json')
assert np.allclose(binding['source_xyz'],[-3.2,-3.3,-.5],atol=1e-6,rtol=0)
# Re-read 3D geometry and the actual released source voxel.
lines=(P/'input_evidence/derived_B4/OccupancyGrid3D.csv').read_text().splitlines()
minimum=list(map(float,lines[0].split()[1:]));dims=list(map(int,lines[2].split()[1:]));step=float(lines[3].split()[1])
planes=[];plane=[]
for line in lines[4:]:
 if line.strip()==';':
  if plane:planes.append(plane);plane=[]
 elif line.strip():plane.append(list(map(int,line.split())))
if plane:planes.append(plane)
occ=np.array(planes,dtype=np.int32);assert occ.shape==(33,87,114)
ijk=((np.array([-3.2,-3.3,-.5],dtype=np.float32)-np.array(minimum,dtype=np.float32))/np.float32(step)).astype(int)
assert ijk.tolist()==[43,45,5] and occ[ijk[2],ijk[0],ijk[1]]==0
# All trace rows and sampled binary files have a physical time lineage.
times=rows('run/PHYSICAL_FRAME_TIME.csv');assert len(times)==1803
clock_times=np.array([float(r['physical_snapshot_time_s']) for r in times]);assert np.all(np.diff(clock_times)>0)
registered=rows('run/ALL_FRAME_SHA256_AND_TIME.csv');assert [int(x['frame']) for x in registered]==list(range(1803))
assert g2['seed_override'] is False and g2['independent_realizations']==1
for k,(r,t) in enumerate(zip(registered,times)):
 assert abs(float(r['physical_snapshot_time_s'])-clock_times[k])<1e-12
 assert int(r['wind_index'])==int(t['wind_index_at_save'])
 assert [float(r[n]) for n in ('source_x','source_y','source_z')]==[-3.2,-3.3,-.5]
 assert int(r['source_num_filaments_sec'])==7 and r['source_variable_rate']=='False'
 assert int(r['filaments'])==int(t['filaments_after_step'])
assert set(int(r['wind_index']) for r in registered[500:])=={10}
assert abs(clock_times[500]-267.307098389)<1e-9
for f in (P/'input_evidence/sample_frames').glob('iteration_*'):
 k=int(f.name.split('_')[-1]);b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==registered[k]['sha256'] and b[13]==1
 raw=zlib.decompress(b[22:]);assert len(raw)==struct.unpack_from('<Q',b,14)[0]
 assert struct.unpack_from('<II',raw)==(3,0) and list(struct.unpack_from('<3i',raw,8))==[87,114,33]
 off=56+struct.unpack_from('<Q',raw,48)[0];assert np.allclose(struct.unpack_from('<3f',raw,off),[-3.2,-3.3,-.5],atol=1e-6,rtol=0)
 assert struct.unpack_from('<i',raw,off+12)[0]==13 and struct.unpack_from('<i',raw,off+24)[0]==int(times[k]['wind_index_at_save'])
clock=rows('runtime/physical_clock_trace.csv');ages=[]
for r in clock:
 target=float(r['target_internal_s']);frame=int(r['frame']);now=int(r['receipt_ros_ns']);anchor=int(r['anchor_ros_ns'])
 assert abs(target-(clock_times[500]+(now-anchor)/1e9))<1e-9
 assert frame==np.searchsorted(clock_times,target,side='right')-1 and int(r['wind_index'])==10
 assert abs(float(r['frame_internal_s'])-clock_times[frame])<1e-9
 assert clock_times[frame]<=target<clock_times[frame+1];ages.append(target-clock_times[frame])
assert max(ages)<.601
# Actual PMFS/GMRF consumers use the same stamped transform and physical vector.
consumed=rows('runtime/consumer_messages.csv');message_ages=[(int(r['receipt_ns'])-int(r['stamp_ns']))/1e9 for r in consumed]
assert min(message_ages)>=-1e-9
gmrf={}
for line in (P/'runtime/GMRF_consumed.csv').read_text().splitlines():
 r=line.split(',');gmrf.setdefault((int(r[0])*1000000000+int(r[1]),r[2]),[]).append(r)
angle_residual=[];position_delta=[]
for x in consumed:
 if x['kind']!='wind':continue
 pool=gmrf.get((int(x['stamp_ns']),x['frame']),[])
 pool=[r for r in pool if abs(float(r[3])-float(x['speed']))<1e-10 and abs(math.atan2(math.sin(float(r[4])+math.pi-float(x['direction'])),math.cos(float(r[4])+math.pi-float(x['direction']))))<5e-7]
 if not pool or float(x['speed'])<=1e-8:continue
 assert len(pool)==1;r=pool[0];delta=float(x['map_yaw'])-float(r[5]);signed=math.atan2(math.sin(delta),math.cos(delta));angle_residual.append(abs(signed-(math.pi-3.14159)));position_delta.append(math.hypot(float(x['map_x'])-float(r[6]),float(x['map_y'])-float(r[7])))
assert len(angle_residual)>0 and max(angle_residual)<1e-6 and max(position_delta)<2e-6
# Parse actual ROS map CDR and verify the unmodified pinned PGM pixel by pixel.
wire=next(r for r in jsonlines('runtime/raw_ros_cdr.jsonl.gz') if r['topic']=='/PioneerP3DX/map')
class CDR:
 def __init__(self,hex):self.b=bytes.fromhex(hex)[4:];self.p=0
 def read(self,fmt):
  size=struct.calcsize(fmt);align=min(size,8);self.p=(self.p+align-1)//align*align;v=struct.unpack_from('<'+fmt,self.b,self.p)[0];self.p+=size;return v
 def string(self):
  n=self.read('I');s=self.b[self.p:self.p+n];self.p+=n;return s
 def seqdouble(self):
  n=self.read('I');self.p=(self.p+7)//8*8;x=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.p);self.p+=n*8;return x
c=CDR(wire['cdr_hex']);c.read('i');c.read('I');c.string();c.read('i');c.read('I');res=c.read('f');w,h=c.read('I'),c.read('I');origin=[c.read('d') for _ in range(3)];q=[c.read('d') for _ in range(4)];n=c.read('I');actual=np.frombuffer(c.b,dtype='i1',count=n,offset=c.p).reshape(h,w)
meta=yaml.safe_load((P/'input_evidence/official_B4/scenarios/B/_occupancy.yaml').read_text());pixels=np.asarray(Image.open(P/'input_evidence/official_B4/scenarios/B/_occupancy.pgm'))
expected_map=np.flipud(np.where(pixels>255*.9,0,np.where(pixels<255*.1,100,-1))).astype('i1')
assert np.array_equal(actual,expected_map) and [w,h]==[870,1140] and origin==[-7.55,-7.88,0] and q==[0,0,0,1]
reduced=np.all(actual[:1125,:850].reshape(45,25,34,25)==0,axis=(1,3))
native_free=np.zeros_like(reduced);pending=[(26,32)]
while pending:
 x,y=pending.pop()
 if not (0<=x<34 and 0<=y<45) or native_free[y,x] or not reduced[y,x]:continue
 native_free[y,x]=True
 pending.extend((x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy)
assert reduced.sum()==461 and native_free.sum()==447 and native_free[18,17]
# Full finite static wind field is recomputed using pinned float32 / last-row-wins parsing.
wind=a('derived_B4/wind/wind_iteration_10','u1')[8:].view('<f4').reshape(-1,3)
raw=np.loadtxt(P/'input_evidence/official_B4/scenarios/B/wind_simulations/2,4-1_fast/2,4-1_fast_10.csv',delimiter=',',skiprows=1)
ind=((raw[:,3:6].astype(np.float32)-np.array([-7.55,-7.8795,-1.0185],dtype=np.float32))/np.float32(.1)).astype(int)
flat=ind[:,0]+ind[:,1]*87+ind[:,2]*87*114;reference=np.zeros_like(wind)
for i,v in zip(flat,raw[:,:3]):reference[i]=v
assert np.array_equal(wind,reference)
queries=list(jsonlines('runtime/service_queries.jsonl.gz'));wind_checked=0;bulk=0
for r in queries:
 if r['kind']!='WindPosition':continue
 c=CDR(r['response_cdr_hex']);uv=np.column_stack([c.seqdouble(),c.seqdouble(),c.seqdouble()]);xyz=np.column_stack([r['x'],r['y'],r['z']]).astype(np.float32)
 assert np.isfinite(uv).all()
 ijk=((xyz-np.array([-7.55,-7.8795,-1.0185],dtype=np.float32))/np.float32(.1)).astype(int)
 legal=np.all((ijk>=0)&(ijk<np.array([87,114,33])),axis=1)
 assert legal.all();indices=ijk[:,0]+ijk[:,1]*87+ijk[:,2]*87*114
 assert np.array_equal(uv,wind[indices]),r['serial'];wind_checked+=len(uv);bulk+=len(uv)>1
# Diagnose the first actual watchdog decision and the independent player clock.
guard_events=list(jsonlines('runtime/guard_events.jsonl.gz'));first=guard_events[0];last=guard_events[-1]
assert first['decision']=={'action':'DRAIN','reason':'ROS_CLOCK_FORWARD_JUMP'}
assert last['decision']=={'action':'STOP','reason':'ROS_CLOCK_FORWARD_JUMP'}
import importlib.util,re
spec=importlib.util.spec_from_file_location('frozen_executed_guard',P/'runtime_guard_policy.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
guard=module.RuntimeGuard(run['guard_started_monotonic'],run['goal_invocation_ROS_ns'])
assert guard.observe(first['monotonic_wall'],first['ROS_ns'])==first['decision']
ros=[int(x['receipt_ros_ns']) for x in clock];d=np.diff(ros)/1e9
assert d.min()>=0 and d.max()<1
client_delta=(first['ROS_ns']-run['goal_invocation_ROS_ns'])/1e9
assert abs(client_delta-40.49976432)<1e-9 and first['wall_elapsed']<.2
tests=js('GUARD_OFFLINE_TEST_RESULTS.json');assert tests['verdict']=='PASS' and tests['tests']==12 and tests['GSL_executions']==0
assert tests['policy_sha256']==hashlib.sha256((P/'runtime_guard_policy.py').read_bytes()).hexdigest()
newtests=js('offline_proposal/PROPOSED_GUARD_TEST_RESULTS.json');assert newtests['tests']==14 and newtests['GSL_executions']==0 and newtests['applied_to_replacement_goal'] is False
assert newtests['policy_sha256']==hashlib.sha256((P/'offline_proposal/runtime_guard_policy.py').read_bytes()).hexdigest()
log=(P/'runtime/launch.log').read_text();assert 'RESULT IS:' not in log and 'exit code -6' in log
assert 'Asked to publish result for goal that does not exist' in log
sig=log.index("sending signal 'SIGINT'");abort=log.index('Asked to publish result for goal that does not exist')
cleanlog=re.sub(r'\x1b\[[0-9;]*m','',log);exits=[]
for number,line in enumerate(cleanlog.splitlines(),1):
 m=re.search(r'\[([^]]+)\]: process has died \[pid (\d+), exit code (-?\d+)',line)
 if m:exits.append(dict(name=m.group(1),pid=int(m.group(2)),returncode=int(m.group(3)),log_line=number,explicit_exit=True))
 m=re.search(r'\[([^]]+)\]: process has finished cleanly \[pid (\d+)\]',line)
 if m:exits.append(dict(name=m.group(1),pid=int(m.group(2)),returncode=0,log_line=number,explicit_exit=False))
path=np.array(js('runtime/robot_path.json'));travel=float(np.linalg.norm(np.diff(path[:,1:3],axis=0),axis=1).sum())
with (P/'runtime/measurement_events.csv').open() as f:events=list(csv.reader(f))
stops=[]
for r in events:
 stamp,gas,ws,wd,x,y,k,b=r;k=int(k)
 if not stops or stops[-1]['counter']!=k:stops.append(dict(counter=k,x=float(x),y=float(y),blocks=0,positive=0,gas=[]))
 s=stops[-1];s['blocks']+=1;s['positive']+=float(gas)>.1;s['gas'].append(float(gas))
for s in stops:
 gas=s.pop('gas');s.update(gas_min=min(gas),gas_max=max(gas))
assert len(events)==5 and len(stops)==1
old=js('first_B4_reference/B4_RESULT.json');oldpath=np.array(js('first_B4_reference/robot_path.json'))
original_updates=[]
for u in sorted((P/'first_B4_reference/updates').glob('update_*')):
 p=np.frombuffer((u/'posterior.f64').read_bytes(),'<f8');data=list(csv.DictReader((u/'input.csv').open()));free=np.array([int(x['occupancy'])==1 for x in data])
 assert free.sum()==447 and abs(p.sum()-1)<1e-12
 xy=np.column_stack([-7.55+(np.arange(len(p))%34+.5)*.25,-7.88+(np.arange(len(p))//34+.5)*.25]);mean=(xy*p[:,None]).sum(axis=0);var=float((np.sum((xy-mean)**2,axis=1)*p).sum());maperr=float(np.linalg.norm(xy[np.argmax(p)]-[-3.2,-3.3]));meanerr=float(np.linalg.norm(mean-[-3.2,-3.3]));mass=float(p[np.linalg.norm(xy-[-3.2,-3.3],axis=1)<=1].sum())
 expected=next(x for x in old['updates'] if x['update']==u.name)
 assert abs(var-expected['variance'])<1e-12 and abs(maperr-expected['MAP_error_m'])<1e-12 and abs(meanerr-expected['mean_error_m'])<1e-12
 original_updates.append(dict(update=u.name,variance=var,MAP_error_m=maperr,mean_error_m=meanerr,source_1m_mass=mass))
summary=dict(physical_bank_reuse='PASS',replacement_execution='HOLD_EXTERNAL_GUARD_FALSE_CLOCK_ALARM',executed_guard_integration='FAIL_CACHED_CLOCK_OBSERVER_ASSUMPTION',official_action_returned=False,official_success=None,official_top5_error_m=None,official_final_variance=None,MAP_error_m=None,full_mean_error_m=None,native_goals_this_authorization=1,B4_goals_total=2,new_gas_generation=0,new_CFD=0,new_random_seed=0,new_native_updates=0,completed_stops=len(stops),measurement_blocks=len(events),positive_blocks=sum(s['positive'] for s in stops),negative_blocks=sum(s['blocks']-s['positive'] for s in stops),robot_travel_m=travel,stops=stops,goal_client_ROS_s=run['goal_invocation_ROS_ns']/1e9,first_guard_client_ROS_s=first['ROS_ns']/1e9,client_clock_catchup_s=client_delta,first_guard_wall_elapsed_s=first['wall_elapsed'],guard_cancel_wall_elapsed_s=last['wall_elapsed'],player_clock_trace_rows=len(clock),player_clock_max_gap_s=float(d.max()),player_clock_backward_steps=int((d<0).sum()),frame_hold_age_max_s=max(ages),wind_vectors_verified=wind_checked,matched_wind_consumers=len(angle_residual),actual_ROS_map_matches_official=True,launch_exit_states=exits,wrapper_processes=run['processes'],parameter_dump_complete=False,first_B4_updates_recomputed=original_updates,old_B4_preserved=True,third_attempt=False,physical_failure_mechanism='HOLD_NO_OFFICIAL_RESULT_NO_NEW_SOURCE_UPDATE',prospective_guard='OFFLINE_TESTS_14_PASS_NOT_RUNTIME_VALIDATED')
if '--write-summary' in sys.argv:(P/'B4_TERMINAL_COMPLETION_RESULT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
if '--no-manifest' not in sys.argv and (P/'SHA256_MANIFEST.json').exists():
 for n,h in js('SHA256_MANIFEST.json').items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
print(json.dumps(summary,ensure_ascii=False))
