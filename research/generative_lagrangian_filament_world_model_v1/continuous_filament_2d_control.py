#!/usr/bin/env python3
"""Continuous-filament anti-overengineering control for House02.

No neural model. Restores only physical state that scalar M4 deletes:
- continuous sub-cell XY filament position;
- deterministic filament sigma/age growth;
- GADEN-compatible stochastic displacement scale;
- GADEN-like tangential obstacle deflection.

Still deliberately omits:
- z dynamics / Wz / buoyancy;
- 3-D line of sight;
- learned residuals.

One global observation scale is fitted on S1W1/S2W1/S1W2 only, then S2W2 is
evaluated. House02 is development-only.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F

DT=0.1
CELL_M=0.1
FILAMENTS_PER_S=7.0
SIGMA0_CM=10.0
GAMMA_CM2_S=15.0
NOISE_DISP_STD_M=0.01
TARGET_TIMES=(50,75,100,125,150,175,200,225,250,275)
TRAIN=(("S1","W1"),("S2","W1"),("S1","W2"))
EVAL=(("S2","W2"),("S2","W1"),("S1","W2"))
PLUMES=("A","B")
RNG_SEED=84017

def wind_ids(mm,max_steps):
    return mm.gaden_wind_index_schedule(max_steps,DT,1.0,11,1,10)

def source_position(source_map):
    a=source_map.astype(np.float64)
    ids=np.argwhere(a>0)
    if len(ids)==0: raise ValueError("empty source map")
    w=a[a>0]
    r=float(np.sum((ids[:,0]+0.5)*w)/np.sum(w))
    c=float(np.sum((ids[:,1]+0.5)*w)/np.sum(w))
    return np.array([r,c],dtype=np.float64)

def cell_free(pos,free):
    rr=np.floor(pos[:,0]).astype(np.int64)
    cc=np.floor(pos[:,1]).astype(np.int64)
    inside=(rr>=0)&(rr<free.shape[0])&(cc>=0)&(cc<free.shape[1])
    ok=np.zeros(len(pos),dtype=bool)
    ii=np.where(inside)[0]
    ok[ii]=free[rr[ii],cc[ii]]
    return ok,inside,rr,cc

def advance_particles(pos,sigma,active,wind,free,rng,slide=True):
    ids=np.where(active)[0]
    if len(ids)==0: return
    p=pos[ids]
    rr=np.floor(p[:,0]).astype(np.int64)
    cc=np.floor(p[:,1]).astype(np.int64)
    w=wind[rr,cc,:2]
    noise=rng.normal(0.0,NOISE_DISP_STD_M/CELL_M,size=(len(ids),2))
    disp=w*(DT/CELL_M)+noise
    q=p+disp
    ok,inside,rq,cq=cell_free(q,free)

    # clear endpoints
    pos[ids[ok]]=q[ok]

    bad=~ok
    if np.any(bad):
        bid=ids[bad]
        bp=p[bad]; bq=q[bad]; bdisp=disp[bad]
        binside=inside[bad]
        # out-of-bounds filaments disappear
        active[bid[~binside]]=False
        hit_local=np.where(binside)[0]
        if len(hit_local)>0:
            hid=bid[hit_local]
            hp=bp[hit_local]; hq=bq[hit_local]; hd=bdisp[hit_local]
            if slide:
                sr=np.floor(hp[:,0]).astype(np.int64)
                sc=np.floor(hp[:,1]).astype(np.int64)
                er=np.floor(hq[:,0]).astype(np.int64)
                ec=np.floor(hq[:,1]).astype(np.int64)
                normal=np.stack((sr-er,sc-ec),axis=1).astype(np.float64)
                nn=np.sum(normal*normal,axis=1,keepdims=True)
                fallback=-hd/np.maximum(np.linalg.norm(hd,axis=1,keepdims=True),1e-12)
                nunit=np.where(nn>0,normal/np.sqrt(np.maximum(nn,1e-12)),fallback)
                tangent=hd-nunit*np.sum(hd*nunit,axis=1,keepdims=True)
                q2=hp+tangent
                ok2,inside2,_,_=cell_free(q2,free)
                pos[hid[ok2]]=q2[ok2]
                # blocked again -> restore old hp; out-of-bounds -> inactive
                active[hid[~inside2]]=False
            # if slide=False, blocked particles stay at hp.

    # sigma growth applies to all currently active filaments
    ai=np.where(active)[0]
    sigma[ai]+=GAMMA_CM2_S/(2.0*sigma[ai])*DT

def render_raw(pos,sigma,active,h,w):
    ids=np.where(active)[0]
    out=np.zeros((h,w),dtype=np.float64)
    if len(ids)==0: return out.astype(np.float32)
    rr,cc=np.meshgrid(np.arange(h,dtype=np.float64)+0.5,
                      np.arange(w,dtype=np.float64)+0.5,indexing="ij")
    flat_r=rr.reshape(-1); flat_c=cc.reshape(-1)
    pp=pos[ids]; ss=sigma[ids]
    # relative centre amplitude; global physical scale is fitted source-blind.
    for start in range(0,len(ids),128):
        p=pp[start:start+128]; s=ss[start:start+128]
        sig_cell=(s/100.0)/CELL_M
        dr=flat_r[None]-p[:,0,None]
        dc=flat_c[None]-p[:,1,None]
        d2=dr*dr+dc*dc
        amp=(SIGMA0_CM/s)**3
        z=amp[:,None]*np.exp(-d2/(2.0*sig_cell[:,None]**2))
        out.reshape(-1)[:] += z.sum(axis=0)
    return out.astype(np.float32)

def simulate(source_pos,wind_seq,free,wind_index,slide=True):
    max_steps=int(round(max(TARGET_TIMES)/DT))
    max_birth=int(math.ceil(FILAMENTS_PER_S*max(TARGET_TIMES)))+8
    pos=np.zeros((max_birth,2),dtype=np.float64)
    sigma=np.full(max_birth,SIGMA0_CM,dtype=np.float64)
    active=np.zeros(max_birth,dtype=bool)
    born=0; acc=0.0
    rng=np.random.default_rng(RNG_SEED)
    records=[]; target_steps={int(round(t/DT)):i for i,t in enumerate(TARGET_TIMES)}
    h,w=free.shape
    for step in range(1,max_steps+1):
        acc+=FILAMENTS_PER_S*DT
        n=int(math.floor(acc+1e-12)); acc-=n
        if n:
            pos[born:born+n]=source_pos[None]
            sigma[born:born+n]=SIGMA0_CM
            active[born:born+n]=True
            born+=n
        wi=wind_index[step-1]
        advance_particles(pos,sigma,active,wind_seq[wi],free,rng,slide)
        if step in target_steps:
            records.append(render_raw(pos,sigma,active,h,w))
    return np.stack(records,axis=0)

def pool_log(raw,scale):
    x=torch.from_numpy(raw)[:,None]
    return F.avg_pool2d(torch.log1p(scale*x),2,ceil_mode=True)

def target(bank,s,w,ps):
    a=np.load(bank/"realizations"/f"{s}_{w}_{ps}"/"concentration.npy",allow_pickle=False).astype(np.float32)
    return F.avg_pool2d(torch.from_numpy(np.log1p(a))[:,None],2,ceil_mode=True)

def fit_scale(raws,targets,free):
    log_s=torch.tensor(0.0,dtype=torch.float64,requires_grad=True)
    opt=torch.optim.Adam([log_s],lr=.08)
    rawt=[torch.from_numpy(r.astype(np.float64))[:,None] for r in raws]
    tg=[t.double() for t in targets]
    f=free.double()
    for _ in range(250):
        s=torch.exp(log_s)
        loss=0.0
        for r,y in zip(rawt,tg):
            p=F.avg_pool2d(torch.log1p(s*r),2,ceil_mode=True)
            loss+=(((p-y)**2)*f).sum()/(f.sum()*p.shape[0])
        loss=loss/len(rawt)
        opt.zero_grad(); loss.backward(); opt.step()
    return float(torch.exp(log_s).detach())

def flat(x,free):
    m=free[0,0]>0.5
    return x[:,0][:,m].reshape(-1).double()

def metrics(p,y,free):
    a=flat(p,free); b=flat(y,free)
    na=torch.linalg.vector_norm(a); nb=torch.linalg.vector_norm(b)
    return {"amplitude_ratio":float(na/nb),
            "cosine":float(torch.dot(a,b)/(na*nb)),
            "pred_norm":float(na),"true_norm":float(nb)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--slide",action="store_true")
    args=ap.parse_args()
    root=args.repo_root
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dyn=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    g=bank/"geometry"
    free=(np.load(g/"obstacle_mask_z0p20.npy",allow_pickle=False)==0)
    src={s:source_position(np.load(g/f"source_map_{s}.npy",allow_pickle=False)) for s in ("S1","S2")}
    winds={w:np.load(dyn/f"wind_{w}_sequence_z0p20.npy",allow_pickle=False).astype(np.float64) for w in ("W1","W2")}
    # load only helper schedule from frozen M4 module
    import importlib.util
    p=root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py"
    spec=importlib.util.spec_from_file_location("mm",p); mm=importlib.util.module_from_spec(spec); spec.loader.exec_module(mm)
    ids=wind_ids(mm,int(round(max(TARGET_TIMES)/DT)))

    raw={}
    for pair in (("S1","W1"),("S2","W1"),("S1","W2"),("S2","W2")):
        s,w=pair
        print("simulate",s,w,"slide",args.slide,flush=True)
        raw[pair]=simulate(src[s],winds[w],free,ids,args.slide)

    free_raw=torch.from_numpy(free.astype(np.float32))[None,None]
    free_pool=1.0-F.max_pool2d(1.0-free_raw,2,ceil_mode=True)
    train_targets=[]
    train_raw=[]
    for pair in TRAIN:
        s,w=pair
        y=.5*(target(bank,s,w,"A")+target(bank,s,w,"B"))
        train_targets.append(y); train_raw.append(raw[pair])
    scale=fit_scale(train_raw,train_targets,free_pool)

    pred={k:pool_log(v,scale) for k,v in raw.items()}
    dw=pred[("S2","W2")]-pred[("S2","W1")]
    ds=pred[("S2","W2")]-pred[("S1","W2")]
    result={"mode":"CONTINUOUS_FILAMENT_2D_CONTROL","slide":args.slide,
            "physics":{"dt":DT,"cell_m":CELL_M,"filaments_per_s":FILAMENTS_PER_S,
                       "sigma0_cm":SIGMA0_CM,"gamma_cm2_s":GAMMA_CM2_S,
                       "noise_disp_std_m":NOISE_DISP_STD_M,"rng_seed":RNG_SEED},
            "fitted_observation_scale":scale,"plumes":{}}
    for ps in PLUMES:
        y22=target(bank,"S2","W2",ps); y21=target(bank,"S2","W1",ps); y12=target(bank,"S1","W2",ps)
        result["plumes"][ps]={
          "wind_delta":metrics(dw,y22-y21,free_pool),
          "source_delta":metrics(ds,y22-y12,free_pool),
          "field_mse":float(((((pred[("S2","W2")]-y22)**2)*free_pool).sum()/(free_pool.sum()*len(TARGET_TIMES))))
        }
    cos=[result["plumes"][p]["wind_delta"]["cosine"] for p in PLUMES]
    result["summary"]={"all_wind_cosine_gt_0p5":all(x>.5 for x in cos),
                       "mean_wind_cosine":float(np.mean(cos)),
                       "decision":"CONTINUOUS_2D_FILAMENT_SURVIVES" if all(x>.5 for x in cos) else "CONTINUOUS_2D_FILAMENT_INSUFFICIENT"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
