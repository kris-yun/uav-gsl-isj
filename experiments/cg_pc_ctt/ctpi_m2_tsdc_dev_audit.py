#!/usr/bin/env python3
"""Reproduce the spent-data DEV audit for CTPI M2 TSDC V0.

The old 30 CAL + 30 CONFIRM worlds are permanently DEV_SPENT.  This script is
for reproducibility/falsification only; it does not authorize reusing them as a
fresh confirmation set.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import binomtest

MEMBER_COUNT=8
THRESHOLD=0.1
EPS=1e-15
FROZEN_BETA=np.asarray([-1.1915279295661385,1.0423583775118566,2.9896670550884170],dtype=np.float64)


def rk(k):
    p=(np.asarray(k,dtype=np.float64)+0.5)/(MEMBER_COUNT+1.0)
    return np.log(p/(1-p))
def rm(m): return np.log1p(np.asarray(m,dtype=np.float64)/THRESHOLD)
def rawp(k): return (np.asarray(k,dtype=np.float64)+0.5)/(MEMBER_COUNT+1.0)
def nll(y,p):
    y=np.asarray(y,dtype=np.float64); p=np.clip(np.asarray(p,dtype=np.float64),EPS,1-EPS)
    return float(np.mean(-(y*np.log(p)+(1-y)*np.log1p(-p))))
def brier(y,p): return float(np.mean((np.asarray(y)-np.asarray(p))**2))
def ece(y,p,bins=5):
    y=np.asarray(y); p=np.asarray(p); edges=np.linspace(0,1,bins+1); out=0.0
    for i in range(bins):
        mask=(p>=edges[i]) & ((p<edges[i+1]) if i<bins-1 else (p<=edges[i+1]))
        if np.any(mask): out += float(np.mean(mask))*abs(float(np.mean(p[mask])-np.mean(y[mask])))
    return out

def fit_logit(X,y):
    X=np.asarray(X,dtype=np.float64); y=np.asarray(y,dtype=np.float64); D=np.column_stack([np.ones(len(X)),X])
    def fg(b):
        eta=D@b; return float(np.sum(np.logaddexp(0,eta)-y*eta)), D.T@(expit(eta)-y)
    res=minimize(lambda b:fg(b)[0],np.zeros(D.shape[1]),jac=lambda b:fg(b)[1],method='BFGS',options={'gtol':1e-10,'maxiter':2000})
    b=np.asarray(res.x,dtype=np.float64); grad=fg(b)[1]
    if not np.isfinite(b).all() or np.max(np.abs(grad))>1e-6: raise RuntimeError('TSDC_DEV_MLE')
    return b
def predict(X,b): return expit(np.column_stack([np.ones(len(X)),np.asarray(X)])@np.asarray(b))

def add_decision_state(df, world_root:Path):
    states=[]; cache={}
    for r in df.itertuples(index=False):
        w=r.world_id; sid=int(r.stop_id)
        if w not in cache:
            obs=pd.read_csv(world_root/w/'observation_tape.csv'); stops=pd.read_csv(world_root/w/'stop_events.csv')
            arr=[0.0]
            for s in range(2,16):
                prev=stops.loc[stops.stop_id==s-1].iloc[0]; end=int(prev.end_index)
                arr.append(float(obs.iloc[end].measured_gas_ppm))
            cache[w]=arr
        states.append(cache[w][sid-1])
    z=df.copy(); z['decision_sensor_state_ppm']=states; return z

def load_spent(root:Path):
    ve=root/'vm_evidence'
    cal=add_decision_state(pd.read_csv(ve/'CTPI_M2_SOURCE_INTERVENTION_CAL_FREEZE_20260903_R1'/'CAL_RECORDS.csv'),ve/'CTPI_M2_SOURCE_INTERVENTION_CAL_20260902_R1'); cal['split']='CAL'
    con=add_decision_state(pd.read_csv(ve/'CTPI_M2_SOURCE_INTERVENTION_CONFIRM_GATE_20260903_R1'/'CONFIRM_RECORDS.csv'),ve/'CTPI_M2_SOURCE_INTERVENTION_CONFIRM_20260902_R1'); con['split']='CONFIRM'
    d=pd.concat([cal,con],ignore_index=True)
    if len(d)!=900 or d.world_id.nunique()!=60 or not np.all(d.groupby('world_id').size().to_numpy()==15): raise RuntimeError('TSDC_DEV_CARDINALITY')
    if not np.allclose(d.loc[d.stop_id==1,'decision_sensor_state_ppm'],0.0): raise RuntimeError('TSDC_FIRST_STATE')
    return d,cal,con

def suffix_fold(world_id:str)->int:
    m=re.search(r'_(\d\d)$',world_id)
    if not m: raise ValueError(world_id)
    return int(m.group(1))

def paired_table(d,p0,p1):
    tmp=d[['world_id','house','observed_event']].copy(); tmp['p0']=p0; tmp['p1']=p1; rows=[]
    for (w,h),g in tmp.groupby(['world_id','house']):
        yy=g.observed_event.to_numpy(); rows.append((w,h,nll(yy,g.p0),nll(yy,g.p1),brier(yy,g.p0),brier(yy,g.p1)))
    return pd.DataFrame(rows,columns=['world_id','house','nll0','nll1','brier0','brier1'])
def signs(t,col0,col1):
    w=int((t[col1]<t[col0]-1e-15).sum()); l=int((t[col1]>t[col0]+1e-15).sum()); return {'wins':w,'losses':l,'ties':len(t)-w-l,'p_one_sided':float(binomtest(w,w+l,.5,alternative='greater').pvalue) if w+l else 1.0}

def fixed_point_free_affine_perms(n=20,count=31):
    out=[]
    for a in range(n):
        if math.gcd(a,n)!=1: continue
        for b in range(n):
            perm=tuple((a*i+b)%n for i in range(n))
            if len(set(perm))==n and all(perm[i]!=i for i in range(n)) and perm not in out:
                out.append(perm)
                if len(out)==count: return out
    raise RuntimeError('NOT_ENOUGH_PERMS')

def shift_by_perm(d,col,perm):
    vals=np.empty(len(d),dtype=float)
    lookup=d.set_index(['world_id','stop_id'])[col]
    for h,dh in d.groupby('house',sort=True):
        worlds=sorted(dh.world_id.unique())
        if len(worlds)!=20: raise RuntimeError('HOUSE_WORLD_COUNT')
        mapping={worlds[i]:worlds[perm[i]] for i in range(20)}
        for idx,r in dh.iterrows(): vals[idx]=lookup.loc[(mapping[r.world_id],r.stop_id)]
    return vals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--package-root',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    root=Path(args.package_root); d,cal,con=load_spent(root)
    y=d.observed_event.to_numpy(dtype=int); X=np.column_stack([rk(d.member_hit_count),rm(d.decision_sensor_state_ppm)]); base=rawp(d.member_hit_count)
    beta=fit_logit(X,y); beta_delta=float(np.max(np.abs(beta-FROZEN_BETA)))
    if beta_delta>1e-12: raise RuntimeError(f'TSDC_FROZEN_BETA_PARITY:{beta_delta}')

    poof=np.zeros(len(d)); pstate=np.zeros(len(d)); betas=[]
    for fold in range(10):
        te=np.asarray([suffix_fold(w)==fold for w in d.world_id]); tr=~te
        b=fit_logit(X[tr],y[tr]); bs=fit_logit(X[tr,1:2],y[tr]); betas.append(b)
        poof[te]=predict(X[te],b); pstate[te]=predict(X[te,1:2],bs)
    betas=np.asarray(betas)
    tab=paired_table(d,base,poof); tabs=paired_table(d,pstate,poof)

    per_house={}
    for h in sorted(d.house.unique()):
        m=d.house.to_numpy()==h; th=tab[tab.house==h]
        per_house[h]={'raw_nll':nll(y[m],base[m]),'oof_nll':nll(y[m],poof[m]),'raw_brier':brier(y[m],base[m]),'oof_brier':brier(y[m],poof[m]),'nll_sign':signs(th,'nll0','nll1'),'brier_sign':signs(th,'brier0','brier1')}

    loho={}
    for h in sorted(d.house.unique()):
        te=d.house.to_numpy()==h; tr=~te; b=fit_logit(X[tr],y[tr]); pp=predict(X[te],b); bb=base[te]; sub=d.loc[te].copy(); sub['bb']=bb; sub['pp']=pp; tt=paired_table(sub,bb,pp)
        loho[h]={'raw_nll':nll(y[te],bb),'tsdc_nll':nll(y[te],pp),'nll_sign':signs(tt,'nll0','nll1'),'beta':b.tolist()}

    Xcal=np.column_stack([rk(cal.member_hit_count),rm(cal.decision_sensor_state_ppm)]); ycal=cal.observed_event.to_numpy(int); bcal=fit_logit(Xcal,ycal)
    Xcon=np.column_stack([rk(con.member_hit_count),rm(con.decision_sensor_state_ppm)]); ycon=con.observed_event.to_numpy(int); pc=predict(Xcon,bcal); bc=rawp(con.member_hit_count); tc=paired_table(con,bc,pc)

    perms=fixed_point_free_affine_perms(); real=nll(y,predict(X,beta)); kn=[]; sn=[]
    for perm in perms:
        kk=shift_by_perm(d,'member_hit_count',perm); Xk=np.column_stack([rk(kk),rm(d.decision_sensor_state_ppm)]); kn.append(nll(y,predict(Xk,beta)))
        ss=shift_by_perm(d,'decision_sensor_state_ppm',perm); Xs=np.column_stack([rk(d.member_hit_count),rm(ss)]); sn.append(nll(y,predict(Xs,beta)))

    report={
      'contract':'CTPI_M2_TSDC_DEV_AUDIT_V0','status':'DEV_SPENT_ONLY_NOT_CONFIRMATORY','events':900,'worlds':60,
      'frozen_beta':FROZEN_BETA.tolist(),'refit_beta':beta.tolist(),'beta_max_abs_diff':beta_delta,
      'oof':{
        'raw':{'nll':nll(y,base),'brier':brier(y,base),'ece5':ece(y,base)},
        'tsdc':{'nll':nll(y,poof),'brier':brier(y,poof),'ece5':ece(y,poof)},
        'sensor_only':{'nll':nll(y,pstate),'brier':brier(y,pstate),'ece5':ece(y,pstate)},
        'vs_raw_nll':signs(tab,'nll0','nll1'),'vs_raw_brier':signs(tab,'brier0','brier1'),
        'vs_sensor_nll':signs(tabs,'nll0','nll1'),'vs_sensor_brier':signs(tabs,'brier0','brier1'),
        'fold_beta_mean':betas.mean(axis=0).tolist(),'fold_beta_min':betas.min(axis=0).tolist(),'fold_beta_max':betas.max(axis=0).tolist(),
        'per_house':per_house,'leave_one_house_out':loho},
      'retrospective_cal_to_old_confirm':{
        'status':'DEV_ONLY_OLD_CONFIRM_ALREADY_OPENED','cal_beta':bcal.tolist(),
        'raw_nll':nll(ycon,bc),'tsdc_nll':nll(ycon,pc),'raw_brier':brier(ycon,bc),'tsdc_brier':brier(ycon,pc),'raw_ece5':ece(ycon,bc),'tsdc_ece5':ece(ycon,pc),
        'nll_sign':signs(tc,'nll0','nll1'),'brier_sign':signs(tc,'brier0','brier1')},
      'destructive_controls':{
        'count':31,'permutations':'31 unique fixed-point-free affine permutations over 20 worlds within each House, stop_id preserved','real_in_sample_nll':real,
        'transport_destroyed_nll':{'min':float(min(kn)),'median':float(np.median(kn)),'max':float(max(kn)),'real_better':int(sum(real<x for x in kn))},
        'sensor_state_destroyed_nll':{'min':float(min(sn)),'median':float(np.median(sn)),'max':float(max(sn)),'real_better':int(sum(real<x for x in sn))}},
      'authorization':{'fresh_confirm_only':True,'m3':False,'cpp':False,'ros':False,'closed_loop':False}}
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print('CTPI_M2_TSDC_DEV_AUDIT=PASS')
    print(json.dumps({'raw_nll':report['oof']['raw']['nll'],'tsdc_nll':report['oof']['tsdc']['nll'],'raw_brier':report['oof']['raw']['brier'],'tsdc_brier':report['oof']['tsdc']['brier'],'beta_delta':beta_delta},sort_keys=True))

if __name__=='__main__': main()
