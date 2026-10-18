from pathlib import Path
import csv,hashlib,json,math,collections,statistics,os
import numpy as np
R=Path(__file__).resolve().parent;OLD=Path(os.environ.get('PMFS_AUDIT_PREVIOUS_ROOT',str(R.parent/'PMFS_PAPER_FIRST_ROS_QUAL_20261017')));A=R/'analysis';A.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open()))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rows):
 if not rows:return
 with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def metrics(rows,prob,truth):
 prob=np.asarray(prob,dtype=float);prob=prob/prob.sum();xs=np.array([float(r['x_m'])for r in rows]);ys=np.array([float(r['y_m'])for r in rows]);mx=float(prob@xs);my=float(prob@ys);var=float(prob@((xs-mx)**2+(ys-my)**2));k=math.ceil(.05*len(rows));order=np.argsort(-prob,kind='stable');top=order[:k];tx=float(prob[top]@xs[top]/prob[top].sum());ty=float(prob[top]@ys[top]/prob[top].sum());cs=float(rows[0]['cell_size_m'])
 # Grid membership is half-open; A2 truth x=1.75 lies exactly on a boundary.
 # An inclusive distance-to-center test would incorrectly count two source cells.
 ox=float(rows[0]['x_m'])-(int(rows[0]['col'])+.5)*cs;oy=float(rows[0]['y_m'])-(int(rows[0]['row'])+.5)*cs
 truth_col=math.floor((truth[0]-ox)/cs);truth_row=math.floor((truth[1]-oy)/cs)
 hit=[i for i,r in enumerate(rows)if int(r['col'])==truth_col and int(r['row'])==truth_row];assert len(hit)<=1
 return dict(variance_m2=var,declares_by_variance=var<1,top5_error_m=math.hypot(tx-truth[0],ty-truth[1]),posterior_mean_error_m=math.hypot(mx-truth[0],my-truth[1]),posterior_mean_x=mx,posterior_mean_y=my,true_source_supported=bool(hit),true_cell_mass=float(prob[hit].sum())if hit else 0.,true_strict_rank=1+int((prob>prob[hit[0]]).sum())if hit else None,effective_source_cells=float(1/(prob@prob)))
