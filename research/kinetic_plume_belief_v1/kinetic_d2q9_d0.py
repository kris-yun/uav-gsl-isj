#!/usr/bin/env python3
"""Stable D2Q9 kinetic plume D0 screen.

Scientific question:
Does retaining a mesoscopic directional population f_i, rather than only scalar
concentration C=sum_i f_i, recover the missing wind-intervention geometry?

This is a House02 development-only screen. No ROS/PMFS/closed loop.
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
DIRS=((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))
OPPOSITE=(0,2,1,4,3,8,7,6,5)

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def load_py(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def shift_zero(x,di,dj):
    out=torch.zeros_like(x)
    h,w=x.shape[-2:]
    rs=max(0,-di); re=min(h,h-di)
    cs=max(0,-dj); ce=min(w,w-dj)
    rd=rs+di; rde=re+di
    cd=cs+dj; cde=ce+dj
    if re>rs and ce>cs:
        out[...,rd:rde,cd:cde]=x[...,rs:re,cs:ce]
    return out

def neighbour(x,di,dj):
    return shift_zero(x,-di,-dj)

class D2Q9KineticPlume(nn.Module):
    """Positive directional-population transport with exact first-moment matching.

    The 1-D three-state marginal is parameterized so that its mean equals the
    physical Courant number m exactly while a learned diffusion floor controls
    unresolved directional spread. The 2-D D2Q9 equilibrium is the product of
    row/column marginals.

    Collision is convex BGK relaxation, preserving positivity. Streaming is
    exact one-cell lattice transport. Obstacle hits use local bounce-back.
    """
    def __init__(self):
        super().__init__()
        self.omega_raw=nn.Parameter(torch.tensor(0.0))      # relaxation
        self.nu_raw=nn.Parameter(torch.tensor(-3.0))        # diffusion floor
        self.source_raw=nn.Parameter(torch.tensor(0.0))
        self.sink_raw=nn.Parameter(torch.tensor(-4.0))

    def omega(self):
        return 0.05+0.95*torch.sigmoid(self.omega_raw)

    def nu(self):
        return 0.25*torch.sigmoid(self.nu_raw)

    def source_strength(self):
        return F.softplus(self.source_raw)

    def sink_rate(self):
        return 0.02*torch.sigmoid(self.sink_raw)

    def initial_state(self,source):
        b,_,h,w=source.shape
        return torch.zeros(b,9,h,w,device=source.device,dtype=source.dtype)

    def concentration(self,f):
        return f.sum(dim=1,keepdim=True)

    def _p3(self,m):
        # m must lie in [-1,1]. q >= |m| guarantees nonnegative probabilities.
        a=m.abs().clamp(max=0.999)
        q=a+self.nu()*(1.0-a)
        p_plus=0.5*(q+m)
        p_minus=0.5*(q-m)
        p_zero=1.0-q
        return p_minus,p_zero,p_plus

    def equilibrium_weights(self,wind_xy):
        mr=(wind_xy[:,0:1]*DT/DX).clamp(-0.999,0.999)
        mc=(wind_xy[:,1:2]*DT/DX).clamp(-0.999,0.999)
        rminus,rzero,rplus=self._p3(mr)
        cminus,czero,cplus=self._p3(mc)
        table={
          (0,0):rzero*czero,
          (-1,0):rminus*czero,(1,0):rplus*czero,
          (0,-1):rzero*cminus,(0,1):rzero*cplus,
          (-1,-1):rminus*cminus,(-1,1):rminus*cplus,
          (1,-1):rplus*cminus,(1,1):rplus*cplus,
        }
        return torch.cat([table[d] for d in DIRS],dim=1)

    def collide(self,f,wind_xy,free):
        c=self.concentration(f)
        w=self.equilibrium_weights(wind_xy)
        feq=c*w
        om=self.omega()
        return ((1.0-om)*f+om*feq)*free

    def stream_bounce(self,f,free):
        if free.shape[0]==1 and f.shape[0]>1:
            free=free.expand(f.shape[0],-1,-1,-1)
        b,_,h,w=f.shape
        ones=torch.ones_like(free)
        out=torch.zeros_like(f)
        for k,(di,dj) in enumerate(DIRS):
            amount=f[:,k:k+1]*free
            if di==0 and dj==0:
                out[:,k:k+1]+=amount
                continue
            dest_free=neighbour(free,di,dj)
            dest_inside=neighbour(ones,di,dj)
            valid=(dest_free>0.5)&(dest_inside>0.5)
            blocked=(dest_inside>0.5)&(~valid)
            # Valid mass streams to destination in same population.
            out[:,k:k+1]+=shift_zero(amount*valid.to(amount.dtype),di,dj)
            # Obstacle collision: bounce to opposite direction at source cell.
            out[:,OPPOSITE[k]:OPPOSITE[k]+1]+=amount*blocked.to(amount.dtype)
            # out-of-domain mass is deliberate outflow.
        return out*free

    def step(self,f,source_map,wind_xy,free):
        if free.shape[0]==1 and f.shape[0]>1:
            free=free.expand(f.shape[0],-1,-1,-1)
        f=self.collide(f,wind_xy,free)
        f=self.stream_bounce(f,free)
        # Isotropic-in-kinetic-space source injection conditioned on current wind.
        sw=self.equilibrium_weights(wind_xy)
        f=f+self.source_strength()*source_map*sw
        f=f*torch.exp(-self.sink_rate()*DT)
        if not torch.isfinite(f).all():
            raise FloatingPointError("non-finite D2Q9 state")
        return f*free

def evolve(model,source,schedule,free,use_checkpoint=True):
    record_steps=[int(round(t/DT)) for t in (50,75,100,125,150,175,200,225,250,275)]
    state=model.initial_state(source)
    outs=[]; start=0
    mask=free.expand(source.shape[0],-1,-1,-1)
    def seg(s,src,w,msk):
        z=s
        for i in range(w.shape[0]):
            z=model.step(z,src,w[i],msk)
        return z
    for end in record_steps:
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
    return {"pred_norm":pn,"true_norm":yn,
            "amplitude_ratio":pn/yn if yn>0 else float("nan"),
            "cosine":cos}

def centroid(field,free):
    a=field[0,:,0].clamp_min(0).double()*free[0,0].double()[None]
    rr,cc=torch.meshgrid(torch.arange(a.shape[-2],dtype=torch.double),
                         torch.arange(a.shape[-1],dtype=torch.double),indexing="ij")
    pts=[]
    for z in a:
        mass=z.sum()
        pts.append((float((z*rr).sum()/mass),float((z*cc).sum()/mass))
                   if float(mass)>1e-12 else (float("nan"),float("nan")))
    return np.asarray(pts)

def centroid_shift(a,b,free):
    d=centroid(b,free)-centroid(a,free)
    good=np.isfinite(d).all(axis=1)
    if not good.any():
        return {"vector":[float("nan"),float("nan")],"norm":float("nan")}
    v=d[good].mean(axis=0)
    return {"vector":v.tolist(),"norm":float(np.linalg.norm(v))}

def source_superposition(model,source1,source2,schedule,free):
    with torch.no_grad():
        a,b=.37,.61
        lhs=evolve(model,a*source1+b*source2,schedule,free,False)[:,-1]
        rhs=a*evolve(model,source1,schedule,free,False)[:,-1]+b*evolve(model,source2,schedule,free,False)[:,-1]
        return float((lhs-rhs).abs().max())

def smoke():
    m=D2Q9KineticPlume()
    with torch.no_grad():
        wind=torch.tensor([[[[0.6]],[[0.0]]]]) # wrong shape guard below
    # exact first moment test on random Courant-compatible winds
    wind=torch.zeros(4,2,3,5)
    wind[:,0]=torch.tensor([0.0,0.2,-0.4,0.7])[:,None,None]
    wind[:,1]=torch.tensor([0.1,-0.3,0.4,-0.5])[:,None,None]
    w=m.equilibrium_weights(wind)
    er=torch.tensor([d[0] for d in DIRS],dtype=w.dtype).reshape(1,9,1,1)
    ec=torch.tensor([d[1] for d in DIRS],dtype=w.dtype).reshape(1,9,1,1)
    mr=(w*er).sum(1,keepdim=True)
    mc=(w*ec).sum(1,keepdim=True)
    tr=wind[:,0:1]*DT/DX; tc=wind[:,1:2]*DT/DX
    prob_err=float((w.sum(1,keepdim=True)-1).abs().max())
    moment_err=max(float((mr-tr).abs().max()),float((mc-tc).abs().max()))

    # wall bounce test
    f=torch.zeros(1,9,11,11)
    free=torch.ones(1,1,11,11); free[:,:,:,6]=0
    f[:,4,5,5]=1.0 # moving +col toward wall
    out=m.stream_bounce(f,free)
    wall_cross=float(out[:,:,:,7:].sum())
    bounced=float(out[:,3,5,5])
    return {"probability_sum_max_abs_error":prob_err,
            "first_moment_max_abs_error":moment_err,
            "wall_cross_mass":wall_cross,"bounced_mass":bounced,
            "pass":prob_err<1e-6 and moment_err<1e-6 and wall_cross<1e-8 and bounced>0.999}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()

    sm=smoke()
    print("SMOKE",json.dumps(sm))
    if not sm["pass"]:
        raise RuntimeError("D2Q9 smoke failed")

    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)
    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    sources,free=d0.load_static_context(bank)
    winds,_=d0.load_dynamic_winds(args.dynamic_wind)
    device=torch.device("cpu"); free=free.to(device)

    train_src=torch.cat([sources[s] for s,_ in TRAIN_PAIRS],0).to(device)
    train_sched=d0.build_batch_schedule(mm,winds,TRAIN_PAIRS,device)
    train_targets=[]
    for sid,wid in TRAIN_PAIRS:
        train_targets.append(torch.stack([d0.target(bank,sid,wid,ps) for ps in PLUME_SEEDS],0))
    train_targets=torch.stack(train_targets,0).to(device)

    args.out.mkdir(parents=True,exist_ok=False)
    manifest={
      "mode":"D2Q9_KINETIC_TRAIN",
      "holdout_unopened":["S2_W2_A","S2_W2_B"],
      "train_pairs":[f"{s}_{w}" for s,w in TRAIN_PAIRS],
      "train_seeds":list(TRAIN_SEEDS),"epochs":EPOCHS,"lr":LR,
      "dt_s":DT,"cell_m":DX,"smoke":sm,"fits":{}
    }
    for seed in TRAIN_SEEDS:
        torch.manual_seed(seed)
        model=D2Q9KineticPlume().to(device)
        with torch.no_grad():
            model.omega_raw.add_(0.02*torch.randn_like(model.omega_raw))
            model.nu_raw.add_(0.02*torch.randn_like(model.nu_raw))
            model.source_raw.add_(0.02*torch.randn_like(model.source_raw))
        opt=torch.optim.Adam(model.parameters(),lr=LR)
        losses=[]
        for ep in range(EPOCHS):
            model.train()
            p=evolve(model,train_src,train_sched,free,True)
            plog=torch.log1p(p.clamp_min(0))[:,None]
            fmask=free[None,None]
            diff=(plog-train_targets)**2
            loss=(diff*fmask).sum()/(fmask.sum()*diff.shape[0]*diff.shape[1]*diff.shape[2])
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss seed={seed} epoch={ep+1}")
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
            losses.append(float(loss.detach()))
            print(f"seed={seed} epoch={ep+1}/{EPOCHS} loss={losses[-1]:.8g}",flush=True)
        cp=args.out/f"d2q9_seed{seed}.pt"; torch.save(model.state_dict(),cp)
        manifest["fits"][str(seed)]={
          "loss_first":losses[0],"loss_last":losses[-1],
          "checkpoint_sha256":sha256(cp),
          "omega":float(model.omega().detach()),
          "directional_persistence_1_minus_omega":float((1-model.omega()).detach()),
          "nu":float(model.nu().detach()),
          "source_strength":float(model.source_strength().detach()),
          "sink_rate":float(model.sink_rate().detach()),
        }
    (args.out/"train_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")

    for seed in TRAIN_SEEDS:
        cp=args.out/f"d2q9_seed{seed}.pt"
        if sha256(cp)!=manifest["fits"][str(seed)]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash drift")

    eval_src=torch.cat([sources[s] for s,_ in EVAL_PAIRS],0).to(device)
    eval_sched=d0.build_batch_schedule(mm,winds,EVAL_PAIRS,device)
    truth={(s,w):{ps:d0.target(bank,s,w,ps).to(device)[None] for ps in PLUME_SEEDS} for s,w in EVAL_PAIRS}

    result={"mode":"D2Q9_KINETIC_EVALUATE","fits":{},"decision":None}
    all_pass=True
    for seed in TRAIN_SEEDS:
        model=D2Q9KineticPlume().to(device)
        model.load_state_dict(torch.load(args.out/f"d2q9_seed{seed}.pt",map_location="cpu",weights_only=True)); model.eval()
        with torch.no_grad():
            p=evolve(model,eval_src,eval_sched,free,False)
            plog=torch.log1p(p.clamp_min(0))
            dw=plog[0:1]-plog[1:2]; ds=plog[0:1]-plog[2:3]
            full_norm=float(torch.linalg.vector_norm(flatten_free(dw,free)))
            zero_sched=torch.zeros_like(eval_sched)
            p0=evolve(model,eval_src,zero_sched,free,False)
            zlog=torch.log1p(p0.clamp_min(0))
            abl_norm=float(torch.linalg.vector_norm(flatten_free(zlog[0:1]-zlog[1:2],free)))
            s_w2=d0.build_batch_schedule(mm,winds,(("S1","W2"),),device)
            sup=source_superposition(model,sources["S1"].to(device),sources["S2"].to(device),s_w2,free)
        sr={
          "omega":float(model.omega()),"directional_persistence_1_minus_omega":float(1-model.omega()),
          "nu":float(model.nu()),
          "wind_ablation_norm_ratio":abl_norm/full_norm if full_norm>0 else float("inf"),
          "superposition_max_abs_error":sup,"plumes":{}
        }
        seed_pass=sr["wind_ablation_norm_ratio"]<=0.5 and sup<1e-4
        for ps in PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]; y12=truth[("S1","W2")][ps]
            wm=delta_metrics(dw,y22-y21,free); smet=delta_metrics(ds,y22-y12,free)
            true_ws=wm["true_norm"]/smet["true_norm"]; pred_ws=wm["pred_norm"]/smet["pred_norm"]
            rws=pred_ws/true_ws
            tc=centroid_shift(y21,y22,free); pc=centroid_shift(plog[1:2],plog[0:1],free)
            cr=pc["norm"]/tc["norm"]
            mse=free_mse(plog[0:1],y22,free)
            gates={
              "wind_amplitude":0.5<=wm["amplitude_ratio"]<=1.5,
              "wind_cosine":wm["cosine"]>0.5,
              "centroid_ratio":cr>0.5,
              "relative_wind_source":rws>0.5,
              "source_amplitude":smet["amplitude_ratio"]>0.5,
              "beats_frozen_monolithic_mse":mse<MONO_MSE[seed][ps],
            }
            pp=all(gates.values()); seed_pass &= pp
            sr["plumes"][ps]={
              "field_mse":mse,"wind_delta":wm,"source_delta":smet,
              "relative_wind_to_source":rws,"centroid_shift_magnitude_ratio":cr,
              "gates":gates,"pass":pp
            }
        sr["pass"]=bool(seed_pass)
        result["fits"][str(seed)]=sr
        all_pass &= seed_pass

    result["decision"]="D2Q9_KINETIC_STATE_SURVIVES_D0" if all_pass else "D2Q9_KINETIC_STATE_NO_GO"
    (args.out/"d2q9_result.json").write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))

if __name__=="__main__":
    main()
