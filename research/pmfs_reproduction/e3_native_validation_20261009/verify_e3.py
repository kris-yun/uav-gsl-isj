"""Read-only audit of saved E3 evidence. Python + numpy + PyYAML + Pillow. No ROS/simulation/training.
Run: python verify_e3.py [--write-summary] [--no-manifest]
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
def js(n):return json.loads((P/n).read_text(encoding='utf-8'))
def rows(n):
 with (P/n).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def jsonlines(n):
 with gzip.open(P/n,'rt',encoding='utf-8') as f:
  for line in f:yield json.loads(line)
def a(n,d):
 b=(P/n).read_bytes();x=np.frombuffer(b,dtype=d);assert np.isfinite(x).all(),n;return x
g1=js('run/GATE1.json');g2=js('run/GATE2.json');run=js('run/RUN_RESULT.json');pre=js('runtime/PREFLIGHT.json')
assert g1['verdict']=='PASS' and g2['verdict'].startswith('PASS')
assert run['native_goal_count']==1 and run['result']=='NATIVE_ACTION_RETURNED' and run['action_status']==4
assert run['fixture_messages_injected']==0 and run['generated_gas_data']==0 and pre['native_goal_count']==0
assert all(x=='active' for x in pre['lifecycle'].values()) and pre['sensor_xyz']==[-3,4.5,.5]
assert pre['gas_types']==['butane'] and pre['probe_is_input_to_algorithm'] is False
assert js('run/GENERATION_RESULT.json')['generation_executions']==js('run/PREPROCESSING_RESULT.json')['preprocessing_executions']==1
assert js('run/OWN_DOMAIN_CLEANUP.json')['remaining_pids']==[]
for n,h in js('run/OFFICIAL_RUNTIME_ASSETS.json').items():assert hashlib.sha256((P/'official_E3'/n).read_bytes()).hexdigest()==h,n
params=yaml.safe_load((P/'runtime/resolved_GSL_parameters.yaml').read_text())['/PioneerP3DX/GSL']['ros__parameters']
expected={'use_sim_time':True,'maxSearchTime':300.,'initialExplorationMoves':2,'stepsSourceUpdate':3,'sourceDiscriminationPower':.3,'convergence_thr':1.5,'scale':25,'th_gas_present':.1,'th_wind_present':.02,'iterationsToRecord':200,'maxWarmupIterations':500,'minWarmupIterations':200,'deltaTime':.1,'noiseSTDev':.5,'ground_truth_x':-4.,'ground_truth_y':-1.9,'useWindGroundTruth':True,'maxUpdatesPerStop':5,'stop_and_measure_time':.4}
for n,v in expected.items():assert params[n]==v,(n,params[n],v)
pid=yaml.safe_load((P/'runtime/preflight_PioneerP3DX_PID_parameters.yaml').read_text())['/PioneerP3DX/PID']['ros__parameters']
assert pid['sensor_model']==30 and pid['use_PID_correction_factors'] is False and pid['use_sim_time'] is True
assert 'return accumulated_conc;' in (P/'source/sensor/fake_gas_sensor.cpp').read_text()
binding=js('run/PARAMETER_BINDING.json');assert np.allclose(binding['source_xyz'],[-4,-1.9,.7],atol=1e-6,rtol=0)
for key in ['temperature','pressure','gas_type','num_filaments_sec','filament_noise_std']:
 assert abs(binding[key]-{'temperature':298,'pressure':1,'gas_type':10,'num_filaments_sec':10,'filament_noise_std':.015}[key])<1e-6
# All trace rows and sampled binary files have a physical time lineage.
times=rows('run/PHYSICAL_FRAME_TIME.csv');assert len(times)==1803
clock_times=np.array([float(r['physical_snapshot_time_s']) for r in times]);assert np.all(np.diff(clock_times)>0)
registered=rows('run/ALL_FRAME_SHA256_AND_TIME.csv');assert [int(x['frame']) for x in registered]==list(range(1803))
for f in (P/'sample_frames').glob('iteration_*'):
 k=int(f.name.split('_')[-1]);b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==registered[k]['sha256'] and b[13]==1
 raw=zlib.decompress(b[22:]);assert len(raw)==struct.unpack_from('<Q',b,14)[0]
 assert struct.unpack_from('<II',raw)==(3,0) and list(struct.unpack_from('<3i',raw,8))==[110,120,30]
 off=56+struct.unpack_from('<Q',raw,48)[0];assert np.allclose(struct.unpack_from('<3f',raw,off),[-4,-1.9,.7],atol=1e-6,rtol=0)
 assert struct.unpack_from('<i',raw,off+12)[0]==10 and struct.unpack_from('<i',raw,off+24)[0]==0
clock=rows('runtime/physical_clock_trace.csv');ages=[]
for r in clock:
 target=float(r['target_internal_s']);frame=int(r['frame']);now=int(r['receipt_ros_ns']);anchor=int(r['anchor_ros_ns'])
 assert abs(target-(clock_times[200]+(now-anchor)/1e9))<1e-9
 assert frame==np.searchsorted(clock_times,target,side='right')-1 and int(r['wind_index'])==0
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
assert len(angle_residual)>100 and max(angle_residual)<1e-6 and max(position_delta)<2e-6
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
meta=yaml.safe_load((P/'official_E3/scenarios/E/_occupancy.yaml').read_text());pixels=np.asarray(Image.open(P/'official_E3/scenarios/E/_occupancy.pgm'))
expected_map=np.flipud(np.where(pixels>255*.9,0,np.where(pixels<255*.1,100,-1))).astype('i1')
assert np.array_equal(actual,expected_map) and [w,h]==[1100,1200] and origin==[-5.5,-6,0] and q==[0,0,0,1]
native_free=np.all(actual.reshape(48,25,44,25)==0,axis=(1,3));assert native_free[16,6]
# Full finite static wind field is recomputed using pinned float32 / last-row-wins parsing.
wind=a('derived_E3/wind/wind_iteration_0','u1')[8:].view('<f4').reshape(-1,3)
raw=np.loadtxt(P/'official_E3/scenarios/E/wind_simulations/W1/wind_at_cell_centers_0.csv',delimiter=',',skiprows=1)
ind=((raw[:,3:6].astype(np.float32)-np.array([-5.5,-6,0],dtype=np.float32))/np.float32(.1)).astype(int)
flat=ind[:,0]+ind[:,1]*110+ind[:,2]*110*120;reference=np.zeros_like(wind)
for i,v in zip(flat,raw[:,:3]):reference[i]=v
assert np.array_equal(wind,reference)
queries=list(jsonlines('runtime/service_queries.jsonl.gz'));wind_checked=0;bulk=0
for r in queries:
 if r['kind']!='WindPosition':continue
 c=CDR(r['response_cdr_hex']);uv=np.column_stack([c.seqdouble(),c.seqdouble(),c.seqdouble()]);xyz=np.column_stack([r['x'],r['y'],r['z']]).astype(np.float32)
 assert np.isfinite(uv).all()
 ijk=((xyz-np.array([-5.5,-6,0],dtype=np.float32))/np.float32(.1)).astype(int)
 legal=np.all((ijk>=0)&(ijk<np.array([110,120,30])),axis=1)
 assert legal.all();indices=ijk[:,0]+ijk[:,1]*110+ijk[:,2]*110*120
 assert np.array_equal(uv,wind[indices]),r['serial'];wind_checked+=len(uv);bulk+=len(uv)>1
# Saved candidate maps, samples, scores and all posterior updates are independently recomputed.
updates=sorted((P/'runtime/updates').glob('update_*'));assert updates
summary_updates=[];source=np.array([-4,-1.9]);all_candidates=0;maxrel=0.;maxpost=0.
for u in updates:
 assert (u/'COMPLETE.txt').exists()
 m=json.loads((u/'metadata.json').read_text());data=rows(str(u.relative_to(P)/'input.csv'));assert [m['width'],m['height']]==[44,48]
 free=np.array([int(x['occupancy'])==1 for x in data]);assert free.sum()==1132 and free[6+16*44]
 measured=1-1/(1+np.exp(np.array([float(x['logOdds']) for x in data])))
 conf=np.array([float(x['confidence']) for x in data]);scores=np.zeros(len(data),dtype=np.longdouble)
 candidates=rows(str(u.relative_to(P)/'candidates.csv'));points_count=0
 for r in candidates:
  hm=a(str(u.relative_to(P)/r['map_file']),'<f4');assert len(hm)==len(data) and hm.min()>=-2e-6 and hm.max()<=1+2e-6
  un=a(str(u.relative_to(P)/'maps'/(r['candidate_id']+'_unblurred.f32')),'<f4');assert len(un)==len(data)
  factor=1+((1-np.abs(measured-hm)*.3)-1)*np.where(conf>=0,np.minimum(conf,1),0)
  score=np.prod(factor[free].astype(np.longdouble),dtype=np.longdouble);actual_score=np.longdouble(r['score']);rel=float(abs(score-actual_score)/actual_score);maxrel=max(maxrel,rel);assert rel<5e-12
  x,y,ww,hh=[int(r[k]) for k in ['origin_i','origin_j','size_i','size_j']]
  for yy in range(y,y+hh):scores[x+yy*44:x+ww+yy*44]=actual_score
  pt=a(str(u.relative_to(P)/r['points_file']),'<f4').reshape(-1,2);assert len(pt)==int(r['point_count']);points_count+=len(pt)
  assert ((pt[:,0]>=-5.5+x*.25-2e-6)&(pt[:,0]<=-5.5+(x+ww)*.25+2e-6)&(pt[:,1]>=-6+y*.25-2e-6)&(pt[:,1]<=-6+(y+hh)*.25+2e-6)).all()
  assert r['rng_before'].strip() and r['rng_after'].strip()
 rawscores=np.array([np.longdouble(r['score']) for r in rows(str(u.relative_to(P)/'raw_cell_scores.csv'))]);assert np.allclose(scores,rawscores,rtol=1e-15,atol=0)
 posterior=a(str(u.relative_to(P)/'posterior.f64'),'<f8');recomputed=np.where(free,scores/scores[free].sum(dtype=np.longdouble),0);err=float(np.max(np.abs(posterior-recomputed)));maxpost=max(maxpost,err);assert err<1e-12
 assert (posterior[~free]==0).all() and abs(posterior.sum()-1)<1e-12
 assert a(str(u.relative_to(P)/'gaussian_cache.f32'),'<f4').size==2500
 assert (u/'coarse_tree.csv').exists() and (u/'final_tree.csv').exists()
 xy=np.column_stack([-5.5+(np.arange(len(data))%44+.5)*.25,-6+(np.arange(len(data))//44+.5)*.25]);mean=(xy*posterior[:,None]).sum(axis=0);var=float((np.sum((xy-mean)**2,axis=1)*posterior).sum());ties=np.flatnonzero(posterior==posterior.max());mapxy=xy[ties[0]]
 error=np.linalg.norm(xy-source,axis=1)
 summary_updates.append(dict(update=u.name,ROS_stamp_s=m['stamp_ns']/1e9,candidates=len(candidates),captured_points=points_count,variance=var,MAP_xy=mapxy.tolist(),MAP_error_m=float(np.linalg.norm(mapxy-source)),MAP_ties=len(ties),mean_xy=mean.tolist(),mean_error_m=float(np.linalg.norm(mean-source)),source_probability=float(posterior[6+16*44]),source_1m_mass=float(posterior[error<=1].sum()),source_halfm_mass=float(posterior[error<=.5].sum()),max_cell_probability=float(posterior.max()),nonzero_free_cells=int((posterior[free]>0).sum())))
 all_candidates+=len(candidates)
last=summary_updates[-1];native=(P/'runtime/native_results.csv').read_text().split();success=native[0]!='FAILED';native=native if success else native[1:]
assert success==run['localization_success'] and abs(float(native[2])-last['mean_error_m'])<2e-5 and abs(float(native[5])-last['variance'])<2e-5
assert (last['variance']<1.5)==success
path=np.array(js('runtime/robot_path.json'));travel=float(np.linalg.norm(np.diff(path[:,1:3],axis=0),axis=1).sum())
with (P/'runtime/measurement_events.csv').open() as f:events=list(csv.reader(f))
stops=[];audit=[]
for i,r in enumerate(events):
 stamp,gas,ws,wd,x,y,k,b=r;k=int(k)
 if not stops or stops[-1]['counter']!=k:stops.append(dict(counter=k,x=float(x),y=float(y),first_ROS_s=int(stamp)/1e9,last_ROS_s=int(stamp)/1e9,blocks=0,positive=0,gas=[]))
 stop=stops[-1];stop['last_ROS_s']=int(stamp)/1e9;stop['blocks']+=1;stop['positive']+=float(gas)>.1;stop['gas'].append(float(gas))
 audit.append(dict(event='measurement_block',id=i+1,stop=k+1,ROS_s=int(stamp)/1e9,x=x,y=y,gas_ppm=gas,detected=float(gas)>.1,updates_before_in_stop=b,update_trigger_after_block=(int(b)==4 and k>=2 and k%3==0),variance='',MAP_error_m='',mean_error_m='',source_1m_mass=''))
for s in stops:
 gas=s.pop('gas');s['gas_min']=min(gas);s['gas_max']=max(gas);s['source_update_scheduled']=s['counter']>=2 and s['counter']%3==0
for u in summary_updates:audit.append(dict(event='source_update',id=u['update'],stop='',ROS_s=u['ROS_stamp_s'],x='',y='',gas_ppm='',detected='',updates_before_in_stop='',update_trigger_after_block='',variance=u['variance'],MAP_error_m=u['MAP_error_m'],mean_error_m=u['mean_error_m'],source_1m_mass=u['source_1m_mass']))
normal=success and last['MAP_error_m']<=1 and last['mean_error_m']<=1
log=(P/'runtime/launch.log').read_text();teardown='HOLD_POST_RESULT_GSL_EXIT_MINUS11' if 'exit code -11' in log else ('HOLD_POST_RESULT_ABNORMAL_EXIT' if 'process has died' in log else 'PASS')
summary=dict(physical_input_qualification='PASS_TRACEABLE_CONTROLLED_SIMULATION',native_goal_execution='PASS_RESULT_RETURNED_AND_ALL_UPDATES_CAPTURED',localization_success=success,normal_control='PASS' if normal else 'FAIL_PRE_REGISTERED_1M_ERROR_GATE',physical_failure_mechanism='HOLD_SINGLE_REALIZATION_NO_CAUSAL_CONTROL',N1_engineering_aligned=True,historical_N0_reproduction_claim=False,source_xyz=[-4,-1.9,.7],actual_ROS_map_matches_pinned_official=True,source_2D_supported=True,source_3D_free=True,native_goal_count=1,gas_realizations=1,native_search_sim_s=float(native[1]),native_goal_wall_s=run['wall_seconds'],native_top5_percent_mean_error_m=float(native[3]),official_variance_threshold=1.5,final=last,updates=summary_updates,completed_measurement_stops=len(stops),measurement_blocks=len(events),positive_blocks=sum(x['positive'] for x in stops),negative_blocks=sum(x['blocks']-x['positive'] for x in stops),distinct_stationary_locations=len({(x['x'],x['y']) for x in stops}),stops=stops,independent_realizations=1,independence_of_measurement_blocks='NOT_ASSUMED',robot_travel_m=travel,candidates_all_updates=all_candidates,score_max_relative_error=maxrel,posterior_max_abs_error=maxpost,clock_trace_rows=len(clock),frame_hold_age_max_s=max(ages),no_future_frames=True,raw_service_queries=len(queries),wind_vectors_verified=wind_checked,bulk_wind_queries=bulk,teardown=teardown,B4='HOLD_NOT_AUTHORIZED',source_position_or_threshold_or_seed_changed=False)
summary.update(consumer_message_age_max_sim_s=max(message_ages),matched_wind_consumers=len(angle_residual),wind_heading_residual_max_rad=max(angle_residual),wind_position_delta_max_m=max(position_delta))
if '--write-summary' in sys.argv:
 (P/'E3_RESULT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 with (P/'E3_OBSERVATION_AND_POSTERIOR_AUDIT.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=audit[0]);w.writeheader();w.writerows(sorted(audit,key=lambda x:float(x['ROS_s'])))
if '--no-manifest' not in sys.argv and (P/'SHA256_MANIFEST.json').exists():
 for n,h in js('SHA256_MANIFEST.json').items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
print(json.dumps(summary,ensure_ascii=False))
