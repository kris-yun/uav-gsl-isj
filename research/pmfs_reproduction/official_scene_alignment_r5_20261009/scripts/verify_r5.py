"""Read-only portable verification of saved R5 evidence. No ROS, simulations or training."""
import csv,json,struct,math,sys
from pathlib import Path
from decimal import Decimal,localcontext
O=Path(sys.argv[1]);R=O/'runtime';checks=[]
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def arr(p,typ,count=None):
 b=p.read_bytes();size=struct.calcsize(typ);assert len(b)%size==0,str(p);a=struct.unpack('<'+str(len(b)//size)+typ,b)
 if count is not None:assert len(a)==count,str(p)
 assert all(math.isfinite(x) for x in a),str(p)
 return a
def put(layer,verdict='PASS',**kwargs):checks.append(dict(layer=layer,verdict=verdict,**kwargs))
run=json.loads((R/'RUN_RESULT.json').read_text());assert run['native_goal_count']==1 and run['fixture_messages_injected']==run['generated_gas_data']==0
assert run['result']=='NATIVE_ACTION_RETURNED';assert all(x['returncode'] is not None for x in run['processes'])
pre=json.loads((R/'PREFLIGHT.json').read_text());assert all(x=='active' for x in pre['lifecycle'].values());assert abs(pre['sensor_xyz'][2]-.4)<1e-10
put('native_closed_loop_execution',native_goals=1,search_budget_s=300,action_status=run['action_status'],localization_success=run['localization_success'],wall_seconds=run['wall_seconds'],nonzero_cmd_vel_messages=run['nonzero_cmd_vel_messages'])
path=json.loads((R/'robot_path.json').read_text());assert len(path)>100;travel=sum(math.hypot(b[1]-a[1],b[2]-a[2]) for a,b in zip(path,path[1:]));put('physical_robot_motion',path_samples=len(path),travel_m=travel,closest_robot_to_source_m=min(math.hypot(p[1],p[2]+1) for p in path))
consumed=rows(R/'consumer_messages.csv');wind=[x for x in consumed if x['kind']=='wind'];ages=[(int(x['receipt_ns'])-int(x['stamp_ns']))/1e9 for x in consumed];assert min(ages)>=-1e-9 and max(ages)<1
gmrf={}
for line in (R/'GMRF_consumed.csv').read_text().splitlines():
 a=line.split(',');gmrf.setdefault((int(a[0])*1000000000+int(a[1]),a[2]),[]).append(a)
angles=[];positions=[];residuals=[];skipped_zero=0
for x in wind:
 pool=gmrf.get((int(x['stamp_ns']),x['frame']),[])
 # /clock is 10 Hz and the sensor is faster: stamp/frame alone are not a message identity.
 pool=[g for g in pool if abs(float(g[3])-float(x['speed']))<1e-10 and abs(math.atan2(math.sin(float(g[4])+math.pi-float(x['direction'])),math.cos(float(g[4])+math.pi-float(x['direction']))))<5e-7]
 if not pool:continue
 assert len(pool)==1
 g=pool[0]
 if float(x['speed'])<=1e-8:skipped_zero+=1;continue
 delta=float(x['map_yaw'])-float(g[5]);signed=math.atan2(math.sin(delta),math.cos(delta));angles.append(abs(signed));residuals.append(abs(signed-(math.pi-3.14159)));positions.append(math.hypot(float(x['map_x'])-float(g[6]),float(x['map_y'])-float(g[7])))
# Fixed upstream GMRF adds literal 3.14159, whereas the TO adapter uses math.pi.
# Preserve the actual discrepancy, and verify the analytic residual with the original 1e-6 bound.
assert len(angles)>100;assert max(residuals)<1e-6 and max(positions)<2e-6
put('actual_consumers_wind_frame_and_runtime_clock',matched_nonzero_wind_messages=len(angles),zero_speed_angle_comparisons_skipped=skipped_zero,heading_max_abs_rad=max(angles),upstream_pi_approximation_rad=math.pi-3.14159,heading_residual_max_abs_rad=max(residuals),position_max_abs_m=max(positions),consumed_message_age_max_s=max(ages),wind_sensor_height_m=.4)
put('physical_time_of_underlying_gas_record','HOLD',reason='Frame numbering does not establish the generation time axis; native wall/simulation clocks are aligned but underlying data are not qualified C1.')
updates=sorted((R/'updates').glob('update_*'));assert len(updates)==1
for u in updates:
 assert (u/'COMPLETE.txt').exists();m=json.loads((u/'metadata.json').read_text());data=rows(u/'input.csv');n=m['width']*m['height'];assert len(data)==n
 free=[int(x['occupancy'])==1 for x in data];assert sum(free)==m['free_cells'];prob=[]
 for x in data:
  lo=float(x['logOdds']);prob.append(1. if lo>700 else 1-1/(1+math.exp(lo)))
 native=rows(u/'candidates.csv');cell_scores=[Decimal(0)]*n;max_score_error=Decimal(0);point_count=0;min_factor=1.
 with localcontext() as c:
  c.prec=60
  for x in native:
   hm=arr(u/x['map_file'],'f',n);assert min(hm)>=-2e-6 and max(hm)<=1+2e-6
   score=Decimal(1)
   for i,(measured,sim) in enumerate(zip(prob,hm)):
    if not free[i]:continue
    confidence=float(data[i]['confidence']);single=1-abs(measured-sim)*.3;factor=1+(single-1)*min(1.,confidence) if confidence>=0 else 1.;min_factor=min(min_factor,factor);assert factor>0;score*=Decimal.from_float(factor)
   actual=Decimal(x['score']);assert actual>0;relative=abs(score-actual)/actual;max_score_error=max(max_score_error,relative)
   assert relative<Decimal('5e-13'),str(relative)
   i,j,w,h=[int(x[k]) for k in ['origin_i','origin_j','size_i','size_j']]
   for y in range(j,j+h):
    for xx in range(i,i+w):cell_scores[xx+y*m['width']]=actual
   points=arr(u/x['points_file'],'f',int(x['point_count'])*2);point_count+=len(points)//2
   assert all(m['origin_x']+i*m['cell_size']-2e-6<=px<=m['origin_x']+(i+w)*m['cell_size']+2e-6 and m['origin_y']+j*m['cell_size']-2e-6<=py<=m['origin_y']+(j+h)*m['cell_size']+2e-6 for px,py in zip(points[::2],points[1::2]))
  raw=rows(u/'raw_cell_scores.csv');assert all(abs(a-Decimal(b['score']))<=max(abs(a),Decimal('1e-1000'))*Decimal('5e-19') for a,b in zip(cell_scores,raw))
  total=sum(p for p,f in zip(cell_scores,free) if f);post=arr(u/'posterior.f64','d',n);expected=[float(p/total) if f else 0. for p,f in zip(cell_scores,free)];error=max(abs(a-b) for a,b in zip(post,expected));assert error<1e-12
 arr(u/'gaussian_cache.f32','f',2500)
 put('captured_candidate_samples_and_score_recomputation',candidates=len(native),captured_source_points=point_count,min_single_cell_factor=min_factor,independent_score_max_relative_error=float(max_score_error))
 put('captured_refinement_and_posterior',grid_cells=n,free_cells=sum(free),posterior_sum=sum(post),posterior_max_abs_error=error)
 if (O/'offline_forward/candidate_scores.csv').exists():
  offline=rows(O/'offline_forward/candidate_scores.csv');assert len(offline)==len(native);maxmap=0.;maxrel=0.
  for a,b in zip(native,offline):
   assert a['candidate_id']==b['candidate_id'];assert a['point_count']==b['points_used'];assert a['gaussian_index_after']==b['gaussian_index_after']
   for suffix in ['.f32','_unblurred.f32']:
    left=arr(u/'maps'/(a['candidate_id']+suffix),'f',n);right=arr(O/'offline_forward/maps'/(a['candidate_id']+suffix),'f',n);diff=max(abs(x-y) for x,y in zip(left,right));maxmap=max(maxmap,diff);assert diff<=2e-7
   relative=float(abs(Decimal(a['score'])-Decimal(b['score']))/Decimal(a['score']));maxrel=max(maxrel,relative);assert relative<5e-12
  put('native_to_offline_candidate_forward_replay',candidates=len(native),map_max_abs=maxmap,score_max_relative_error=maxrel,uses_captured_points=True,raw_measurement_map_reconstruction=False)
 else:put('native_to_offline_candidate_forward_replay','HOLD',reason='Offline replay evidence absent')
put('official_C1_physical_reproduction','HOLD',reason='Existing record winds cycle beyond wind index 10; official C1 generation disallows cycling. Existing and official map masks also differ; 3D geometry/projection lineage requires qualification.')
launch=(R/'launch.log').read_text(encoding='utf-8');abnormal='Invalid argument' in launch and 'exit code -6' in launch
put('native_process_teardown','HOLD' if abnormal else 'PASS',post_result_abnormal_child_exit=abnormal,reason='SIGINT overlaps upstream post-result shutdown; root cause and clean teardown are not validated' if abnormal else '')
result=dict(verdict='NATIVE_CHAIN_EXECUTED_C1_QUALIFICATION_HOLD',checks=checks,scientific_mismatch_claim='NOT_QUALIFIED',STOP_results_unchanged=True)
(O/'R5_VERIFICATION_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
