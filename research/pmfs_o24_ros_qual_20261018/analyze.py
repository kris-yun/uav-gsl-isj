from pathlib import Path
import csv,collections,hashlib,json,math,re,statistics,os
import numpy as np
R=Path(__file__).resolve().parent;A=R/'analysis';A.mkdir(exist_ok=True)
P24=R.parent/'PMFS_EARLY_DECLARATION_AUDIT_20261018'
if not P24.exists():P24=R/'p24_reference'
pairs={r['case']:r for r in json.loads((R/'PHASE1_DIAGNOSTIC_SOURCE_PAIRS.json').read_text(encoding='utf-8'))['pairs']}
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rows):
 if rows:
  with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
eps=[];updates=[];parity=[];cppgroups=[];cppindex=[];times=[];cost=[]
for F in sorted((R/'cases').iterdir()):
 rt=F/'runtime'
 if not (F/'RUN_RESULT.json').exists():continue
 meta=json.loads((F/'CASE_META.json').read_text(encoding='utf-8'));res=json.loads((F/'RUN_RESULT.json').read_text(encoding='utf-8'));case=meta['case'];truth=meta['source_xyz'];post=read(rt/'native_posterior_updates.csv')if (rt/'native_posterior_updates.csv').exists()else[];nav=json.loads((rt/'NAVIGATION_MAP_METADATA.json').read_text(encoding='utf-8'))if (rt/'NAVIGATION_MAP_METADATA.json').exists()else None
 grouped=collections.defaultdict(list)
 for x in post:grouped[int(x['update'])].append(x)
 candidates=read(rt/'native_candidate_maps.csv')if (rt/'native_candidate_maps.csv').exists()else[];blob=(rt/'native_candidate_maps.f32').read_bytes()if candidates else b''
 for u,rows in grouped.items():
  n=len(rows);p=np.array([float(x['source_probability'])for x in rows]);xx=np.array([float(x['x_m'])for x in rows]);yy=np.array([float(x['y_m'])for x in rows]);mass=float(p.sum());assert abs(mass-1)<1e-10;p/=mass;mx=float(p@xx);my=float(p@yy);var=float(p@((xx-mx)**2+(yy-my)**2));cs=nav['resolution']*25;cx=int((truth[0]-nav['origin_x'])/cs);cy=int((truth[1]-nav['origin_y'])/cs);lookup={(int(x['col']),int(x['row'])):i for i,x in enumerate(rows)};ti=lookup.get((cx,cy));near= pairs[case]['near_source_cell'];comp=pairs[case]['competitor_cell'];ni=lookup[(near['col'],near['row'])];ci=lookup[(comp['col'],comp['row'])];margin=math.log(p[ni])-math.log(p[ci])if p[ni]>0 and p[ci]>0 else None;dist=np.hypot(xx-truth[0],yy-truth[1]);best=np.flatnonzero(p==p.max());mi=min(best,key=lambda i:(int(rows[i]['row']),int(rows[i]['col'])));omega=np.array([float(x['hit_omega'])for x in rows]);alpha=np.array([float(x['hit_confidence'])for x in rows]);ae=float(np.max(np.abs(alpha-(1-np.exp(-omega)))))
  updates.append(dict(role=F.name,case=case,update=u,source_cells=n,mass=mass,full_variance_m2=var,posterior_mean_error_m=math.hypot(mx-truth[0],my-truth[1]),MAP_error_m=math.hypot(xx[mi]-truth[0],yy[mi]-truth[1]),MAP_tie_cells=len(best),truth_supported=ti is not None,truth_cell_mass=float(p[ti])if ti is not None else None,truth_strict_rank=1+int((p>p[ti]).sum())if ti is not None else None,truth_radius1m_mass=float(p[dist<=1].sum()),truth_radius2m_mass=float(p[dist<=2].sum()),near_source_cell_mass=float(p[ni]),near_source_strict_rank=1+int((p>p[ni]).sum()),fixed_competitor_mass=float(p[ci]),fixed_source_pair_logmargin=margin,max_linear_Omega_alpha_error=ae))
  nx,ny=nav['width']//25,nav['height']//25;idx=np.array([int(x['col'])+nx*int(x['row'])for x in rows]);log=np.array([float(x['hit_log_odds'])for x in rows]);
  with np.errstate(over='ignore'):measured=1-1/(1+np.exp(log))
  grid=np.zeros(nx*ny);maxrel=0.;sims=[c for c in candidates if int(c['update'])==u]
  for c in sorted(sims,key=lambda c:-(int(c['size_x'])*int(c['size_y']))):
   hit=np.frombuffer(blob,dtype='<f4',count=int(c['count']),offset=int(c['offset_bytes']));assert len(hit)==nx*ny
   # Match the author's lerp arithmetic order, including subtract-from-one.
   val=1+((1-np.abs(measured-hit[idx])*.2)-1)*alpha;score=float(np.prod(val));saved=float(c['score']);maxrel=max(maxrel,abs(score-saved)/max(abs(saved),1e-280));x,y,sx,sy=[int(c[k])for k in ['origin_x','origin_y','size_x','size_y']];grid.reshape(ny,nx)[y:y+sy,x:x+sx]=saved
  q=grid[idx];q/=q.sum();err=float(np.max(np.abs(q-p)));assert err<1e-10 and ae<2e-15,(F.name,u,err,ae)
  parity.append(dict(role=F.name,case=case,update=u,candidate_calls=len(sims),map_score_max_relative_error=maxrel,posterior_max_abs_error=err,linear_alpha_max_abs_error=ae))
  lines=[f"{nx} {ny} {nav['origin_x']} {nav['origin_y']} {cs} {n}"]+[f"{x['col']} {x['row']} {x['source_probability']}"for x in rows];cppindex.append(dict(group=len(cppgroups),role=F.name,case=case,update=u,truth_x=truth[0],truth_y=truth[1]));cppgroups.append('\n'.join(lines))
 win=read(rt/'native_window_consumption.csv')if (rt/'native_window_consumption.csv').exists()else[];valid=[x for x in win if x['status']=='CONSUMED'];native=(rt/'native_results.csv').read_text().strip().splitlines()if (rt/'native_results.csv').exists()else[];fields=native[-1].split()if native else[];failed=bool(fields and fields[0]=='FAILED');fields=fields[1:]if failed else fields;last=next((x for x in reversed(updates)if x['role']==F.name),{})
 eps.append(dict(identity='PMFS-O24-PORT-GMRF',role=F.name,case=case,result=res.get('result'),technical_error=res.get('error'),native_declared=bool(fields and not failed),native_search_wall_s=float(fields[1])if fields else None,native_Top5_error_m=float(fields[3])if fields else None,native_mean_error_m=float(fields[2])if fields else None,native_variance_m2=float(fields[5])if fields else None,source_updates=len(grouped),candidate_calls=len(candidates),consumed_windows=len(valid),empty_waits=len(win)-len(valid),truth_supported=last.get('truth_supported'),truth_radius1m_mass=last.get('truth_radius1m_mass'),truth_radius2m_mass=last.get('truth_radius2m_mass'),fixed_source_pair_logmargin=last.get('fixed_source_pair_logmargin')))
 trace=read(rt/'physical_clock_trace.csv')if (rt/'physical_clock_trace.csv').exists()else[];pre=json.loads((rt/'CLOCK_SENSOR_RATE_PREFLIGHT.json').read_text(encoding='utf-8'))if (rt/'CLOCK_SENSOR_RATE_PREFLIGHT.json').exists()else{};start=json.loads((F/'RUN_STARTED.json').read_text(encoding='utf-8'))if (F/'RUN_STARTED.json').exists()else{}
 times.append(dict(role=F.name,native_clock='SYSTEM_WALL',robot_clock_factor=pre.get('real_time_factor'),goal_wall_epoch_s=start.get('wall_time'),goal_observed_robot_ns=start.get('ROS_ns'),stop_window_wall_s=.4,physical_frames_saved=len(trace),physical_first_frame=trace[0]['frame']if trace else None,physical_last_frame=trace[-1]['frame']if trace else None,mapping_limit='World query/frame traces and native consumer windows are timestamped; raw sensor robot receipt clock has no per-message wall field. Goal anchor and5x clock allow bounded association, not exact sensor/TF causal owner.'))
 log=(rt/'launch.log').read_text(errors='replace')if (rt/'launch.log').exists()else'';count=list(map(int,re.findall(r'Total number of simulations: (\d+)',log)));seconds=list(map(float,re.findall(r'Time ellapsed in simulation = ([0-9.eE+-]+) s',log)));cost.append(dict(role=F.name,native_reported_forward_calls=sum(count),captured_valid_candidate_calls=len(candidates),source_batches=len(seconds),source_batch_wall_sum_s=sum(seconds),RNG_trace_bytes=(rt/'native_rng_states.jsonl').stat().st_size if (rt/'native_rng_states.jsonl').exists()else 0,candidate_float_bytes=len(blob),new_worlds=0,AIMMD=0))
