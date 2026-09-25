#!/usr/bin/env python3
"""DASN D0 mechanism screen on frozen D1R reference data.

No new simulation. No target generation. No new model family.

Primary question:
Does same-realization shared localization error contain a reproducible
source-displacement-aligned component beyond gain/factor/readout/boundary
controls?

Input:
- D1R reference tensor [168,16,10,30]
- frozen panel TSV

This script implements:
- odd/even 1-based probe split;
- 8/8 forward and reverse realization directions;
- regularized coordinate Ridge readout;
- shrinkage-LDA posterior-mean readout;
- source-centered same-realization cross-view localization statistic T;
- pairing-destruction null;
- common-gain residualization;
- generic low-rank residual PCA control;
- local source-sensitivity Jacobian displacement projection;
- source-shuffled Jacobian control;
- boundary/internal audit.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.decomposition import PCA

RIDGE_ALPHAS=np.logspace(-4,4,9)
TEMPS=np.array([0.25,0.5,1.0,2.0,4.0])
LAM_RATIO=1e-2

def temp_probs(p,t):
    lp=np.log(np.clip(p,1e-300,1.0))/t
    lp-=lp.max(axis=1,keepdims=True)
    q=np.exp(lp); q/=q.sum(axis=1,keepdims=True)
    return q

def centered(e):
    return e-e.mean(axis=1,keepdims=True)

def t_stat(ea,eb,mask=None):
    a=centered(ea); b=centered(eb)
    if mask is not None:
        a=a[mask]; b=b[mask]
    vals=np.sum(a*b,axis=2).sum(axis=1)/(a.shape[1]-1)
    return float(vals.mean()), vals

def pairing_null(ea,eb,B,seed):
    rng=np.random.default_rng(seed)
    a=centered(ea); b=centered(eb)
    ns,r,_=a.shape
    out=np.empty(B)
    for k in range(B):
        s=0.0
        for i in range(ns):
            p=rng.permutation(r)
            s+=np.sum(a[i]*b[i,p])/(r-1)
        out[k]=s/ns
    return out

def get_view(X,probes):
    return X[:,:,:,probes].reshape(X.shape[0],X.shape[1],-1)

def ridge_errors(Xv,xy,train_reps,diag_reps):
    folds=[train_reps[i*2:(i+1)*2] for i in range(4)]
    best=None
    for alpha in RIDGE_ALPHAS:
        vals=[]
        for vf in folds:
            s=set(map(int,vf))
            tr=np.array([r for r in train_reps if int(r) not in s])
            Xt=Xv[:,tr].reshape(-1,Xv.shape[-1])
            yt=np.repeat(xy,len(tr),axis=0)
            Xh=Xv[:,vf].reshape(-1,Xv.shape[-1])
            yh=np.repeat(xy,len(vf),axis=0)
            sc=StandardScaler().fit(Xt)
            m=Ridge(alpha=float(alpha)).fit(sc.transform(Xt),yt)
            pr=m.predict(sc.transform(Xh))
            vals.append(np.mean(np.sum((pr-yh)**2,axis=1)))
        score=float(np.mean(vals))
        if best is None or score<best[0]:
            best=(score,float(alpha))
    Xt=Xv[:,train_reps].reshape(-1,Xv.shape[-1])
    yt=np.repeat(xy,len(train_reps),axis=0)
    sc=StandardScaler().fit(Xt)
    m=Ridge(alpha=best[1]).fit(sc.transform(Xt),yt)
    pr=m.predict(sc.transform(Xv[:,diag_reps].reshape(-1,Xv.shape[-1])))
    pr=pr.reshape(len(xy),len(diag_reps),2)
    return pr-xy[:,None,:], best[1]

def lda_errors(Xv,xy,train_reps,diag_reps):
    N=len(xy)
    folds=[train_reps[i*2:(i+1)*2] for i in range(4)]
    scores={float(t):[] for t in TEMPS}
    for vf in folds:
        s=set(map(int,vf))
        tr=np.array([r for r in train_reps if int(r) not in s])
        Xt=Xv[:,tr].reshape(-1,Xv.shape[-1])
        yt=np.repeat(np.arange(N),len(tr))
        Xh=Xv[:,vf].reshape(-1,Xv.shape[-1])
        yh=np.repeat(np.arange(N),len(vf))
        sc=StandardScaler().fit(Xt)
        lda=LinearDiscriminantAnalysis(solver="lsqr",shrinkage="auto").fit(sc.transform(Xt),yt)
        p=lda.predict_proba(sc.transform(Xh))
        for t in TEMPS:
            q=temp_probs(p,float(t))
            scores[float(t)].append(float(np.mean(np.log(np.clip(q[np.arange(len(yh)),yh],1e-300,1)))))
    t=max(scores,key=lambda k:np.mean(scores[k]))
    Xt=Xv[:,train_reps].reshape(-1,Xv.shape[-1])
    yt=np.repeat(np.arange(N),len(train_reps))
    sc=StandardScaler().fit(Xt)
    lda=LinearDiscriminantAnalysis(solver="lsqr",shrinkage="auto").fit(sc.transform(Xt),yt)
    p=temp_probs(lda.predict_proba(sc.transform(Xv[:,diag_reps].reshape(-1,Xv.shape[-1]))),t)
    pr=(p@xy).reshape(N,len(diag_reps),2)
    return pr-xy[:,None,:], float(t)

def gain_residualize(ea,eb,Cdiag):
    g=np.log1p(Cdiag.sum(axis=(2,3)))
    g-=g.mean(axis=1,keepdims=True)
    a=centered(ea); b=centered(eb)
    gv=g.reshape(-1,1)
    ba=np.linalg.lstsq(gv,a.reshape(-1,2),rcond=None)[0]
    bb=np.linalg.lstsq(gv,b.reshape(-1,2),rcond=None)[0]
    ar=(a.reshape(-1,2)-gv@ba).reshape(a.shape)
    br=(b.reshape(-1,2)-gv@bb).reshape(b.shape)
    return ar,br

def grid_and_jac(mu,panel):
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in panel.iterrows()}
    J=np.zeros((len(panel),mu.shape[1],2))
    for s,r in panel.iterrows():
        i,j=int(r.pmfs_i),int(r.pmfs_j)
        for dim,(di,dj,col) in enumerate(((1,0,"x_m"),(0,1,"y_m"))):
            lo=grid.get((i-di,j-dj)); hi=grid.get((i+di,j+dj))
            if lo is not None and hi is not None:
                den=float(panel.loc[hi,col]-panel.loc[lo,col])
                J[s,:,dim]=(mu[hi]-mu[lo])/den
            elif hi is not None:
                den=float(panel.loc[hi,col]-panel.loc[s,col])
                J[s,:,dim]=(mu[hi]-mu[s])/den
            else:
                den=float(panel.loc[s,col]-panel.loc[lo,col])
                J[s,:,dim]=(mu[s]-mu[lo])/den
    return J

def displacement_from_residual(res,J,lam_ratio=LAM_RATIO):
    N,r,D=res.shape
    out=np.zeros((N,r,2))
    for s in range(N):
        A=J[s].T@J[s]
        lam=lam_ratio*(np.trace(A)/2+1e-12)
        K=np.linalg.inv(A+lam*np.eye(2))@J[s].T
        out[s]=res[s]@K.T
    return out

def j_displacement(Xv,train_reps,diag_reps,panel,J_override=None):
    mu=Xv[:,train_reps].mean(axis=1)
    J=grid_and_jac(mu,panel) if J_override is None else J_override
    res=Xv[:,diag_reps]-mu[:,None,:]
    return displacement_from_residual(res,J), grid_and_jac(mu,panel), mu

def factor2_control(Xfull,XA,XB,train_reps,diag_reps,panel):
    mu=Xfull[:,train_reps].mean(axis=1)
    tr=(Xfull[:,train_reps]-mu[:,None,:]).reshape(-1,300)
    pca=PCA(n_components=2,svd_solver="full").fit(tr)
    de=(Xfull[:,diag_reps]-mu[:,None,:]).reshape(-1,300)
    rem=(de-pca.inverse_transform(pca.transform(de))).reshape(len(panel),len(diag_reps),10,30)
    ra=rem[:,:,:,::2].reshape(len(panel),len(diag_reps),-1)
    rb=rem[:,:,:,1::2].reshape(len(panel),len(diag_reps),-1)
    muA=XA[:,train_reps].mean(axis=1); muB=XB[:,train_reps].mean(axis=1)
    JA=grid_and_jac(muA,panel); JB=grid_and_jac(muB,panel)
    return displacement_from_residual(ra,JA), displacement_from_residual(rb,JB), float(pca.explained_variance_ratio_.sum()), JA, JB, ra, rb

def summarize_null(obs,null):
    return {
      "obs":float(obs),
      "null_q025":float(np.quantile(null,.025)),
      "null_median":float(np.median(null)),
      "null_q975":float(np.quantile(null,.975)),
      "mc_p_ge":float((np.sum(null>=obs)+1)/(len(null)+1))
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tensor",type=Path,required=True)
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--permutations",type=int,default=5000)
    ap.add_argument("--j-shuffles",type=int,default=300)
    args=ap.parse_args()

    C=np.load(args.tensor,allow_pickle=False)
    panel=pd.read_csv(args.panel,sep="\t")
    assert C.shape==(168,16,10,30)
    X=np.log1p(C); Xfull=X.reshape(168,16,300)
    XA=get_view(X,np.arange(0,30,2)); XB=get_view(X,np.arange(1,30,2))
    xy=panel[["x_m","y_m"]].to_numpy(float)
    boundary=((panel.pmfs_i==panel.pmfs_i.min())|(panel.pmfs_i==panel.pmfs_i.max())|
              (panel.pmfs_j==panel.pmfs_j.min())|(panel.pmfs_j==panel.pmfs_j.max())).to_numpy()

    result={"status":"DISCOVERY_ONLY","decision":None,"directions":[]}
    for di,(tr,de) in enumerate(((np.arange(8),np.arange(8,16)),(np.arange(8,16),np.arange(8)))):
        row={"direction":di}
        rA,aA=ridge_errors(XA,xy,tr,de); rB,aB=ridge_errors(XB,xy,tr,de)
        lA,tA=lda_errors(XA,xy,tr,de); lB,tB=lda_errors(XB,xy,tr,de)

        for name,ea,eb,seed in (("ridge",rA,rB,100+di),("lda",lA,lB,200+di)):
            obs,_=t_stat(ea,eb)
            null=pairing_null(ea,eb,args.permutations,seed)
            grA,grB=gain_residualize(ea,eb,C[:,de])
            gainT,_=t_stat(grA,grB)
            row[name]={
              "T_m2":summarize_null(obs,null),
              "median_error_A_m":float(np.median(np.linalg.norm(ea,axis=2))),
              "median_error_B_m":float(np.median(np.linalg.norm(eb,axis=2))),
              "gain_residual_T_m2":float(gainT),
              "internal_T_m2":float(t_stat(ea,eb,~boundary)[0]),
              "boundary_T_m2":float(t_stat(ea,eb,boundary)[0])
            }
        row["ridge"]["alpha_A"]=float(aA); row["ridge"]["alpha_B"]=float(aB)
        row["lda"]["temperature_A"]=float(tA); row["lda"]["temperature_B"]=float(tB)

        dA,JA,muA=j_displacement(XA,tr,de,panel)
        dB,JB,muB=j_displacement(XB,tr,de,panel)
        jobs,_=t_stat(dA,dB)
        jnull=pairing_null(dA,dB,args.permutations,300+di)
        gdA,gdB=gain_residualize(dA,dB,C[:,de])

        fdA,fdB,ev,JA2,JB2,ra,rb=factor2_control(Xfull,XA,XB,tr,de,panel)
        fT,_=t_stat(fdA,fdB)
        fnull=pairing_null(fdA,fdB,args.permutations,400+di)

        # source-shuffled Jacobian null before and after generic factor removal
        rng=np.random.default_rng(500+di)
        sj=[]; sjf=[]
        for k in range(args.j_shuffles):
            p=rng.permutation(168)
            da=displacement_from_residual(XA[:,de]-muA[:,None,:],JA[p])
            db=displacement_from_residual(XB[:,de]-muB[:,None,:],JB[p])
            sj.append(t_stat(da,db)[0])
            daf=displacement_from_residual(ra,JA2[p])
            dbf=displacement_from_residual(rb,JB2[p])
            sjf.append(t_stat(daf,dbf)[0])
        sj=np.asarray(sj); sjf=np.asarray(sjf)

        row["sensitivity_projection"]={
          "T_m2":summarize_null(jobs,jnull),
          "gain_residual_T_m2":float(t_stat(gdA,gdB)[0]),
          "internal_T_m2":float(t_stat(dA,dB,~boundary)[0]),
          "boundary_T_m2":float(t_stat(dA,dB,boundary)[0]),
          "source_shuffled_J_median":float(np.median(sj)),
          "source_shuffled_J_q95":float(np.quantile(sj,.95)),
          "source_shuffled_J_mc_p_ge":float((np.sum(sj>=jobs)+1)/(len(sj)+1)),
          "generic_factor2_explained_variance":float(ev),
          "factor2_residual_T_m2":summarize_null(fT,fnull),
          "factor2_source_shuffled_J_median":float(np.median(sjf)),
          "factor2_source_shuffled_J_q95":float(np.quantile(sjf,.95)),
          "factor2_source_shuffled_J_mc_p_ge":float((np.sum(sjf>=fT)+1)/(len(sjf)+1))
        }
        result["directions"].append(row)

    # frozen qualitative decision
    # Shared paired error is robust, but displacement specificity must survive
    # the equal-dimension generic-factor and source-shuffled-J controls in both directions.
    sig_shared=all(d["ridge"]["T_m2"]["mc_p_ge"]<0.01 and d["lda"]["T_m2"]["mc_p_ge"]<0.01
                   for d in result["directions"])
    sig_specific=all(d["sensitivity_projection"]["factor2_source_shuffled_J_mc_p_ge"]<0.05
                     for d in result["directions"])
    if not sig_shared:
        decision="D0_STOP_NO_REPRODUCIBLE_SHARED_LOCALIZATION_ERROR"
    elif not sig_specific:
        decision="D0_HOLD_SHARED_ERROR_NOT_DISPLACEMENT_SPECIFIC"
    else:
        decision="D0_ADVANCE_MECHANISM_ONLY"
    result["decision"]=decision
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
