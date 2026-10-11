"""Fixed final native libraries and actual native per-block map lineage; zero forwards."""
from common_n import *
import csv,numpy as np,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');truth=load(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json');shape=(45,34);free=np.array([r['occupancy']=='1' for r in rows(CORE/'native_inputs/inputs/DERIVED/input.csv')]);blocks=[];supports=[];contributions=[];prefix=[]
for oid,tr in truth.items():
 folder=D/f'native_cold_results/N0_{oid}';u=folder/'update_2';cand={r['candidate_id']:r for r in rows(u/'candidates.csv')};leaves=[r for r in rows(u/'final_tree.csv') if r['has_children']=='0'];post=np.fromfile(u/'posterior.f64',dtype='<f8');peak=int(np.argmax(post));sx,sy=tr['source_xyz'][:2]
 ix=int((np.float32(sx)-np.float32(-7.55))/np.float32(.25));iy=int((np.float32(sy)-np.float32(-7.88))/np.float32(.25));tcell=ix+34*iy
 def contains(l,cell):
  i,j=cell%34,cell//34;ox,oy,nx,ny=[int(l[k]) for k in ['origin_i','origin_j','size_i','size_j']];return ox<=i<ox+nx and oy<=j<oy+ny
 tl=next(l for l in leaves if contains(l,tcell));wl=next(l for l in leaves if contains(l,peak));tc=cand[tl['node_id']];wcand=cand[wl['node_id']]
 qtrue=np.fromfile(u/tc['map_file'],dtype='<f4').astype(float);qwrong=np.fromfile(u/wcand['map_file'],dtype='<f4').astype(float)
 mr=rows(folder/'final_map.csv');pr=np.array([float(r['probability']) for r in mr]);cf=np.array([float(r['confidence']) for r in mr]);lt=np.log(1-.4*np.abs(pr-qtrue)*cf);lw=np.log(1-.4*np.abs(pr-qwrong)*cf)
 assert abs(math.fsum(lt[free])-float(tc['logscore']))<1e-10;assert abs(math.fsum(lw[free])-float(wcand['logscore']))<1e-10
 visited={int((np.float32(float(e['x']))-np.float32(-7.55))/.25)+34*int((np.float32(float(e['y']))-np.float32(-7.88))/.25) for e in rows(CORE/f'native_inputs/events/{oid}.csv')}
 for l,c,role in [(tl,tc,'TRUE_LEAF'),(wl,wcand,'FINAL_MAP_LEAF')]:
  members=np.array([contains(l,i) and free[i] for i in range(len(free))]);points=np.fromfile(u/c['points_file'],dtype='<f4').reshape(-1,2)
  supports.append(dict(oid=oid,role=role,candidate_id=l['node_id'],rectangle_cells=int(l['size_i'])*int(l['size_j']),legal_cells=int(members.sum()),leaf_probability_mass=float(post[members].sum()),single_cell_density=float(post[members][0]),release_x_min=float(points[:,0].min()),release_x_max=float(points[:,0].max()),release_y_min=float(points[:,1].min()),release_y_max=float(points[:,1].max()),release_count=len(points),exact_point_source=False))
 for i in np.flatnonzero(free):contributions.append(dict(oid=oid,cell=int(i),direct_stop_cell=i in visited,observed_probability=pr[i],confidence=cf[i],true_prediction=qtrue[i],final_peak_prediction=qwrong[i],true_minus_peak_log_factor=lt[i]-lw[i]))
 previous=0;prob=np.full(len(free),.3);confidence=np.zeros(len(free));line=rows(folder/'event_cell_lineage.csv')
 for b in range(50):
  rb=line[b*447:(b+1)*447];assert len(rb)==447 and all(int(r['block'])==b for r in rb)
  for r in rb:i=int(r['cell_index']);prob[i]=float(r['probability_after']);confidence[i]=float(r['confidence_after'])
  delta=np.log(1-.4*np.abs(prob-qtrue)*confidence)-np.log(1-.4*np.abs(prob-qwrong)*confidence)
  margin=math.fsum(delta[free]);direct=math.fsum(delta[[i for i in visited if free[i]]]);blocks.append(dict(oid=oid,block_count=b+1,stop_index=b//5,common_final_library=True,true_minus_final_peak_log_margin=margin,margin_change_this_block=margin-previous,direct_stop_cells_log_margin=direct,other_cells_log_margin=margin-direct,independent_observation_units_claimed=False));previous=margin
 assert abs(previous-(float(tc['logscore'])-float(wcand['logscore'])))<1e-10
 # Every final leaf, same library, against saved prefixes: conditional diagnostic, no new tree branch.
 for count in [20,35,50]:
  m=rows(folder/f'map_blocks_{count}.csv');p=np.array([float(x['probability']) for x in m]);c=np.array([float(x['confidence']) for x in m]);raw=np.zeros(len(free))
  for leaf in leaves:
   cr=cand[leaf['node_id']];q=np.fromfile(u/cr['map_file'],dtype='<f4').astype(float);score=math.exp(math.fsum(np.log(1-.4*np.abs(p-q)*c)[free]));raw[np.array([contains(leaf,i) and free[i] for i in range(len(free))])]=score
  raw/=raw.sum();imap=int(np.argmax(raw));x=np.float32(-7.55)+(np.arange(len(free))%34+.5)*.25;y=np.float32(-7.88)+(np.arange(len(free))//34+.5)*.25
  prefix.append(dict(oid=oid,blocks=count,library='final_update2_native_final_leaves',MAP_error_m=float(math.hypot(x[imap]-sx,y[imap]-sy)),true_cell_probability=float(raw[tcell]),true_rank_mid=int((raw[free]>raw[tcell]).sum())+1+(int((raw[free]==raw[tcell]).sum())-1)/2,variance=float(np.sum(raw*((x-np.sum(raw*x))**2+(y-np.sum(raw*y))**2)))))
wc(CORE/'QUALIFIED_NATIVE_LEAF_SUPPORT_AND_RELEASE.csv',supports);wc(CORE/'QUALIFIED_NATIVE_PAIR_CELL_CONTRIBUTIONS.csv',contributions);wc(CORE/'QUALIFIED_NATIVE_MEASUREMENT_BLOCK_MARGIN_LINEAGE.csv',blocks);wc(CORE/'QUALIFIED_NATIVE_FIXED_LIBRARY_PREFIX_SCORES.csv',prefix)
dump(CORE/'QUALIFIED_D_STAGE_SCOPE.json',dict(status='COMPLETED_REGISTERED_EXISTING_LIBRARY_DIAGNOSTICS',new_forwards=0,blocks=50,independent_stops=10,independent_realizations=12,
 adaptive_refinement='Recorded leaf geometry, release distributions, area mass versus cell density; no fair atomic candidate library, so refinement mechanism not excluded',
 evidence_correlation='Exact native block-to-grid lineage and fixed-prediction score changes; no cell deletion, no repaired-score method claim, no independence assumption',
 finite_references='Original2 / extra2 / all4 / individual0,1 use identical score and supports; no IQR or temperature change',
 limits='Postselected final true/peak pair and final adaptive library; conditional attribution, not full causal separation or independent holdout'))
print(json.dumps({'status':'PASS_D_CONDITIONAL_LINEAGE','native_tasks':len(truth),'block_rows':len(blocks),'cell_rows':len(contributions)}))
