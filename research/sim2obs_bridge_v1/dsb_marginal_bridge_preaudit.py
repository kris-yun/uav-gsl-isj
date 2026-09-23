import os, glob, json
import numpy as np, pandas as pd

BASE=os.environ.get('R2_NATIVE_BASE','/mnt/data/r2_partial_id/extracted/tnqc_r2_six_offline_20260921_authoritative/native')
RUNS=sorted(glob.glob(BASE+'/House*_seed*_off_off'))

def load_run(d):
    ev=json.load(open(d+'/tnqc_fixed_trajectory_evaluation.json'))
    truth=np.array(ev['truth'],float)
    u=int(ev['selected_source_update_id'])
    b=f'{d}/context_bank/source_update_{u:04d}'
    a=pd.read_csv(b+'/candidate_support_alignment.csv')
    m=pd.read_csv(b+'/candidate_manifest.csv')
    m['truth_dist']=np.hypot(m.native_source_x-truth[0],m.native_source_y-truth[1])
    tid=m.loc[m.truth_dist.idxmin(),'candidate_id']
    return dict(name=os.path.basename(d),house=os.path.basename(d).split('_')[0],truth=truth,a=a,m=m,tid=tid)

def pava(x,y,w):
    o=np.argsort(x,kind='mergesort'); x=x[o]; y=y[o]; w=w[o]
    ux, inv=np.unique(x,return_inverse=True)
    sw=np.bincount(inv,weights=w); sy=np.bincount(inv,weights=w*y)
    yy=sy/np.maximum(sw,1e-300)
    blocks=[]
    for i,(v,wt) in enumerate(zip(yy,sw)):
        blocks.append([i,i,wt,v])
        while len(blocks)>=2 and blocks[-2][3] > blocks[-1][3]:
            b2=blocks.pop(); b1=blocks.pop()
            wt=b1[2]+b2[2]
            v=(b1[2]*b1[3]+b2[2]*b2[3])/wt
            blocks.append([b1[0],b2[1],wt,v])
    fit=np.empty(len(ux))
    for s,e,wt,v in blocks:
        fit[s:e+1]=v
    return ux, np.clip(fit,0,1)

def apply_iso(q,ux,fit):
    return np.interp(q,ux,fit,left=fit[0],right=fit[-1])

def native_logscore(a,qcol):
    f=1-a.measured_confidence.to_numpy(float)*np.abs(
        a.measured_probability.to_numpy(float)-a[qcol].to_numpy(float)
    )
    return np.log(np.clip(f,1e-300,None)).sum()

data=[load_run(d) for d in RUNS]
rows=[]
for test in data:
    train=[r for r in data if r['house']!=test['house']]
    xs=[]; ys=[]; ws=[]
    for r in train:
        t=r['a'][r['a'].candidate_id.astype(str)==str(r['tid'])]
        xs.append(t.simulated_hit_probability.to_numpy(float))
        ys.append(t.measured_probability.to_numpy(float))
        ws.append(t.measured_confidence.to_numpy(float))
    x=np.concatenate(xs); y=np.concatenate(ys); w=np.concatenate(ws)
    ux,fit=pava(x,y,np.maximum(w,1e-12))

    a=test['a'].copy()
    a['bridge_probability']=apply_iso(a.simulated_hit_probability.to_numpy(float),ux,fit)
    scores=[]
    for cid,g in a.groupby('candidate_id',sort=False):
        scores.append((str(cid),native_logscore(g,'bridge_probability')))
    sm=pd.DataFrame(scores,columns=['candidate_id','bridge_logscore'])

    mm=test['m'].copy()
    mm['candidate_id']=mm.candidate_id.astype(str)
    mm=mm.merge(sm,on='candidate_id',how='left')
    mm['native_rank']=pd.Series(-mm.native_score.to_numpy(float)).rank(method='average').to_numpy(float)
    mm['bridge_rank']=pd.Series(-mm.bridge_logscore.to_numpy(float)).rank(method='average').to_numpy(float)
    tr=mm[mm.candidate_id.astype(str)==str(test['tid'])].iloc[0]

    rho_native=pd.Series(mm.native_score).rank().corr(pd.Series(-mm.truth_dist).rank())
    rho_bridge=pd.Series(mm.bridge_logscore).rank().corr(pd.Series(-mm.truth_dist).rank())
    rows.append(dict(
        run=test['name'],house=test['house'],n=len(mm),truth_candidate=test['tid'],
        truth_dist=float(tr.truth_dist),native_truth_rank=float(tr.native_rank),
        bridge_truth_rank=float(tr.bridge_rank),
        rank_delta_native_minus_bridge=float(tr.native_rank-tr.bridge_rank),
        native_spearman_vs_negdist=float(rho_native),
        bridge_spearman_vs_negdist=float(rho_bridge),
        train_houses='|'.join(sorted(set(r['house'] for r in train))),
        iso_knots=len(ux),iso_output_min=float(fit.min()),iso_output_max=float(fit.max())
    ))

out=pd.DataFrame(rows)
print(out.to_string(index=False))
print('improved',int((out.bridge_truth_rank<out.native_truth_rank).sum()),'/6')
out.to_csv('DSB_MARGINAL_BRIDGE_PREAUDIT_R2.csv',index=False)
