"""Independent arithmetic on actual native outputs, no production scorer import."""
from common_n import *
import csv,math,numpy as np,shutil
HOST_DATA=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
def rows(p):
 with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,rr):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]),lineterminator='\n');w.writeheader();w.writerows(rr)
def independent_log(inp,q,D):
 logits=np.array([float(r['logOdds']) for r in inp]);pr=np.where(logits>=0,1/(1+np.exp(-logits)),np.exp(logits)/(1+np.exp(logits)))
 confidence=np.array([float(r['confidence']) for r in inp]);free=np.array([r['occupancy']=='1' for r in inp]);f=1-D*abs(pr-q.astype(float))*confidence
 assert (f[free]>0).all();return math.fsum(math.log(float(x)) for x in f[free])
def main():
 anchor=[]
 for a in load(CORE/'HISTORICAL_ANCHOR_PLAN.json'):
  label=a['label'];old=Path(a['expected_snapshot']);inp=rows(old/'input.csv');cand=rows(old/'candidates.csv');new=HOST_DATA/'native_results'/(label+'_saved_map_scores')
  rr=rows(new/'scores.csv');assert len(rr)==len(cand)
  D=.3 if label=='E3' else .4;differences=[];reconstruct=np.zeros(len(inp));qmax=0
  width=load(old/'metadata.json')['width']
  for c,r in zip(cand,rr):
   q=np.fromfile(old/c['map_file'],dtype='<f4');v=independent_log(inp,q,D)
   differences.append(abs(v-float(r['log_score'])));qmax=max(qmax,abs(float(r['score'])-float(c['score'])))
   ox,oy,sx,sy=[int(c[k]) for k in ['origin_i','origin_j','size_i','size_j']]
   for y in range(oy,oy+sy):
    for x in range(ox,ox+sx):reconstruct[x+y*width]=float(r['score'])
  reconstruct[[r['occupancy']!='1' for r in inp]]=0;reconstruct/=reconstruct.sum()
  actual=np.fromfile(old/'posterior.f64',dtype='<f8');postdiff=float(max(abs(reconstruct-actual)))
  forward=HOST_DATA/'native_results'/(label+'_short_forward_OFF')/'forward';newcand=rows(forward/'candidates.csv')[0];first=cand[0]
  mapdiff=float(max(abs(np.fromfile(forward/newcand['map_file'],dtype='<f4')-np.fromfile(old/first['map_file'],dtype='<f4'))))
  pointdiff=float(max(abs(np.fromfile(forward/newcand['points_file'],dtype='<f4')-np.fromfile(old/first['points_file'],dtype='<f4'))))
  rng_same=newcand['rng_after']==first['rng_after'] and newcand['gaussian_index_after']==first['gaussian_index_after']
  passed=max(differences)<1e-10 and qmax<1e-14 and postdiff<1e-12 and mapdiff==0 and pointdiff==0 and rng_same
  anchor.append(dict(label=label,status='PASS' if passed else 'FAIL',saved_candidates=len(rr),maximum_independent_logscore_difference=max(differences),maximum_historical_score_difference=qmax,
   maximum_final_posterior_abs_difference=postdiff,short_forward_map_max_abs=mapdiff,short_forward_release_point_max_abs=pointdiff,RNG_and_cache_phase_after_same=rng_same))
 dump(CORE/'N0_ANCHORS.json',dict(status='PASS' if all(r['status']=='PASS' for r in anchor) else 'FAIL',anchors=anchor,original_snapshots_modified=False,new_navigation_goals=0))
 truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json');result=[];cellrows=[]
 for p in sorted((HOST_DATA/'native_results').glob('N0_*')):
  if not (p/'EXECUTION.json').exists():continue
  oid=p.name[3:];meta=load(BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_2/metadata.json');sx,sy=truth[oid]['source_xyz'][:2]
  ledger=rows(p/'update_ledger.csv');freeze={q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file()}
  dump(CORE/'evaluation_only'/(oid+'_NATIVE_OUTPUT_FREEZE_BEFORE_METRICS.json'),freeze)
  for lr in ledger:
   uid=int(lr['update']);d=p/('update_'+str(uid));post=np.fromfile(d/'posterior.f64',dtype='<f8');free=np.array([r['occupancy']=='1' for r in rows(CORE/'native_inputs/inputs/DERIVED/input.csv')]);n=len(post)
   i=np.arange(n)%meta['width'];j=np.arange(n)//meta['width'];x=np.float32(meta['origin_x'])+np.float32((i+.5)*.25);y=np.float32(meta['origin_y'])+np.float32((j+.5)*.25)
   true_i=int(np.float32((np.float32(sx)-np.float32(meta['origin_x']))/.25));true_j=int(np.float32((np.float32(sy)-np.float32(meta['origin_y']))/.25));true_index=true_i+true_j*meta['width'];assert free[true_index]
   maxidx=int(np.argmax(post));dist=np.hypot(x-sx,y-sy);sumcheck=abs(post.sum()-1);assert sumcheck<1e-12
   cand=rows(d/'candidates.csv');inputrows=rows(d/'input_full.csv')
   # Check every candidate against frozen native formula, not only final error.
   logdiff=max(abs(independent_log(inputrows,np.fromfile(d/r['map_file'],dtype='<f4'),.4)-float(r['logscore'])) for r in cand)
   assert logdiff<1e-10
   row=dict(oid=oid,public_original_role=truth[oid]['role'],update=uid,blocks=int(lr['blocks']),candidate_forwards=len(cand),variance=float(lr['variance']),
     native_Top5_error_m=float(math.hypot(float(lr['top5_x'])-sx,float(lr['top5_y'])-sy)),MAP_error_m=float(dist[maxidx]),
     posterior_mean_error_m=float(math.hypot(float(lr['mean_x'])-sx,float(lr['mean_y'])-sy)),source1m_mass=float(post[dist<=1].sum()),
     true_source_cell_probability=float(post[true_index]),true_cell_rank_mid=float((post[free]>post[true_index]).sum()+1+((post[free]==post[true_index]).sum()-1)/2),
     first_native_variance_convergence=lr['official_rule_first_convergence'],maximum_logscore_verification_abs=logdiff,source_support_legal=True,
     classification='N0_NATIVE_CONTROLLED_FIXED50_HISTORY_REPLAY_NOT_OFFICIAL_NEW_ACTION')
   result.append(row)
   for c in range(n):cellrows.append(dict(oid=oid,update=uid,cell_index=c,free=int(free[c]),posterior=post[c]))
 if result:write(CORE/'NATIVE_COMPLETE_MAP_RESULTS.csv',result);write(CORE/'NATIVE_COMPLETE_MAP_POSTERIORS.csv',cellrows)
 print(json.dumps(dict(anchors=anchor,completed_public_native_tasks=len({r['oid'] for r in result}),native_updates=len(result),partial_completion_explicit=True),indent=2))
if __name__=='__main__':main()
