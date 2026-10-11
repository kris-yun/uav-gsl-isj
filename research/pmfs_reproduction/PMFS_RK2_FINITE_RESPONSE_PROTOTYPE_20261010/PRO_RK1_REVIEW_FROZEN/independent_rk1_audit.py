#!/usr/bin/env python3
"""Read-only numerical RK1 review; no producer, fitting search or physics calls.
Reconstructs the EIGHT FROZEN kernels and 1,632 frozen predictions from caches,
then computes descriptive error identities. No new method is trained.
Usage: python -B independent_rk1_audit.py --root <extracted_RK1> --out <new_dir>
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, time
from collections import defaultdict
from pathlib import Path
import numpy as np

ARMS = ('U', 'S', 'C_C7', 'C_K2')
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def read_csv(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def write_csv(p, rows):
    if not rows: raise ValueError('Empty output table')
    with p.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b):
    if not math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=3e-13):
        raise AssertionError((a,b))
def key_array(f,cuts):
    ij=np.floor((f[:,:2]-np.asarray([-7.55,-7.88],np.float32))/np.float32(.25)).astype(np.int64)
    k=2*(f[:,2].astype(np.float64)>=cuts[0]).astype(np.int64)+(f[:,3].astype(np.float64)>=cuts[1]).astype(np.int64)
    return np.column_stack((ij,k))
def metric(e):
    n=len(e); b=math.fsum(e)/n
    return dict(MSE_ppm2=math.fsum(v*v for v in e)/n, bias_ppm=b,
                MAE_ppm=math.fsum(abs(v) for v in e)/n, squared_bias_ppm2=b*b,
                centered_error_ppm2=math.fsum((v-b)**2 for v in e)/n)

def run(root,out):
    start=time.perf_counter(); rk=root/'RK1_NEW'; cache=root/'RK0_NEW/reference_contribution_cache'
    files_before={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
    idx=read_json(cache/'CONTRIBUTION_CACHE_RESULT.json'); frames={}; anchors=0
    for rec in idx['frames']:
        path=cache/rec['cache_relative_path']
        assert digest(path)==rec['cache_SHA256']
        with np.load(path,allow_pickle=False) as z:
            f=z['filaments'].copy(); phi=z['contributions'].copy(); total=z['native_totals'].copy()
        assert np.isfinite(phi).all() and (phi>=0).all()
        np.testing.assert_array_equal(np.cumsum(phi,axis=0,dtype=np.float32)[-1].view(np.uint32),total.view(np.uint32))
        for a in rec['native_query_checks']:
            assert float(total[a['pose_index']])==a['native_cpp_ppm']; anchors+=1
        frames[(rec['bank'],int(rec['frame']))]=(f,phi,int(rec['exposure_weight']))
    assert len(frames)==196 and anchors==204
    pred=read_csv(rk/'PREDICTIONS_BLIND.csv'); mapping=read_json(rk/'POST_FREEZE_GENERATOR_MAPPING.json')
    maxh=0.; maxp=0.; nvalues=0; fitstats=[]
    for side in (0,1):
        fold=f'T{side}_E{1-side}'; train=[f'C7_{side}',f'K2_{side}']
        population=np.concatenate([np.repeat(f[:,[2,3]].astype(np.float64),w,axis=0)
            for (b,_),(f,phi,w) in frames.items() if b in train])
        cuts=np.median(population,axis=0)
        sets=[]
        for b in train:
            sets.append({tuple(k) for (bb,_),(f,phi,w) in frames.items() if bb==b for k in key_array(f,cuts)})
        Q=sets[0]&sets[1]
        savedQ={(int(r['cell_i']),int(r['cell_j']),int(r['class_id']))
                for r in read_csv(rk/'COMMON_SUPPORT_FINE_KEYS.csv') if r['fold']==fold}
        assert Q==savedQ
        accum={a:defaultdict(lambda:[0,np.zeros(10,np.float64)]) for a in ARMS}
        for b in train:
            for (bb,frame),(f,phi,w) in sorted(frames.items()):
                if bb!=b: continue
                kk=key_array(f,cuts)
                # Zero phi values still contribute particle exposure counts.
                for k,p in zip(kk,phi):
                    k=tuple(map(int,k))
                    if k not in Q: continue
                    xy=(k[0],k[1],-1)
                    for arm,key in [('U',xy),('S',k),('C_'+b.split('_')[0],xy)]:
                        accum[arm][key][0]+=w;accum[arm][key][1]+=p.astype(np.float64)*w
        h={a:{k:v[1]/v[0] for k,v in accum[a].items()} for a in ARMS}
        for a in ARMS:
            for row in read_csv(rk/f'{fold}_KERNEL_{a}.csv'):
                k=(int(row['cell_i']),int(row['cell_j']),int(row['class_id']));j=int(row['pose_id'])
                assert accum[a][k][0]==int(row['particle_exposure_denominator'])
                val=float(h[a][k][j]);saved=float(row['h_ppm_per_particle']);close(val,saved)
                maxh=max(maxh,abs(val-saved))
        for row in [r for r in pred if r['fold']==fold]:
            f,phi,w=frames[(row['bank'],int(row['frame']))];j=int(row['pose_id']);kk=key_array(f,cuts)
            mask=np.asarray([tuple(k) in Q for k in kk]); nxy=defaultdict(int); ncl=defaultdict(int)
            for k in kk[mask]:
                k=tuple(map(int,k));ncl[k]+=1;nxy[(k[0],k[1],-1)]+=1
            tail=math.fsum(map(float,phi[~mask,j])); target=math.fsum(map(float,phi[:,j]))
            close(tail,row['tail_Qoutside64_ppm']);close(target,row['target_phi64_ppm'])
            for a in ARMS:
                ns=ncl if a=='S' else nxy
                val=tail+math.fsum(n*float(h[a][k][j]) for k,n in ns.items())
                saved=float(row[a+'_prediction_ppm']);close(val,saved);maxp=max(maxp,abs(val-saved));nvalues+=1
        fitstats.append(dict(fold=fold,Q_fine_keys=len(Q),shared_XY_keys=len(h['U']),
                U_coefficients=10*len(h['U']),S_coefficients=10*len(h['S']),
                C_two_kernel_coefficients=10*(len(h['C_C7'])+len(h['C_K2']))))
    # New descriptive algebra, computed from the frozen test predictions only.
    groups=defaultdict(list)
    for r in pred:
        if r['role']=='test' and int(r['membership_branch'])==0: groups[(r['fold'],r['bank'])].append(r)
    metrics=[];direction=[]; tailmax=0.
    for (fold,bank),rr in sorted(groups.items()):
        assert len(rr)==50
        errors={}
        for arm in ARMS+('C_ORACLE',):
            col='C_'+mapping[bank] if arm=='C_ORACLE' else arm
            ee=[float(r[col+'_prediction_ppm'])-float(r['target_phi64_ppm']) for r in rr];errors[arm]=ee
            met=metric(ee);close(met['MSE_ppm2'],met['squared_bias_ppm2']+met['centered_error_ppm2'])
            disagreements=sum(int(r[col+'_event'])!=int(r['native_F32_event']) for r in rr)
            for r,e in zip(rr,ee):
                tailmax=max(tailmax,abs(e-(float(r[col+'_Q_prediction_ppm'])-float(r['target_Q64_ppm']))))
            metrics.append(dict(fold=fold,bank=bank,arm=arm,**met,event_disagreements=disagreements))
        gains=np.square(errors['S'])-np.square(errors['C_ORACLE'])
        direction.append(dict(fold=fold,bank=bank,exposures=50,
                C_lower_squared_error_blocks=int((gains>1e-12).sum()),
                C_higher_squared_error_blocks=int((gains< -1e-12).sum()),
                median_S_minus_C_squared_error=float(np.median(gains)),
                tail_alone_positive_blocks=sum(int(r['tail_alone_event']) for r in rr),
                not_independent_trials=True))
    sums=[]
    for arm in ('U','S','C_ORACLE'):
        rr=[r for r in metrics if r['arm']==arm]
        sums.append(dict(arm=arm,**{k:math.fsum(r[k] for r in rr)/4 for k in ['MSE_ppm2','squared_bias_ppm2','centered_error_ppm2']}))
    ss={r['arm']:r for r in sums};gain=ss['S']['MSE_ppm2']-ss['C_ORACLE']['MSE_ppm2']
    condition=[]
    for fold in ('T0_E1','T1_E0'):
        rr=[r for r in read_csv(rk/'CLASS_CONDITIONAL_RESPONSE_DIFFERENCES.csv') if r['fold']==fold and int(r['test_C7_count'])>0 and int(r['test_K2_count'])>0]
        x=np.asarray([float(r['train_C7_minus_K2_h']) for r in rr]);y=np.asarray([float(r['test_C7_minus_K2_h']) for r in rr]);w=np.asarray([min(int(r['test_C7_count']),int(r['test_K2_count'])) for r in rr],float)
        condition.append(dict(fold=fold,supported_rows=len(rr),weighted_cosine=float((w*x*y).sum()/np.sqrt((w*x*x).sum()*(w*y*y).sum())),
                difference_MSE_to_zero_difference_MSE=float((w*(x-y)**2).sum()/(w*y*y).sum()),exploratory_not_independent=True))
    files_after={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
    assert files_before==files_after
    for name,rows in [('independent_test_metrics.csv',metrics),('error_identity_equal_bank.csv',sums),('block_direction_descriptive.csv',direction),('actual_kernel_capacity.csv',fitstats),('conditional_difference_check.csv',condition)]:write_csv(out/name,rows)
    result=dict(status='PASS_SECOND_IMPLEMENTATION_CACHE_AND_METRIC_RECOMPUTATION',
            input_files_unchanged=len(files_before),cache_files=196,native_anchors=anchors,
            frozen_kernels_reconstructed=8,all_arm_values_recomputed=nvalues,max_h_abs_difference=maxh,
            max_prediction_abs_difference=maxp,tail_error_identity_max_abs=tailmax,
            equal_bank_MSE={r['arm']:r['MSE_ppm2'] for r in sums},
            S_to_C_MSE_reduction=gain,
            S_to_C_squared_bias_reduction=ss['S']['squared_bias_ppm2']-ss['C_ORACLE']['squared_bias_ppm2'],
            S_to_C_centered_error_reduction=ss['S']['centered_error_ppm2']-ss['C_ORACLE']['centered_error_ppm2'],
            new_models=0,new_physics=0,new_phi_queries=0,new_localization=0,
            python=platform.python_version(),numpy=np.__version__,wall_seconds=time.perf_counter()-start,
            scope='Independent reconstruction of frozen RK1, plus descriptive algebra on old data; no source localization or prototype validation.')
    (out/'INDEPENDENT_REVIEW_RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=args.root.resolve(strict=True);out=args.out.resolve()
    if out==root or root in out.parents:raise ValueError('Output must be outside immutable input root')
    out.mkdir(parents=True,exist_ok=False);run(root,out)
