#!/usr/bin/env python3
"""Kinetic-moment plume screening on House02 development data.

Main hypothesis under test:
A scalar concentration field is an insufficient Markov state. Retaining the
first transport moment J=(Jx,Jy) should recover wind-intervention geometry that
a concentration-only propagator misses.

No House01/03 data, no ROS/PMFS, no closed loop.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint

TRAIN_PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"))
EVAL_PAIRS=(("S2","W2"),("S2","W1"),("S1","W2"))
PLUME_SEEDS=("A","B")
TRAIN_SEEDS=(1729,2718)
DT=0.1
DX=0.2
EPOCHS=20
LR=2e-2
MONO_MSE={
    1729:{"A":0.442161500453949,"B":0.4313753545284271},
    2718:{"A":0.31033462285995483,"B":0.2978709042072296},
}

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def load_py(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def shift_zero(x,di,dj):
    """Move source value at (r,c) to (r+di,c+dj), zero padding."""
    out=torch.zeros_like(x)
    h,w=x.shape[-2:]
    rs=max(0,-di); re=min(h,h-di)
    cs=max(0,-dj); ce=min(w,w-dj)
    rd=rs+di; rde=re+di
    cd=cs+dj; cde=ce+dj
    if re>rs and ce>cs:
        out[...,rd:rde,cd:cde]=x[...,rs:re,cs:ce]
    return out

def neighbor(x,di,dj):
    """At each cell return x from neighbour (r+di,c+dj)."""
    return shift_zero(x,-di,-dj)

def masked_gradient(c,free,axis):
    if axis==0:
        cp=neighbor(c,1,0); cm=neighbor(c,-1,0)
        fp=neighbor(free,1,0); fm=neighbor(free,-1,0)
    else:
        cp=neighbor(c,0,1); cm=neighbor(c,0,-1)
        fp=neighbor(free,0,1); fm=neighbor(free,0,-1)
    cp=torch.where(fp>0.5,cp,c)
    cm=torch.where(fm>0.5,cm,c)
    return (cp-cm)/(2.0*DX)

class KineticMomentPropagator(nn.Module):
    """Three-state moment closure: concentration C plus resolved scalar flux J."""
    def __init__(self):
        super().__init__()
        self.tau_raw=nn.Parameter(torch.tensor(0.0))
        self.diff_raw=nn.Parameter(torch.tensor(-1.0))
        self.source_raw=nn.Parameter(torch.tensor(0.0))
        self.sink_raw=nn.Parameter(torch.tensor(-4.0))

    def tau(self):
        return 0.10+0.90*torch.sigmoid(self.tau_raw)

    def diffusivity(self):
        return 0.010*torch.sigmoid(self.diff_raw)

    def source_strength(self):
        return F.softplus(self.source_raw)

    def sink_rate(self):
        return 0.020*torch.sigmoid(self.sink_raw)

    def initial_state(self,source):
        b,_,h,w=source.shape
        return torch.zeros(b,3,h,w,device=source.device,dtype=source.dtype)

    def concentration(self,state):
        return state[:,0:1]

    def step(self,state,source_map,wind_xy,free):
        if free.shape[0]==1 and state.shape[0]>1:
            free=free.expand(state.shape[0],-1,-1,-1)
        c=state[:,0:1]*free
        jr=state[:,1:2]*free
        jc=state[:,2:3]*free

        d=self.diffusivity()
        gr=masked_gradient(c,free,0)
        gc=masked_gradient(c,free,1)
        jeq_r=wind_xy[:,0:1]*c-d*gr
        jeq_c=wind_xy[:,1:2]*c-d*gc
        a=1.0-torch.exp(torch.tensor(-DT,device=c.device,dtype=c.dtype)/self.tau())
        jr=(1.0-a)*jr+a*jeq_r
        jc=(1.0-a)*jc+a*jeq_c

        frp=neighbor(free,1,0); fcp=neighbor(free,0,1)
        jr_dn=neighbor(jr,1,0); jc_rt=neighbor(jc,0,1)
        face_r_plus=0.5*(jr+jr_dn)*free*frp
        face_c_plus=0.5*(jc+jc_rt)*free*fcp
        face_r_minus=neighbor(face_r_plus,-1,0)
        face_c_minus=neighbor(face_c_plus,0,-1)
        div=(face_r_plus-face_r_minus+face_c_plus-face_c_minus)/DX

        cnext=c-DT*div
        cnext=F.relu(cnext)
        cnext=(cnext+self.source_strength()*source_map)*free
        retain=torch.exp(-self.sink_rate()*DT)
        cnext=cnext*retain
        jr=jr*retain*free
        jc=jc*retain*free
        return torch.cat((cnext,jr,jc),dim=1)

def build_schedule(d0,mm,winds,pairs,device):
    return d0.build_batch_schedule(mm,winds,pairs,device)

def evolve(model,source,schedule,free,use_checkpoint=True):
    d0_steps=[int(round(t/DT)) for t in (50,75,100,125,150,175,200,225,250,275)]
    state=model.initial_state(source)
    outs=[]; start=0
    mask=free.expand(source.shape[0],-1,-1,-1)
    def seg(s,src,w,msk):
        z=s
        for i in range(w.shape[0]):
            z=model.step(z,src,w[i],msk)
        return z
    for end in d0_steps:
        w=schedule[start:end]
        if use_checkpoint and model.training:
            state=checkpoint(seg,state,source,w,mask,use_reentrant=False)
        else:
            state=seg(state,source,w,mask)
        outs.append(model.concentration(state))
        start=end
    return torch.stack(outs,dim=1)

def free_mse(pred,y,free):
    f=free[:,None]
    return float((((pred-y)**2)*f).sum()/(f.sum()*pred.shape[1]))

def flatten_free(x,free):
    m=free[0,0]>0.5
    return x[:,:,0][:,:,m].reshape(-1).double()

def delta_metrics(p,y,free):
    pf=flatten_free(p,free); yf=flatten_free(y,free)
    pn=float(torch.linalg.vector_norm(pf)); yn=float(torch.linalg.vector_norm(yf))
    cos=float(torch.dot(pf,yf)/(torch.linalg.vector_norm(pf)*torch.linalg.vector_norm(yf))) if pn>0 and yn>0 else float("nan")
    return {"pred_norm":pn,"true_norm":yn,"amplitude_ratio":pn/yn if yn>0 else float("nan"),"cosine":cos}

def centroid(field,free):
    a=field[0,:,0].clamp_min(0).double()*free[0,0].double()[None]
    rr,cc=torch.meshgrid(torch.arange(a.shape[-2],dtype=torch.double),
                         torch.arange(a.shape[-1],dtype=torch.double),indexing="ij")
    pts=[]
    for z in a:
        mass=z.sum()
        pts.append((float((z*rr).sum()/mass),float((z*cc).sum()/mass)) if float(mass)>1e-12 else (float("nan"),float("nan")))
    return np.asarray(pts)

def centroid_shift(a,b,free):
    d=centroid(b,free)-centroid(a,free)
    good=np.isfinite(d).all(axis=1)
    v=d[good].mean(axis=0)
    return {"vector":v.tolist(),"norm":float(np.linalg.norm(v))}

def source_superposition(model,source1,source2,schedule,free):
    with torch.no_grad():
        a,b=.37,.61
        lhs=evolve(model,a*source1+b*source2,schedule,free,False)[:,-1]
        rhs=a*evolve(model,source1,schedule,free,False)[:,-1]+b*evolve(model,source2,schedule,free,False)[:,-1]
        return float((lhs-rhs).abs().max())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()

    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)
    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    sources,free=d0.load_static_context(bank)
    winds,wman=d0.load_dynamic_winds(args.dynamic_wind)
    device=torch.device("cpu"); free=free.to(device)

    train_src=torch.cat([sources[s] for s,_ in TRAIN_PAIRS],0).to(device)
    train_sched=build_schedule(d0,mm,winds,TRAIN_PAIRS,device)
    train_targets=[]
    for sid,wid in TRAIN_PAIRS:
        train_targets.append(torch.stack([d0.target(bank,sid,wid,ps) for ps in PLUME_SEEDS],0))
    train_targets=torch.stack(train_targets,0).to(device)

    args.out.mkdir(parents=True,exist_ok=False)
    manifest={
      "mode":"KINETIC_MOMENT_SCREEN","holdout_unopened":["S2_W2_A","S2_W2_B"],
      "train_pairs":[f"{s}_{w}" for s,w in TRAIN_PAIRS],
      "train_seeds":list(TRAIN_SEEDS),"epochs":EPOCHS,"lr":LR,"dt_s":DT,"cell_m":DX,
      "fits":{}
    }
    for seed in TRAIN_SEEDS:
        torch.manual_seed(seed)
        model=KineticMomentPropagator().to(device)
        with torch.no_grad():
            model.tau_raw.add_(0.05*torch.randn_like(model.tau_raw))
            model.diff_raw.add_(0.05*torch.randn_like(model.diff_raw))
            model.source_raw.add_(0.05*torch.randn_like(model.source_raw))
        opt=torch.optim.Adam(model.parameters(),lr=LR)
        losses=[]
        for ep in range(EPOCHS):
            model.train()
            p=evolve(model,train_src,train_sched,free,True)
            plog=torch.log1p(p.clamp_min(0))[:,None]
            f=free[None,None]
            diff=(plog-train_targets)**2
            loss=(diff*f).sum()/(f.sum()*diff.shape[0]*diff.shape[1]*diff.shape[2])
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
            losses.append(float(loss.detach()))
            print(f"seed={seed} epoch={ep+1}/{EPOCHS} loss={losses[-1]:.8g}",flush=True)
        cp=args.out/f"kinetic_seed{seed}.pt"; torch.save(model.state_dict(),cp)
        manifest["fits"][str(seed)]={
          "loss_first":losses[0],"loss_last":losses[-1],"checkpoint_sha256":sha256(cp),
          "tau_s":float(model.tau()),"diffusivity":float(model.diffusivity()),
          "source_strength":float(model.source_strength()),"sink_rate":float(model.sink_rate())
        }
    (args.out/"train_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")

    # Hash freeze before holdout first read.
    for seed in TRAIN_SEEDS:
        cp=args.out/f"kinetic_seed{seed}.pt"
        if sha256(cp)!=manifest["fits"][str(seed)]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash drift")

    eval_src=torch.cat([sources[s] for s,_ in EVAL_PAIRS],0).to(device)
    eval_sched=build_schedule(d0,mm,winds,EVAL_PAIRS,device)
    truth={(s,w):{ps:d0.target(bank,s,w,ps).to(device)[None] for ps in PLUME_SEEDS} for s,w in EVAL_PAIRS}

    result={"mode":"KINETIC_MOMENT_EVALUATE","fits":{},"decision":None}
    all_pass=True
    for seed in TRAIN_SEEDS:
        model=KineticMomentPropagator().to(device)
        model.load_state_dict(torch.load(args.out/f"kinetic_seed{seed}.pt",map_location="cpu",weights_only=True)); model.eval()
        with torch.no_grad():
            p=evolve(model,eval_src,eval_sched,free,False)
            plog=torch.log1p(p.clamp_min(0))
            dw=plog[0:1]-plog[1:2]; ds=plog[0:1]-plog[2:3]
            full_norm=float(torch.linalg.vector_norm(flatten_free(dw,free)))
            zero_sched=torch.zeros_like(eval_sched)
            p0=evolve(model,eval_src,zero_sched,free,False)
            zlog=torch.log1p(p0.clamp_min(0))
            abl_norm=float(torch.linalg.vector_norm(flatten_free(zlog[0:1]-zlog[1:2],free)))
            s_w2=build_schedule(d0,mm,winds,(("S1","W2"),),device)
            sup=source_superposition(model,sources["S1"].to(device),sources["S2"].to(device),s_w2,free)
        sr={"wind_ablation_norm_ratio":abl_norm/full_norm if full_norm>0 else float("inf"),
            "superposition_max_abs_error":sup,"plumes":{}}
        seed_pass=sr["wind_ablation_norm_ratio"]<=0.5
        for ps in PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]; y12=truth[("S1","W2")][ps]
            wm=delta_metrics(dw,y22-y21,free); sm=delta_metrics(ds,y22-y12,free)
            true_ws=wm["true_norm"]/sm["true_norm"]; pred_ws=wm["pred_norm"]/sm["pred_norm"]
            rws=pred_ws/true_ws
            tc=centroid_shift(y21,y22,free); pc=centroid_shift(plog[1:2],plog[0:1],free)
            cr=pc["norm"]/tc["norm"]
            mse=free_mse(plog[0:1],y22,free)
            gates={
              "wind_amplitude":0.5<=wm["amplitude_ratio"]<=1.5,
              "wind_cosine":wm["cosine"]>0.5,
              "centroid_ratio":cr>0.5,
              "relative_wind_source":rws>0.5,
              "source_amplitude":sm["amplitude_ratio"]>0.5,
              "beats_frozen_monolithic_mse":mse<MONO_MSE[seed][ps],
            }
            pp=all(gates.values()); seed_pass &= pp
            sr["plumes"][ps]={"field_mse":mse,"wind_delta":wm,"source_delta":sm,
                              "relative_wind_to_source":rws,"centroid_shift_magnitude_ratio":cr,
                              "gates":gates,"pass":pp}
        sr["pass"]=bool(seed_pass); result["fits"][str(seed)]=sr; all_pass &= seed_pass
    result["decision"]="KINETIC_STATE_SURVIVES_D0" if all_pass else "KINETIC_STATE_NO_GO"
    (args.out/"result.json").write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))

if __name__=="__main__":
    main()
