"""Finite-world, equal-budget screen. Select never accepts source truth.

All likelihood products are formed BEFORE nuisance marginalization or
profiling. This is essential: one latent transport world spans both actions.
"""
import argparse,csv,hashlib,json,pathlib,time
import numpy as np

def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def entropy(p):
    p=np.asarray(p,dtype=float)
    return -np.sum(p*np.log(np.maximum(p,1e-300)),axis=-1)
def likelihood(p,acts):
    q=np.ones((*p.shape[:2],1))
    for a in acts:
        v=p[:,:,a,None]
        q=np.concatenate([q*(1-v),q*v],axis=-1)
    return q
def information(p,prior,acts,joint=False):
    q=likelihood(p,acts)
    marginal=np.einsum('s,sno->o',prior,q)/p.shape[1]
    conditional=np.einsum('s,sn->',prior,entropy(q))/p.shape[1] if joint else np.dot(prior,entropy(q.mean(axis=1)))
    return float(max(0.,entropy(marginal)-conditional))
def separation_matrix(p,acts):
    """Worst pair of shared worlds for every distinct source pair.

    Use source-row blocks to bound memory; for fixed s,t, world indices are
    held fixed while multiplying affinities across all actions.
    """
    s,n,_=p.shape;out=np.empty((s,s))
    for i in range(s):
        bc=np.ones((n,s,n))
        for a in acts:
            x=p[i,:,a][:,None,None];y=p[:,:,a][None,:,:]
            bc *= np.sqrt(x*y)+np.sqrt((1-x)*(1-y))
        out[i]=np.clip(1-bc.max(axis=(0,2)),0,1)
    return out
def separation_objective(p,prior,acts):
    d=separation_matrix(p,acts);off=~np.eye(len(prior),dtype=bool)
    w=np.outer(prior,prior)
    return float((d*w)[off].sum()/w[off].sum()),float(d[off].min())
def projected_fraction(a,b):
    u,s,_=np.linalg.svd(b,full_matrices=False)
    rank=int(np.sum(s>(s[0]*1e-8 if len(s) and s[0]>0 else 1e-12)))
    residual=a-u[:,:rank]@(u[:,:rank].T@a)
    den=float(np.dot(a,a))
    return (float(np.clip(np.dot(residual,residual)/den,0,1)) if den>1e-20 else None),rank
def load(design_path,bank):
    d=json.loads(design_path.read_text());meta=json.loads((bank/'COMPLETE.json').read_text())
    assert meta['worlds']==35 and meta['sources']==len(d['sources'])
    p=np.memmap(bank/'responses.f32',dtype='<f4',mode='r',shape=(35,len(d['sources']),meta['cells']))
    assert (bank/'responses.f32').stat().st_size==p.size*4
    assert np.isfinite(p).all() and p.min()>=0 and p.max()<=1
    return d,p
