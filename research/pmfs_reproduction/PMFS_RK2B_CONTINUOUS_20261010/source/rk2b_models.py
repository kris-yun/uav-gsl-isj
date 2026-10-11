"""Single deterministic response tree and common nonnegative query-ridge.
No generating-source or observed-test argument exists in this module.
"""
import sys
sys.dont_write_bytecode=True
from dataclasses import dataclass
import time, json, math
import numpy as np
from scipy.optimize import minimize

ORIGIN=np.array([-7.55,-7.88],dtype=np.float32)
CELL=np.float32(.25)

def physical_features(f):
    grid=(f[:,:2]-ORIGIN)/CELL
    cells=np.floor(grid).astype(np.int32)
    features=np.column_stack((grid-cells,f[:,2],f[:,3])).astype(np.float64)
    return cells,features

def weighted_quantile(x,w,q):
    order=np.argsort(x,kind='stable');xx=x[order];ww=w[order]
    assert len(xx)>0 and np.isfinite(xx).all() and (ww>0).all()
    i=int(np.searchsorted(np.cumsum(ww),q*math.fsum(map(float,ww)),side='left'))
    return float(xx[min(i,len(xx)-1)])

def route(features,spec):
    if spec['kind']=='U':return np.zeros(len(features),dtype=np.int32)
    if spec['kind']=='S':
        return ((features[:,2]>=spec['z_cut']).astype(np.int32)*2+(features[:,3]>=spec['sigma_cut']).astype(np.int32))
    assert spec['kind']=='L'
    out=np.zeros(len(features),dtype=np.int32)
    def descend(node,index):
        if isinstance(node,int):out[index]=node;return
        values=features[index,node['feature']]
        keep=values<float(node['cut'])
        descend(node['left'],index[keep]);descend(node['right'],index[~keep])
    descend(spec['tree'],np.arange(len(features)))
    return out

def state_keys(cells,classes):return np.column_stack((cells,classes)).astype(np.int32)

def partition_arrays(data,spec):
    cl=route(data['features'],spec)
    keys,index=np.unique(state_keys(data['cells'],cl),axis=0,return_inverse=True)
    count=np.bincount(index,weights=data['weights'],minlength=len(keys))
    assert (count>0).all()
    prior=np.column_stack([np.bincount(index,weights=data['weights']*data['phi'][:,p].astype(float),minlength=len(keys))/count for p in range(10)])
    X=np.zeros((len(data['queries']),len(keys)),dtype=np.float64)
    for row,q in enumerate(data['queries']):
        lo,hi=data['slices'][q['reference_id'],q['frame']]
        X[row]=np.bincount(index[lo:hi],minlength=len(keys))
    assert np.isfinite(X).all() and np.isfinite(prior).all() and (prior>=0).all()
    return keys,X,prior

def common_fit(X,prior,y,poses,contract):
    h=np.zeros_like(prior);logs=[];total_mse=0.
    for pose in range(10):
        mask=poses==pose;A=X[mask];b=y[mask];n=len(b);assert n==contract['training_rows_per_pose']
        scale=np.sqrt(np.mean(A*A,axis=0));scale=np.where(scale>0,scale,1.)
        Z=A/scale;beta0=prior[:,pose]*scale;lam=contract['ridge_lambda']
        def f(beta):
            residual=Z@beta-b;delta=beta-beta0
            value=float(residual@residual/n+lam*(delta@delta))
            gradient=2*(Z.T@residual/n+lam*delta)
            return value,gradient
        started=time.perf_counter()
        fit=minimize(f,beta0,method='L-BFGS-B',jac=True,bounds=[(0.,None)]*len(beta0),
            options=dict(maxiter=contract['solver_maxiter'],gtol=contract['solver_gtol'],ftol=contract['solver_ftol'],maxls=40))
        beta=np.asarray(fit.x,dtype=float);objective,grad=f(beta)
        # SciPy's relative-objective termination need not satisfy the frozen
        # KKT check. Polish the identical convex problem in its n-row dual;
        # no loss, lambda, routing, capacity, training or task rule is changed.
        dual=Z@beta-b;polish_steps=0
        def primal_from_dual(v):return np.maximum(0.,beta0-Z.T@v/(n*lam))
        def dual_value(v):
            x=primal_from_dual(v)
            return float(.5*(v@v)+b@v+(n*lam/2)*(x@x))
        for polish_steps in range(33):
            candidate=primal_from_dual(dual);_,candidate_gradient=f(candidate)
            check=np.where(candidate>1e-10,np.abs(candidate_gradient),np.maximum(0.,-candidate_gradient))
            bound=contract['KKT_relative_tolerance']*(1+float(np.max(np.abs(Z.T@b/n),initial=0.))+lam*float(np.max(np.abs(beta0),initial=0.)))
            if np.max(check,initial=0.)<=bound:
                beta=candidate;break
            if polish_steps==32:
                beta=candidate;break
            dg=dual+b-Z@candidate
            active=candidate>0
            H=np.eye(n)+(Z[:,active]@Z[:,active].T)/(n*lam)
            direction=-np.linalg.solve(H,dg)
            old_value=dual_value(dual);descent=float(dg@direction);step=1.
            for backtrack in range(64):
                trial=dual+step*direction
                if dual_value(trial)<=old_value+1e-4*step*descent+1e-14*max(1.,abs(old_value)):
                    dual=trial;break
                step*=.5
            else:raise RuntimeError('Convex dual numerical line search failed')
        objective,grad=f(beta)
        projected=np.where(beta>1e-10,np.abs(grad),np.maximum(0.,-grad))
        absolute=float(np.max(projected,initial=0.))
        threshold=contract['KKT_relative_tolerance']*(1+float(np.max(np.abs(Z.T@b/n),initial=0.))+lam*float(np.max(np.abs(beta0),initial=0.)))
        assert np.isfinite(beta).all() and (beta>=0).all()
        mse=float(np.mean((Z@beta-b)**2));total_mse+=mse/10
        logs.append(dict(pose_id=pose,query_rows=n,coefficients=len(beta),objective=objective,train_MSE=mse,
            KKT_projected_gradient_max=absolute,KKT_threshold=threshold,KKT_pass=absolute<=threshold,
            scipy_success=bool(fit.success),scipy_message=str(fit.message),iterations=int(fit.nit),evaluations=int(fit.nfev),wall_s=time.perf_counter()-started))
        logs[-1].update(identical_objective_dual_polish_steps=polish_steps,dual_polish_cap=32)
        if absolute>threshold:
            raise RuntimeError('Query-fit KKT failed: '+json.dumps(logs[-1]))
        h[:,pose]=beta/scale
    return h,total_mse,logs

