"""Only score stored responses; no forward simulation, ROS or invented internal state."""
from pathlib import Path
import csv,json,math,re
import numpy as np
R=Path(__file__).resolve().parent
P=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rs):
    with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
O=R/'analysis_v2';O.mkdir(exist_ok=False)
summaries=[];leaf_scores=[];cells=[];checks=[];alpha_stats=[]
for c in P['contexts']:
    d=R/'fixtures'/c['key'];inp=rows(d/'input.csv');cand=rows(d/'candidates.csv');meta=c['metadata'];n=len(inp)
    free=np.array([r['occupancy']=='1'for r in inp]);ii=np.flatnonzero(free)
    computed={int(r['serial']):r for r in rows(R/'execution'/(c['key']+'.csv'))}
    logs={r['candidate_id']:{k:float(computed[int(r['serial'])][k])for k in ['native_logscore','paper_eq6_logscore']}for r in cand}
    max_log_error=max(abs(float(r['logscore'])-logs[r['candidate_id']]['native_logscore'])for r in cand)
    assert max_log_error<=P['tolerances']['logscore_abs'],(c['key'],max_log_error)
    orig=np.array([float(r['confidence'])for r in inp]);omega=np.array([float(r['omega'])for r in inp]);eq6=1-np.exp(-omega**2/c['weight']**2)
    error=max(abs(orig[free]-(1-np.exp(-omega[free]/c['weight']**2))))
    assert error<P['tolerances']['confidence_abs']
    tree=[r for r in rows(d/'final_tree.csv')if r['has_children']=='0'and r['value']=='1']
    owner=np.full(n,'',dtype=object);density={k:np.full(n,-np.inf)for k in ['native_logscore','paper_eq6_logscore']}
    for t in tree:
        idx=np.array([x+y*meta['width']for y in range(int(t['origin_j']),int(t['origin_j'])+int(t['size_j']))for x in range(int(t['origin_i']),int(t['origin_i'])+int(t['size_i']))])
        assert np.all(free[idx])and np.all(owner[idx]=='')
        name=t['node_id'];owner[idx]=name
        for k in density:density[k][idx]=logs[name][k]
        leaf_scores.append(dict(context=c['key'],leaf=name,area_cells=len(idx),**logs[name],eq6_minus_native_logscore=logs[name]['paper_eq6_logscore']-logs[name]['native_logscore']))
    assert np.all((owner!='')==free)
    q={}
    for k,v in density.items():z=np.exp(v[free]-np.max(v[free]));a=np.zeros(n);a[free]=z/z.sum();q[k]=a
    archive=np.fromfile(d/'posterior.f64','<f8');post_error=float(np.max(abs(q['native_logscore']-archive)))
    assert post_error<P['tolerances']['native_posterior_abs'],(c['key'],post_error)
    cfg=(d/'resolved_GSL_parameters.yaml').read_text()
    def param(key):return float(re.search(r'^\s*'+re.escape(key)+r':\s*([-+0-9.eE]+)\s*$',cfg,re.M)[1])
    truth=np.array([param('ground_truth_x'),param('ground_truth_y')])
    # The archived JSON origin has printed precision. Float casting follows the native grid convention.
    ti=int(np.float32(np.float32(truth[0])-np.float32(meta['origin_x']))/np.float32(meta['cell_size']))
    tj=int(np.float32(np.float32(truth[1])-np.float32(meta['origin_y']))/np.float32(meta['cell_size']))
    truthidx=ti+tj*meta['width'];truth_supported=bool(0<=ti<meta['width'] and 0<=tj<meta['height'] and free[truthidx])
    prior=np.array([float(r['prior_posterior'])for r in inp]);comp=int(ii[np.argmax(prior[free])])
    x=np.float32(meta['origin_x'])+(np.arange(n)%meta['width']+.5).astype('f4')*np.float32(meta['cell_size'])
    y=np.float32(meta['origin_y'])+(np.arange(n)//meta['width']+.5).astype('f4')*np.float32(meta['cell_size'])
    xy=np.c_[x,y].astype(float);dist=np.linalg.norm(xy-truth,axis=1)
    tv=float(.5*np.sum(abs(q['native_logscore']-q['paper_eq6_logscore'])))
    for arm,k in [('author_confidence','native_logscore'),('paper_eq6_only','paper_eq6_logscore')]:
        a=q[k];mean=(a[:,None]*xy).sum(axis=0);m=int(np.argmax(a));o=owner[truthidx]
        summaries.append(dict(context=c['key'],case=c['case'],update=c['update'],arm=arm,tree_frozen=True,source_prediction_implementation='2026_corrected_wind',truth_cell=truthidx,truth_supported=truth_supported,truth_leaf=o or None,prior_max_competitor_cell=comp,prior_max_competitor_is_not_independent_of_native_history=True,truth_logscore=float(density[k][truthidx]) if truth_supported else None,truth_minus_prior_max_logscore=float(density[k][truthidx]-density[k][comp]) if truth_supported else None,truth_strict_rank=int(1+np.sum(a[free]>a[truthidx])) if truth_supported else None,truth_cell_mass=float(a[truthidx]) if truth_supported else 0.,truth_leaf_mass=float(a[owner==o].sum()) if truth_supported else None,mass_within_1p5m=float(a[dist<=1.5].sum()),map_error_m=float(dist[m]),posterior_mean_error_m=float(np.linalg.norm(mean-truth)),full_probability_variance_m2=float(np.sum(a*np.sum((xy-mean)**2,axis=1))),tv_from_native=tv))
    for i in ii:cells.append(dict(context=c['key'],cell_index=int(i),omega=float(omega[i]),native_confidence=float(orig[i]),paper_eq6_confidence=float(eq6[i]),leaf=owner[i],native_source_probability=float(q['native_logscore'][i]),paper_eq6_source_probability=float(q['paper_eq6_logscore'][i])))
    alpha_stats.append(dict(context=c['key'],free_cells=len(ii),alpha_increased=int(np.sum(eq6[free]>orig[free]+1e-14)),alpha_decreased=int(np.sum(eq6[free]<orig[free]-1e-14)),max_alpha_abs_change=float(np.max(abs(eq6[free]-orig[free]))),mean_alpha_abs_change=float(np.mean(abs(eq6[free]-orig[free])))))
    checks.append(dict(context=c['key'],archived_candidates=len(cand),final_leaves=len(tree),source_support_cells=len(ii),truth_supported=truth_supported,max_native_logscore_error=max_log_error,max_native_confidence_error=float(error),max_native_posterior_error=post_error))
write(O/'SOURCE_COMPARISON.csv',summaries);write(O/'LEAF_SCORES.csv',leaf_scores);write(O/'CELL_CONFIDENCE_AND_SOURCE.csv',cells);write(O/'CONFIDENCE_CHANGE.csv',alpha_stats)
put(O/'PARITY_CHECKS.json',dict(status='PASS_FOUR_CONTEXTS_NATIVE_SCORE_CONFIDENCE_POSTERIOR',checks=checks))
status=dict(status='EQ6_COMPONENT_AND_FIXED_TREE_SENSITIVITY_COMPLETE_STRICT_PAPER_BASELINE_HOLD',new_forward_calls=0,new_ros=0,new_worlds=0,AIMMD_resumed=False,paper_eq6_aligned=True,age_radius_resolved=False,original_experiment_commit_identified=False,all_algorithm_parameters_paper_matched=False,full_paper_reproduction=False,closed_loop_gain_tested=False,formal_figures_8_10_11_statistical_comparison_eligible=False,limitations=['Only the Eq6 confidence exponent changes. Candidate maps/history/score coefficient/final tree remain frozen.','2026 corrected-wind diagnostic is not the author 2024 experiment.','B2 truth cell674 is outside the stored legal source support. Its zero source mass is a support fact, not an Eq6 failure or improvement.','Eq6 could change adaptive refinement and movement; these alternative trajectories are not reconstructed.','No age-dependent radius law is invented; no historical Omega or RNG is fabricated.','No claim that lower diagnostic error is innovation or general improvement.'])
put(O/'DECISION.json',status)
print(json.dumps(dict(status=status['status'],contexts=len(checks),max_logscore_error=max(r['max_native_logscore_error']for r in checks),max_posterior_error=max(r['max_native_posterior_error']for r in checks))))