def select(design_path,bank,out):
    begin=time.perf_counter();d,full=load(design_path,bank)
    leaves=np.array([i for i,s in enumerate(d['sources']) if s['measure']>0])
    roots=np.array([i for i,s in enumerate(d['sources']) if s['root']])
    prior=np.array([d['sources'][i]['measure'] for i in leaves],float);prior/=prior.sum()
    actioncells=[a['cell_index'] for a in d['actions']]
    p=np.asarray(full[:27,leaves,:][:,:,actioncells],float).transpose(1,0,2)
    # Native scalar heuristic, point-response approximation, original weights.
    weights=np.array([d['sources'][i]['native_score'] for i in roots]);assert weights.sum()>0
    weights/=weights.sum();q=np.asarray(full[13,roots,:][:,actioncells],float)
    mean=weights@q;variance=weights@((q-mean)**2)
    conf={r['cell_index']:r['confidence'] for r in d['confidence']}
    with (bank/'visibility_weight.csv').open() as f:vis={int(r['cell_index']):float(r['weight']) for r in csv.DictReader(f)}
    native=variance*np.array([(1-conf[c])*vis[c] for c in actioncells])
    pairs=d['pairs']; assert pairs
    singles={j:[information(p,prior,[a],j) for a in range(len(actioncells))] for j in [False,True]}
    def tie(pair):return (-pair['length_m'],-actioncells[pair['a']],-actioncells[pair['b']])
    def greedy(joint):
        first=max(sorted(set(x['a'] for x in pairs)),key=lambda a:(singles[joint][a],-actioncells[a]))
        return max((x for x in pairs if x['a']==first),key=lambda x:(information(p,prior,[x['a'],x['b']],joint),*tie(x)))
    def native_score(pair,a):
        # Distances in cells, matching the original distance field units.
        distance=(len(pair['first_path'])-1) if a==0 else (len(pair['second_path'])-1)
        return native[pair['a'] if a==0 else pair['b']]/(distance+.1)**.15
    first=max(pairs,key=lambda x:(native_score(x,0),*tie(x)))['a']
    available=[x for x in pairs if x['a']==first and x['b']!=first]
    if not available:available=[x for x in pairs if x['a']==first]
    selected={'native_acquisition_heuristic':max(available,key=lambda x:(native_score(x,1),*tie(x))),
              'one_step_source_MI':greedy(False),'one_step_joint_MI':greedy(True)}
    cache={};objectives=[]
    for pair in pairs:
        key=tuple(sorted([pair['a'],pair['b']]))
        if key not in cache:cache[key]=separation_objective(p,prior,key)
        objectives.append((*cache[key],*tie(pair)))
    selected['two_step_deconfounding']=pairs[max(range(len(pairs)),key=lambda i:objectives[i])]
    strategies={}
    for name,pair in selected.items():
        acts=[pair['a'],pair['b']];sep=cache.get(tuple(sorted(acts))) or separation_objective(p,prior,acts)
        strategies[name]={'pair':pair,'actions':[d['actions'][a] for a in acts],
                          'source_MI_nats':information(p,prior,acts),'joint_MI_nats':information(p,prior,acts,True),
                          'first_source_MI_nats':information(p,prior,acts[:1]),
                          'mean_worst_world_separation':sep[0],'global_min_separation':sep[1]}
    # Local nuisance/source diagnostics on the observed map support, not Fisher.
    support=[r['cell_index'] for r in d['confidence'] if r['confidence']>0]
    w=np.sqrt(np.array([conf[c] for c in support]));w/=max(np.linalg.norm(w),1e-15)
    f=np.asarray(full[:27,leaves,:][:,:,support],float)
    f=np.log(np.clip(f,1e-6,1-1e-6)/(1-np.clip(f,1e-6,1-1e-6)))
    # Axial +/- steps about central training world 13; standardized units.
    b=np.stack([(f[22]-f[4])/2,(f[16]-f[10])/2,(f[14]-f[12])/2],axis=-1)*w[None,:,None]
    nominal=f[13]*w[None,:]
    diagnostics=[]
    for i in range(len(leaves)):
        distances=np.sum((nominal-nominal[i])**2,axis=1);distances[i]=np.inf
        rival=int(np.argmin(distances));fraction,rank=projected_fraction(nominal[rival]-nominal[i],b[i])
        diagnostics.append({'source_id':d['sources'][int(leaves[i])]['id'],'rival_id':d['sources'][int(leaves[rival])]['id'],
                            'contrast_energy':float(distances[rival]),'residual_fraction':fraction,'confounding_fraction':None if fraction is None else 1-fraction,'nuisance_rank':rank})
    payload={'case':d['case'],'truth_read':False,'design_sha256':sha(design_path),'response_sha256':sha(bank/'responses.f32'),
             'strategies':strategies,'source_leaf_indices':leaves.tolist(),'prior':prior.tolist(),
             'diagnostics':diagnostics,'selection_seconds':time.perf_counter()-begin,
             'native_baseline_scope':'original variance-confidence-visibility heuristic on regenerated point responses; no exact navigation/RNG replay',
             'likelihood_scope':'conditional Bernoulli product with a shared nuisance; independence is an unvalidated surrogate assumption',
             'local_projection_scope':'confidence-weighted sensitivity, not calibrated Fisher information',
             'pair_objectives':[{'a':x['a'],'b':x['b'],'mean':v[0],'minimum':v[1]} for x,v in zip(pairs,objectives)]}
    dump(out,payload);print(d['case'],{k:(v['pair']['a'],v['pair']['b']) for k,v in strategies.items()},flush=True)