def route_nodes(tree):
    if isinstance(tree,int):return 0
    return 1+route_nodes(tree['left'])+route_nodes(tree['right'])

def capacity(keys,spec):
    nodes=route_nodes(spec['tree']) if spec['kind']=='L' else (2 if spec['kind']=='S' else 0)
    # Canonical arrays: int32 key triple + float64 ten-receptor decoder;
    # 32 bytes per tree node, S two doubles plus implementation marker=32 bytes.
    route_bytes=nodes*32 if spec['kind']=='L' else (32 if spec['kind']=='S' else 0)
    def deep_size(x,seen):
        if id(x) in seen:return 0
        seen.add(id(x));size=sys.getsizeof(x)
        if isinstance(x,dict):size+=sum(deep_size(k,seen)+deep_size(v,seen) for k,v in x.items())
        elif isinstance(x,(list,tuple)):size+=sum(deep_size(v,seen) for v in x)
        return size
    # Count the actual minimal Python runtime object, with two owning arrays.
    runtime=dict(spec=json.loads(json.dumps(spec)),keys=np.array(keys,dtype=np.int32,copy=True),h=np.zeros((len(keys),10),dtype=np.float64))
    return dict(active_states=len(keys),decoder_coefficients=len(keys)*10,
        routing_nodes=nodes,routing_bytes=route_bytes,canonical_key_bytes=len(keys)*12,
        canonical_decoder_bytes=len(keys)*80,canonical_total_bytes=len(keys)*92+route_bytes,
        routing_spec_UTF8_bytes=len(json.dumps(spec,sort_keys=True).encode('utf-8')),
        actual_minimal_runtime_object_bytes=deep_size(runtime,set()),allocator_and_library_overheads_excluded=True)

def build_model(data,spec,contract):
    keys,X,prior=partition_arrays(data,spec)
    h,mse,logs=common_fit(X,prior,data['targets'],data['poses'],contract)
    return dict(spec=spec,keys=keys,X=X,prior=prior,h=h,train_MSE=mse,fit_logs=logs,capacity=capacity(keys,spec))

def leaves(tree):
    if isinstance(tree,int):return [tree]
    return leaves(tree['left'])+leaves(tree['right'])

def replace_leaf(tree,target,feature,cut,newleaf):
    if isinstance(tree,int):
        return dict(feature=int(feature),cut=float(cut),left=target,right=newleaf) if tree==target else tree
    return dict(feature=tree['feature'],cut=tree['cut'],
        left=replace_leaf(tree['left'],target,feature,cut,newleaf),
        right=replace_leaf(tree['right'],target,feature,cut,newleaf))