write(A/'O24_EPISODES.csv',eps);write(A/'O24_SOURCE_UPDATE_METRICS.csv',updates);write(A/'NATIVE_REPLAY_PARITY.csv',parity);write(A/'CPP_READOUT_INDEX.csv',cppindex);write(A/'TIME_DOMAINS_AND_LIMITS.csv',times);write(A/'FORWARD_AND_RECORDING_COST.csv',cost)
(A/'native_readout_input.txt').write_text(str(len(cppgroups))+'\n'+'\n'.join(cppgroups)+'\n',encoding='utf-8')
combined=[]
for case in ['A2','B2']:
 for identity,rr in [('PMFS-O24-PORT-GMRF',[x for x in eps if x['case']==case and x['native_Top5_error_m']is not None]),('PMFS-P24-PAPER-FIRST',[x for x in read(P24/'analysis/EPISODES.csv')if x['phase']=='new'and x['case']==case])]:
  if rr:
   errs=[float(x['native_Top5_error_m']if identity.startswith('PMFS-O24')else x['native_top5_error_m'])for x in rr];tt=[float(x['native_search_wall_s'])for x in rr];combined.append(dict(case=case,identity=identity,n=len(rr),mean_error_m=statistics.mean(errs),mean_wall_search_s=statistics.mean(tt),min_error_m=min(errs),max_error_m=max(errs),comparison_scope='Same existing physical realization, different rules/trajectories/observations; historical comparison, not paired single-factor causal gain or independent worlds'))
write(A/'O24_P24_SEPARATE_RESULTS.csv',combined)
put(A/'ANALYSIS_STATUS.json',dict(completed=len(eps),updates=len(updates),candidate_maps=sum(x['candidate_calls']for x in eps),new_worlds=0,AIMMD=0))
print(json.dumps(dict(episodes=eps,comparison=combined),ensure_ascii=False))