def heldout_metrics(train,held,true,acts):
    """One held world is shared by both observations, including alternative fit."""
    q=likelihood(train,acts);t=likelihood(held[true:true+1],acts)[0]
    bc=np.einsum('ho,sno->hsn',np.sqrt(t),np.sqrt(q))
    dist=np.clip(1-bc.max(axis=2),0,1);dist[:,true]=np.inf
    return dist.min(axis=1),dist.argmin(axis=1)

def evaluate(design,bank,selection,truth_path,out):
    d,full=load(design,bank);sel=json.loads(selection.read_text());truth=json.loads(truth_path.read_text())[d['house']]
    assert sel['truth_read'] is False and sel['design_sha256']==sha(design) and sel['response_sha256']==sha(bank/'responses.f32')
    geom=d['geometry'];gx=int(np.floor((truth[0]-geom['origin_x'])/geom['cell_size']));gy=int(np.floor((truth[1]-geom['origin_y'])/geom['cell_size']))
    # Do not assume storage order: source partition uses grid metadata index x+y*width.
    cell=gx+gy*geom['width'];owner=d['partition'].get(str(cell))
    ids=[d['sources'][i]['id'] for i in sel['source_leaf_indices']]
    if owner not in ids:dump(out,{'case':d['case'],'verdict':'SOURCE_TRUTH_OUTSIDE_PARTITION','promote':False});return
    true=ids.index(owner);leaf=sel['source_leaf_indices'];cells=[a['cell_index'] for a in d['actions']]
    p=np.asarray(full[:27,leaf,:][:,:,cells],float).transpose(1,0,2)
    h=np.asarray(full[27:,leaf,:][:,:,cells],float).transpose(1,0,2)
    results={}
    for name,s in sel['strategies'].items():
        acts=[s['pair']['a'],s['pair']['b']];sep,rival=heldout_metrics(p,h,true,acts)
        single,_=heldout_metrics(p,h,true,acts[:1])
        # Expected entropy/error under heldout truth, using training-world mixture.
        likelihood_train=likelihood(p,acts).mean(axis=1);joint=np.array(sel['prior'])[:,None]*likelihood_train
        pred=joint.sum(axis=0);post=joint/np.maximum(pred,1e-300)
        ent=entropy(post.T);qt=likelihood(h[true:true+1],acts)[0]
        xy=np.array([[d['sources'][i]['x'],d['sources'][i]['y']] for i in leaf])
        point_errors=np.linalg.norm((xy.T@post).T-np.array(truth),axis=1)
        unsupported=qt[:,pred<=0].sum(axis=1)
        # An impossible training outcome does not have a valid posterior.
        # Do not manufacture a zero-entropy posterior by epsilon division.
        expected_entropy=[float(x) if m==0 else None for x,m in zip(qt@ent,unsupported)]
        expected_error=[float(x) if m==0 else None for x,m in zip(qt@point_errors,unsupported)]
        rival_distances=[float(np.hypot(d['sources'][leaf[int(x)]]['x']-truth[0],d['sources'][leaf[int(x)]]['y']-truth[1])) for x in rival]
        results[name]={'heldout_min_separation':sep.tolist(),'fixed_rival_ids':[ids[int(x)] for x in rival],
                       'rival_distance_to_truth_m':rival_distances,
                       'true_representative_hit_probabilities':h[true,:,acts].T.tolist(),
                       'first_min_separation':single.tolist(),'pair_minus_single':(sep-single).tolist(),
                       'expected_source_entropy_nats':expected_entropy,
                       'expected_two_observation_posterior_mean_error_m':expected_error,
                       'unsupported_outcome_mass':unsupported.tolist(),
                       'mean_min_separation':float(sep.mean())}
    a=np.array(results['two_step_deconfounding']['heldout_min_separation']);b=np.array(results['one_step_source_MI']['heldout_min_separation'])
    pass_world=(a-b>=1e-4)&(a>=1.1*b)
    source=d['sources'][leaf[true]];distance=float(np.hypot(source['x']-truth[0],source['y']-truth[1]))
    reasons=[]
    if int(pass_world.sum())<6:reasons.append('FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI')
    if np.any(a<1e-12):reasons.append('TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE')
    chosen=sel['strategies']['two_step_deconfounding']['pair']
    if np.max(h[true,:,[chosen['a'],chosen['b']]])==0:reasons.append('SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS')
    if np.mean(a-b)<-max(.05*float(b.mean()),1e-4):reasons.append('CASE_MEAN_SEPARATION_DEGRADATION')
    if sel['strategies']['two_step_deconfounding']['pair']==sel['strategies']['one_step_source_MI']['pair']:reasons.append('SAME_ACTION_PAIR_AS_GREEDY_SOURCE_MI')
    # True representative against the fixed highest native-mass false source.
    false=max((i for i in range(len(leaf)) if i!=true),key=lambda i:d['sources'][leaf[i]]['native_score']*d['sources'][leaf[i]]['measure'])
    support=[r['cell_index'] for r in d['confidence'] if r['confidence']>0]
    weights=np.sqrt([r['confidence'] for r in d['confidence'] if r['confidence']>0]);weights/=np.linalg.norm(weights)
    z=np.clip(np.asarray(full[:27,leaf,:][:,:,support],float),1e-6,1-1e-6);z=np.log(z/(1-z))
    bmat=np.stack([(z[22,true]-z[4,true])/2,(z[16,true]-z[10,true])/2,(z[14,true]-z[12,true])/2],axis=-1)*weights[:,None]
    frac,rank=projected_fraction((z[13,false]-z[13,true])*weights,bmat)
    dump(out,{'case':d['case'],'house':d['house'],'true_owner':owner,'true_representative_distance_m':distance,
              'fixed_native_false_rival':ids[false],'true_vs_native_false_residual_fraction':frac,'true_nuisance_rank':rank,
              'true_response_at_all_action_worlds_zero_count':int(np.sum(h[true]==0)),
              'true_response_at_all_action_worlds_count':int(h[true].size),
              'selection_sha256_before_truth':sha(selection),'strategies':results,'passing_heldout_worlds':int(pass_world.sum()),
              'necessary_case_gate':int(pass_world.sum())>=6,'case_mean_degradation':bool(np.mean(a-b)<-max(.05*float(b.mean()),1e-4)),
              'two_step_minus_source_mi':(a-b).tolist(),'reasons':reasons,
              'scope':'true-leaf representative, not true continuous-source response; same native model, grid-off transport robustness only'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    for name in ['select','evaluate']:
        s=sub.add_parser(name);s.add_argument('--design',type=pathlib.Path,required=True);s.add_argument('--bank',type=pathlib.Path,required=True);s.add_argument('--out',type=pathlib.Path,required=True)
        if name=='evaluate':s.add_argument('--selection',type=pathlib.Path,required=True);s.add_argument('--truth',type=pathlib.Path,required=True)
    a=ap.parse_args()
    if a.cmd=='select':select(a.design,a.bank,a.out)
    else:evaluate(a.design,a.bank,a.selection,a.truth,a.out)
