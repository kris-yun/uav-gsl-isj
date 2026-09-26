#!/usr/bin/env python3
from __future__ import annotations
import argparse, math, json
from pathlib import Path
import numpy as np, pandas as pd

EPS=1e-9

def edf(x):
    x=np.asarray(x,float).reshape(-1)
    s=np.sort(x)
    return np.searchsorted(s,x,side="right")/len(x)

def rank_of(scores,true_idx,higher=True):
    s=np.asarray(scores,float)
    v=s[true_idx]
    return float(1+np.sum(s>v)) if higher else float(1+np.sum(s<v))

def profiled_mark_ll(obs, pred):
    obs=np.asarray(obs,float)
    pred=np.asarray(pred,float)
    m=obs>0
    n=int(m.sum())
    if n<4:
        return 0.0
    y=np.log(obs[m])
    x=np.log(np.clip(pred[m],EPS,None))
    xc=x-x.mean(); yc=y-y.mean()
    den=float(xc@xc)
    b=max(0.0,float(xc@yc/den)) if den>1e-12 else 0.0
    a=float(y.mean()-b*x.mean())
    r=y-(a+b*x)
    rss=max(float(r@r),1e-12)
    return -0.5*n*math.log(rss/n)

def source_partner(panel,house,sid):
    p=panel[(panel.house==house)&(panel.source_id==sid)].iloc[0]
    q=panel[(panel.house==house)&(panel.pair_id==p.pair_id)&(panel.source_id!=sid)]
    return str(q.iloc[0].source_id)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bank",type=Path,required=True,
      help="CSV: environment_index,house,wind,source_index,source_id,probe_rank,presence_prob,multiplicity_mean_unconditional,multiplicity_mean_conditional")
    ap.add_argument("--targets",type=Path,required=True)
    ap.add_argument("--target-manifest",type=Path,required=True)
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    bank=pd.read_csv(a.bank)
    targ=np.load(a.targets,allow_pickle=False)
    man=pd.read_csv(a.target_manifest,sep="\t")
    panel=pd.read_csv(a.panel,sep="\t")

    req={"environment_index","house","wind","source_index","source_id","probe_rank",
         "presence_prob","multiplicity_mean_unconditional","multiplicity_mean_conditional"}
    if not req.issubset(bank.columns): raise SystemExit(f"bank columns missing {req-set(bank.columns)}")
    if targ.shape!=(3,6,4,10,30): raise SystemExit(f"target shape {targ.shape}")

    rows=[]
    envsum=[]
    for e in range(3):
        b=bank[bank.environment_index==e].copy()
        sources=(b[["source_index","source_id","house","wind"]].drop_duplicates()
                 .sort_values("source_index"))
        if len(sources)!=6: raise SystemExit(f"env {e}: source count {len(sources)}")
        house=str(sources.iloc[0].house)
        pmat=np.zeros((6,30)); umat=np.zeros((6,30)); cmat=np.zeros((6,30))
        for si in range(6):
            g=b[b.source_index==si].sort_values("probe_rank")
            if len(g)!=30: raise SystemExit(f"env {e} source {si}: probe count {len(g)}")
            pmat[si]=np.clip(g.presence_prob.to_numpy(float),1e-6,1-1e-6)
            umat[si]=np.clip(g.multiplicity_mean_unconditional.to_numpy(float),EPS,None)
            cmat[si]=np.clip(g.multiplicity_mean_conditional.to_numpy(float),EPS,None)

        env_delta=[]; ranks0=[]; ranksM=[]; ranksR=[]; rescue=harm=0
        for si in range(6):
          sid=str(sources[sources.source_index==si].iloc[0].source_id)
          partner=source_partner(panel,house,sid)
          pi=int(sources.index[sources.source_id==partner][0]) if partner in set(sources.source_id) else None
          # safer mapping
          pi=int(sources[sources.source_id==partner].iloc[0].source_index)
          for j in range(4):
            y=targ[e,si,j]
            h=(y>0).astype(int)
            occ=np.array([(h*np.log(pmat[k][None,:])+
                           (1-h)*np.log1p(-pmat[k][None,:])).sum() for k in range(6)])
            # candidate mark repeated across ten observed times
            mark=np.array([profiled_mark_ll(y, np.tile(cmat[k],(10,1))) for k in range(6)])
            comb=occ+mark

            # ICRA rank analogue, expected concentration proxy = unconditional multiplicity
            my=edf(y)
            rankdist=[]
            for k in range(6):
                pred=np.tile(umat[k],(10,1))
                rankdist.append(float(((edf(pred)-my)**2).sum()))
            rankdist=np.asarray(rankdist)

            r0=rank_of(occ,si,True)
            rm=rank_of(comb,si,True)
            rr=rank_of(rankdist,si,False)
            ranks0.append(r0); ranksM.append(rm); ranksR.append(rr)
            env_delta.append((mark[si]-mark[pi]))
            if r0>1 and rm==1: rescue+=1
            if r0==1 and rm>1: harm+=1
            rows.append(dict(environment_index=e,house=house,source_id=sid,target_index=j,
                             paired_neighbor=partner,rank_B0=r0,rank_M=rm,rank_ICRA_rank=rr,
                             delta_pair_mark=float(mark[si]-mark[pi]),
                             mark_true=float(mark[si]),mark_partner=float(mark[pi])))

        envsum.append(dict(
          environment_index=e,house=house,
          B0_mean_rank=float(np.mean(ranks0)),B0_top1=float(np.mean(np.asarray(ranks0)==1)),
          M_mean_rank=float(np.mean(ranksM)),M_top1=float(np.mean(np.asarray(ranksM)==1)),
          ICRA_rank_mean_rank=float(np.mean(ranksR)),ICRA_rank_top1=float(np.mean(np.asarray(ranksR)==1)),
          mean_delta_pair_mark=float(np.mean(env_delta)),
          rescued_top1=int(rescue),harmed_top1=int(harm)
        ))

    detail=pd.DataFrame(rows); summ=pd.DataFrame(envsum)
    detail.to_csv(a.out/"TARGET_DETAIL.csv",index=False,float_format="%.17g")
    summ.to_csv(a.out/"ENVIRONMENT_SUMMARY.csv",index=False,float_format="%.17g")

    g=[
      bool((summ.mean_delta_pair_mark>0).all()),
      bool((summ.M_mean_rank<=summ.B0_mean_rank).all()),
      int((summ.M_mean_rank<summ.B0_mean_rank).sum())>=2,
      bool((summ.M_top1>=summ.B0_top1).all()),
      bool((summ.M_mean_rank<=summ.ICRA_rank_mean_rank).all()),
      bool(not ((detail.rank_B0==1)&(detail.rank_M>3)).any()),
    ]
    decision="ME_PMFS_D0_MARK_FORWARD_SIGNAL" if all(g) else "ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE"
    result={"decision":decision,"gates":g,"environment_summary":envsum,
            "note":"If decision is FORWARD_INADEQUATE, verify the predeclared GADEN-reference upper diagnostic before interpreting."}
    (a.out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