def learn_one_tree(data,common,S_model,U_model,progress):
    current=dict(U_model);current['spec']=dict(kind='L',tree=0)
    current['capacity']=capacity(current['keys'],current['spec'])
    proposals=[];proposal_id=0
    for stage in range(1,4):
        assignment=route(data['features'],current['spec']);best=None;nextleaf=max(leaves(current['spec']['tree']))+1
        for leaf in sorted(leaves(current['spec']['tree'])):
            idx=assignment==leaf
            if not idx.any():continue
            for feature in range(4):
                cutpoints=sorted({weighted_quantile(data['features'][idx,feature],data['weights'][idx],q) for q in common['split_quantiles']})
                for cut in cutpoints:
                    proposal_id+=1
                    spec=dict(kind='L',tree=replace_leaf(current['spec']['tree'],leaf,feature,cut,nextleaf))
                    left=int(np.sum(idx & (data['features'][:,feature]<cut)))
                    right=int(np.sum(idx & (data['features'][:,feature]>=cut)))
                    if not left or not right:
                        rec=dict(proposal_id=proposal_id,stage=stage,leaf=leaf,feature=feature,cut=cut,status='EXCLUDED_EMPTY_TRAIN_CHILD',train_MSE=None,left_records=left,right_records=right)
                        proposals.append(rec);progress('TREE_EMPTY_CHILD_EXCLUSION',proposal=rec);continue
                    key,X,prior=partition_arrays(data,spec);cap=capacity(key,spec)
                    rec=dict(proposal_id=proposal_id,stage=stage,leaf=leaf,feature=feature,cut=cut,left_records=left,right_records=right,**cap)
                    if cap['active_states']>S_model['capacity']['active_states'] or cap['canonical_total_bytes']>S_model['capacity']['canonical_total_bytes'] or cap['actual_minimal_runtime_object_bytes']>S_model['capacity']['actual_minimal_runtime_object_bytes']:
                        rec.update(status='EXCLUDED_PRE_FIT_CAPACITY',train_MSE=None);proposals.append(rec);progress('TREE_CAPACITY_EXCLUSION',proposal=rec);continue
                    h,mse,fitlog=common_fit(X,prior,data['targets'],data['poses'],common)
                    rec.update(status='FITTED_TRAIN_ONLY',train_MSE=mse,fit_KKT_all_pass=True,fit_logs=fitlog)
                    proposals.append(rec);progress('TREE_PROPOSAL_FITTED',proposal=rec)
                    ordering=(mse,leaf,feature,cut)
                    if best is None or ordering<best[0]:
                        best=(ordering,dict(spec=spec,keys=key,X=X,prior=prior,h=h,train_MSE=mse,fit_logs=fitlog,capacity=cap),proposal_id)
        if best is None or current['train_MSE']-best[1]['train_MSE']<=common['split_loss_tolerance']:
            progress('TREE_STOP_NO_QUALIFIED_TRAIN_LOSS_GAIN',stage=stage);break
        current=best[1];progress('TREE_SPLIT_ACCEPTED',stage=stage,proposal_id=best[2],train_MSE=current['train_MSE'])
    assert proposal_id<=72 and len(leaves(current['spec']['tree']))<=4
    return current,proposals

@dataclass(frozen=True)
class CompressionSnapshot:
    """Allowed only in the compression interface or a candidate forecast builder."""
    physical_description: dict
    receiver_xyz: np.ndarray
    pose_id: int

def compress(snapshot,model,raw_math,native_primitive,occupancy):
    started=time.perf_counter();desc=snapshot.physical_description;f=desc['filaments']
    route_start=time.perf_counter();cells,features=physical_features(f);cl=route(features,model['spec'])
    keys=state_keys(cells,cl);lookup={tuple(map(int,k)):i for i,k in enumerate(model['keys'])}
    indexes=np.array([lookup.get(tuple(map(int,k)),-1) for k in keys],dtype=np.int32)
    known=indexes>=0;counts=np.bincount(indexes[known],minlength=len(model['keys']))
    route_wall=time.perf_counter()-route_start
    fallback_n=int((~known).sum());fallback_ppm=0.;eligible=blocked=positive=0;fallback_wall=0.
    if fallback_n:
        t=time.perf_counter()
        _,total,e,b,p=native_primitive(f[~known],np.array([snapshot.receiver_xyz],dtype=np.float32),desc,occupancy,raw_math)
        fallback_ppm=float(total[0]);eligible=int(e[0]);blocked=int(b[0]);positive=int(p[0]);fallback_wall=time.perf_counter()-t
    decode_start=time.perf_counter();value=float(counts@model['h'][:,snapshot.pose_id])+fallback_ppm;decode_wall=time.perf_counter()-decode_start
    assert math.isfinite(value) and value>=0
    return value,dict(particles=len(f),fallback_particles=fallback_n,fallback_ppm=fallback_ppm,
        phi_particle_tests=fallback_n,LOS_calls=eligible,LOS_blocked=blocked,positive_contributors=positive,
        state_assignment_wall_s=route_wall,decode_wall_s=decode_wall,fallback_wall_s=fallback_wall,
        total_compression_wall_s=time.perf_counter()-started)