episodes=[];updates=[];controls=[];parity=[];native_readout_inputs=[];native_readout_index=[]
sources=[(OLD/'cases'/'PF24_A2_T02','previous'),(OLD/'cases'/'PF24_B2_Q01','previous')]+[(p,'new')for p in sorted((R/'cases').iterdir())if p.is_dir()]
for F,phase in sources:
 runtime=F/'runtime';post=runtime/'native_posterior_updates.csv';resultfile=F/'RUN_RESULT.json'
 if not resultfile.exists():continue
 result=json.loads(resultfile.read_text());meta=json.loads((F/'CASE_META.json').read_text());case=meta['case'];truth=meta['source_xyz'];case_rows=read(post)if post.exists()else[]
 grouped=collections.defaultdict(list)
 for row in case_rows:grouped[int(row['update'])].append(row)
 for u,rows in grouped.items():
  vals=[float(r['source_probability'])for r in rows];m=metrics(rows,vals,truth);updates.append(dict(role=F.name,phase=phase,case=case,update=u,source_cells=len(rows),mass=sum(vals),**m))
 native=(runtime/'native_results.csv').read_text().strip().splitlines()if (runtime/'native_results.csv').exists()else[]
 search=None;err=None
 if native:
  fields=native[-1].split();fields=fields[1:]if fields[0]=='FAILED'else fields
  search=float(fields[1]);err=float(fields[3])
 win=read(runtime/'native_window_consumption.csv')if (runtime/'native_window_consumption.csv').exists()else[];valid=[r for r in win if r['status']=='CONSUMED'];c=json.loads((runtime/'CLOCK_SENSOR_RATE_PREFLIGHT.json').read_text())if (runtime/'CLOCK_SENSOR_RATE_PREFLIGHT.json').exists()else{}
 episodes.append(dict(role=F.name,phase=phase,case=case,result=result.get('result'),error=result.get('error'),native_search_wall_s=search,native_top5_error_m=err,source_updates=len(grouped),consumed_windows=len(valid),gas_hit_windows=sum(float(r['concentration_mean_ppm'])>.1 for r in valid),variance_m2=updates[-1]['variance_m2']if grouped else None,truth_supported=updates[-1]['true_source_supported']if grouped else None,robot_clock_factor=c.get('real_time_factor')))
 candidates=runtime/'native_candidate_maps.csv';binary=runtime/'native_candidate_maps.f32'
 if not candidates.exists():continue
 cs=read(candidates);blob=binary.read_bytes();nav=json.loads((runtime/'NAVIGATION_MAP_METADATA.json').read_text());nx=nav['width']//25;ny=nav['height']//25
 for u,rows in grouped.items():
  sims=[v for v in cs if int(v['update'])==u];idx=np.array([int(r['col'])+nx*int(r['row'])for r in rows]);logodds=np.array([float(r['hit_log_odds'])for r in rows]);omega=np.array([float(r['hit_omega'])for r in rows]);actualalpha=np.array([float(r['hit_confidence'])for r in rows]);
  with np.errstate(over='ignore'):measured=1-1/(1+np.exp(logodds))
  grid={key:np.zeros(nx*ny,dtype=float)for key in ['paper_alpha_D1','paper_alpha_D02','code_alpha_D1','code_alpha_D02']};nativegrid=np.zeros(nx*ny);maxrel=0
  # All coarse regions are written first, then their children; sorting by area
  # recreates the native overwrite rule independently of OpenMP completion order.
  for v in sorted(sims,key=lambda v:-(int(v['size_x'])*int(v['size_y']))):
   hit=np.frombuffer(blob,dtype='<f4',count=int(v['count']),offset=int(v['offset_bytes']));assert len(hit)==nx*ny
   delta=np.abs(measured-hit[idx]);ox,oy,sx,sy=[int(v[k])for k in ['origin_x','origin_y','size_x','size_y']]
   native=float(v['score']);actualprod=float(np.prod(1-actualalpha*delta));maxrel=max(maxrel,abs(actualprod-native)/max(abs(native),1e-280))
   nativegrid.reshape(ny,nx)[oy:oy+sy,ox:ox+sx]=native
   for name,arr in grid.items():
    alpha=actualalpha if name.startswith('paper_')else 1-np.exp(-omega)
    D=1. if name.endswith('D1')else .2
    score=float(np.prod(1-alpha*D*delta));arr.reshape(ny,nx)[oy:oy+sy,ox:ox+sx]=score
  q=nativegrid[idx];q=q/q.sum();original=np.array([float(r['source_probability'])for r in rows]);diff=float(np.max(np.abs(q-original)));assert diff<1e-11,(F.name,u,diff)
  p=grid['paper_alpha_D1'][idx];p=p/p.sum();auditdiff=float(np.max(np.abs(p-original)));assert auditdiff<1e-10,(F.name,u,auditdiff)
  parity.append(dict(role=F.name,case=case,update=u,candidate_calls=len(sims),native_map_score_max_relative_error=maxrel,native_tree_posterior_max_abs_error=diff,paper_formula_max_abs_error=auditdiff,full_grid_cells=nx*ny,legal_source_cells=len(rows)))
  for name,arr in grid.items():
   controls.append(dict(role=F.name,case=case,update=u,control=name,fixed_native_tree=True,new_robot_observations=False,**metrics(rows,arr[idx],truth)))
   q=arr[idx]/arr[idx].sum()
   native_readout_index.append(dict(group=len(native_readout_inputs),role=F.name,case=case,update=u,control=name,true_x=truth[0],true_y=truth[1]))
   lines=[f"{nx} {ny} {nav['origin_x']} {nav['origin_y']} {nav['resolution']*25} {len(rows)}"]
   lines.extend(f"{row['col']} {row['row']} {value:.17g}"for row,value in zip(rows,q))
   native_readout_inputs.append('\n'.join(lines))
write(A/'EPISODES.csv',episodes);write(A/'SOURCE_UPDATES.csv',updates);write(A/'FIXED_HISTORY_FORMULA_CONTROLS.csv',controls);write(A/'EXACT_NATIVE_REPLAY_PARITY.csv',parity)
(A/'native_readout_input.txt').write_text(str(len(native_readout_inputs))+'\n'+'\n'.join(native_readout_inputs)+'\n')
write(A/'NATIVE_READOUT_INDEX.csv',native_readout_index)
summary=[]
for case in ['A2','B2']:
 for phase in ['new','all']:
  vals=[e for e in episodes if e['case']==case and e['native_top5_error_m']is not None and(phase=='all'or e['phase']=='new')]
  if vals:summary.append(dict(case=case,scope=phase,n=len(vals),mean_error_m=statistics.mean(v['native_top5_error_m']for v in vals),min_error_m=min(v['native_top5_error_m']for v in vals),max_error_m=max(v['native_top5_error_m']for v in vals),mean_search_wall_s=statistics.mean(v['native_search_wall_s']for v in vals),note='Repeated algorithm trials on the same generated physical realization; not independent gas-world repetitions or author30-run reproduction'))
write(A/'PAPER_COMPARISON.csv',summary)
put(A/'ANALYSIS_STATUS.json',dict(episodes=len(episodes),new_episodes=sum(v['phase']=='new'for v in episodes),updates=len(updates),native_replay_checks=len(parity),formula_controls=len(controls)))
print(json.dumps(dict(episodes=episodes,summary=summary,parity=parity),ensure_ascii=False))
