"""Independent scalar verifier. No producer import, fit, ROS or simulation."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,numpy as np

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def table(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b):assert np.allclose(a,b,rtol=1e-10,atol=2e-12),(np.asarray(a),np.asarray(b))
def calculate(x,y,head,scale,ix=None):
    x=np.asarray(x,np.float32);y=np.asarray(y,np.float32);M=x.shape[1]
    p=(np.count_nonzero(x>np.float32(.1),axis=1)+.5)/(M+1.)
    z=np.log1p(x.astype(np.float64));o=np.log1p(y.astype(np.float64));c=np.zeros((len(x),50))
    for k in range(len(x)):
        for b in range(50):
            c[k,b]=sum(abs(t-o[b]) for t in z[k,:,b])/M-sum(abs(a-d) for a in z[k,:,b] for d in z[k,:,b])/(2*M*M)
    terms=np.where(y[None,:]>np.float32(.1),np.log(p),np.log(1-p)) if head=='H0' else -c/scale
    ix=range(50) if ix is None else ix;s=np.array([sum(t[b] for b in ix)/len(ix) for t in terms]);exp=np.exp(s-s.max());lp=s-s.max()-np.log(exp.sum())
    return s,lp,np.exp(lp),terms,p,c

def main(root):
    root=Path(root);reg=load(root/'experiment_registry.json');blind=load(root/'BLIND_PREDICTIONS.json');truth=load(root/'evaluation_only/TRUTH_MAPPING.json');ids=[s['future_candidate_id'] for s in reg['sources']]
    assert sh(root/'BLIND_PREDICTIONS.json')==load(root/'BLIND_PREDICTION_FREEZE.json')['SHA256']
    assert load(root/'ALL_MODELS_FROZEN_BEFORE_OBSERVATIONS.json')['time_ns']<load(root/'OBSERVABLE_OPEN_LEDGER.json')['time_ns']<load(root/'BLIND_PREDICTION_FREEZE.json')['time_ns']
    metrics={(int(r['M']),r['head'],r['oid'],r['method']):r for r in table(root/'per_realization_metrics.csv')};count=0;kkt=[];future_checks=0
    for M in [2,4] if reg['mode']==24 else [2]:
        d=root/f'M{M}';metadata=load(d/'MODEL_METADATA.json');status=load(d/'MODEL_STATUS.json');scale=load(d/'HEAD_SCALE_FROZEN.json')['H1_scale']
        freeze=load(d/'PRE_TEST_PREDICTION_FREEZE.json');assert all(sh(d/n)==h for n,h in freeze.items())
        with np.load(d/'forecasts/F.npz',allow_pickle=False) as zz:f=zz['reference_response_ppm'][:,:M]
        z=np.log1p(f.astype(np.float32).astype(float));a=float(np.quantile(z,.75)-np.quantile(z,.25));close(scale,a if a>1e-12 else 1.)
        for method in status['methods']:
            with np.load(d/'forecasts'/f'{method}.npz',allow_pickle=False) as z:x=z['reference_response_ppm'][:,:M]
            for oid in truth:
                with np.load(root/'scalar_observations'/f'{oid}.npz',allow_pickle=False) as z:y=z['observed_ppm']
                tc=ids.index(truth[oid]['candidate_id'])
                for head in ['H0','H1']:
                    key=f'{M}|{head}|{oid}|{method}';r=blind[key];s,lp,p,terms,event,c=calculate(x,y,head,scale)
                    for k,v in [('scores',s),('log_prob',lp),('prob',p),('block_terms',terms),('event_probability',event),('CRPS',c)]:close(r[k],v)
                    close(float(metrics[M,head,oid,method]['NLL']),-lp[tc]);count+=1
                    assert int(metrics[M,head,oid,method]['top1_error'])==int(len(r['top1'])!=1 or r['top1'][0]!=tc)
                    for n in [10,20,30,40,50]:
                        ps,pl,pp,*_=calculate(x,y,head,scale,range(n));pr=blind[key+f'|prefix{n}'];close(pr['prob'],pp);close(pr['log_prob'],pl)
                    _,_,w,*_=calculate(x,y,head,scale,range(25));fp=blind[key+'|future25'];close(fp['prefix25']['prob'],w)
                    zz=np.log1p(x.astype(np.float32).astype(float)).reshape(3*M,50)[:,25:];weights=np.repeat(w/M,M);oo=np.log1p(y[25:].astype(float))
                    cp=[]
                    for b in range(25):cp.append(sum(weights[i]*abs(zz[i,b]-oo[b]) for i in range(3*M))-.5*sum(weights[i]*weights[j]*abs(zz[i,b]-zz[j,b]) for i in range(3*M) for j in range(3*M)))
                    ep=w@event[:,25:];close(fp['future']['CRPS_per_block'],cp);close(fp['future']['predicted_hit_probability'],ep);close(fp['future']['mean_Brier'],np.mean((ep-(y[25:]>np.float32(.1)))**2));future_checks+=1
            if method=='F':continue
            with np.load(d/'models'/f'{method}.npz',allow_pickle=False) as z:X=z['train_counts'];prior=z['prior'];h=z['decoder'];y=z['train_native_ppm'];poses=z['train_pose_ids']
            assert np.isfinite(h).all() and (h>=0).all()
            for pose in range(10):
                A=X[poses==pose];b=y[poses==pose];n=len(b);assert n==15*M
                col=np.sqrt(np.mean(A*A,axis=0));col[col==0]=1;Z=A/col;beta=h[:,pose]*col;beta0=prior[:,pose]*col;lam=.01
                grad=2*(Z.T@(Z@beta-b)/n+lam*(beta-beta0));project=np.where(beta>1e-10,np.abs(grad),np.maximum(0,-grad));threshold=1e-6*(1+np.max(np.abs(Z.T@b/n),initial=0)+lam*np.max(np.abs(beta0),initial=0))
                assert np.max(project,initial=0)<=threshold*1.00001,(M,method,pose)
                kkt.append(dict(M=M,method=method,pose=pose,rows=n,max_projected_gradient=float(np.max(project,initial=0)),threshold=float(threshold)))
            if method=='L':
                c=metadata[method]['capacity'];b=metadata['S_query']['capacity'];assert c['routing_nodes']<=3
                assert all(c[k]<=b[k] for k in ['active_states','canonical_total_bytes','actual_minimal_runtime_object_bytes'])
    for row in table(root/'candidate_pairwise_margins.csv'):assert float(row['KL_F_to_method'])<=float(row['KL_bound_R2_over8'])+2e-12
    # Every primary endpoint is reconstructed independently; no diagnostic can replace it.
    gate=load(root/'ORIGINAL_B_GATE.json')
    if gate['arms_present']:
        vals={n:[metrics[2,'H0',o,n] for o,t in truth.items() if t['role']=='heldout'] for n in ['U_query','S_query','L']}
        for n in ['U_query','S_query']:
            b=np.mean([float(a['NLL']) for a in vals[n]]);l=np.mean([float(a['NLL']) for a in vals['L']]);close(gate['gain_each_baseline'][n],(b-l)/b)
            close(gate['maximum_individual_harm_nat'][n],max(float(a['NLL'])-float(d['NLL']) for a,d in zip(vals['L'],vals[n])))
    if (root/'MANIFEST_SHA256.json').exists():
        manifest=load(root/'MANIFEST_SHA256.json');assert all(sh(root/n)==h for n,h in manifest.items())
    result=dict(status='PASS_INDEPENDENT_SCALAR_PREFIX_FUTURE_AND_KKT',scalar_results=count,future_results=future_checks,KKT_systems=len(kkt),fitting_or_generation_calls=0,producer_modules_imported=False,CSV_comparison='tolerance-based numeric, not byte equality',maximum_relative_tolerance=1e-10,absolute_tolerance=2e-12)
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':main(sys.argv[1])
