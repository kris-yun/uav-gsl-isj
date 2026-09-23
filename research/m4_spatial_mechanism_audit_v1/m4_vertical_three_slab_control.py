#!/usr/bin/env python3
"""Frozen Tier-1 vertical-transport control for M4-v3.

No learned 3-D module. Keeps M4-v3 horizontal transport/closure and adds a
three-slab conservative exchange driven by the already-exported GADEN Wz at
z=0.2 m. Original grid dz=0.1 m from context_metadata.json. Source injects only
into the middle observation slab. The same x/y field and 2-D obstacle mask are
used in all three slabs; this is intentionally a cheap anti-overengineering
control, not a high-fidelity 3-D simulator.

Train and evaluate are separated exactly as in M4-v3 D0: S2-W2 is never read
during train, and evaluate opens it only after checkpoint hash validation.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, platform, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint

TRAIN_PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"))
PLUME_SEEDS=("A","B")
TRAIN_SEEDS=(1729,2718)
TARGET_TIMES_S=(50,75,100,125,150,175,200,225,250,275)
PHYSICS_DT_S=0.1
WIND_DT_S=1.0
LOOP_FROM=1
LOOP_TO=10
EPOCHS=20
LR=1e-2
DZ_M=0.1
MONO_MSE={
    1729:{"A":0.442161500453949,"B":0.4313753545284271},
    2718:{"A":0.31033462285995483,"B":0.2978709042072296},
}

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def load_py(p:Path,name:str):
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def load_static(bank:Path):
    g=bank/"geometry"; src={}
    for sid in ("S1","S2"):
        a=np.load(g/f"source_map_{sid}.npy",allow_pickle=False).astype(np.float32)
        src[sid]=F.max_pool2d(torch.from_numpy(a)[None,None],2,ceil_mode=True)
    mask=np.load(g/"obstacle_mask_z0p20.npy",allow_pickle=False)
    free0=torch.from_numpy((mask==0).astype(np.float32))[None,None]
    free=1.0-F.max_pool2d(1.0-free0,2,ceil_mode=True)
    meta=json.loads((g/"context_metadata.json").read_text())
    if abs(float(meta["cell_m"])-DZ_M)>1e-12 or int(meta["sensor_z_index"])!=12:
        raise ValueError("vertical grid provenance drift")
    return src,free,meta

def load_wind3(dynamic:Path):
    manifest=json.loads((dynamic/"wind_sequence_manifest.json").read_text())
    out={}
    for wid in ("W1","W2"):
        p=dynamic/f"wind_{wid}_sequence_z0p20.npy"
        if sha256(p)!=manifest[wid]["export_sha256"]: raise ValueError("wind hash drift")
        a=np.load(p,allow_pickle=False).astype(np.float32)
        if a.shape!=(11,83,119,3): raise ValueError("wind shape drift")
        out[wid]=F.avg_pool2d(torch.from_numpy(a).permute(0,3,1,2),2,ceil_mode=True)
    return out,manifest

def target(bank,sid,wid,ps):
    a=np.load(bank/"realizations"/f"{sid}_{wid}_{ps}"/"concentration.npy",allow_pickle=False)
    y=torch.from_numpy(np.log1p(a).astype(np.float32))[:,None]
    return F.avg_pool2d(y,2,ceil_mode=True)

def record_steps():
    return [int(round(t/PHYSICS_DT_S)) for t in TARGET_TIMES_S]

def schedule(mm,winds,pairs,device):
    ids=mm.gaden_wind_index_schedule(
        record_steps()[-1],PHYSICS_DT_S,WIND_DT_S,11,LOOP_FROM,LOOP_TO)
    idx=torch.as_tensor(ids,dtype=torch.long)
    return torch.stack([winds[w][idx] for _,w in pairs],dim=1).to(device)

class ThreeSlabVerticalTransport(nn.Module):
    def __init__(self,base_module,cell_m=0.2):
        super().__init__()
        self.cell_m=float(cell_m)
        self.horizontal=base_module.SourceAgnosticLinearTransport()

    def vertical_exchange(self,x,wz):
        # x [B,3,H,W], wz [B,1,H,W].
        # Courant fraction is physical, fixed and clipped for positivity.
        frac=(wz.abs()*PHYSICS_DT_S/DZ_M).clamp(0.0,1.0)
        up=(wz>0).to(x.dtype)
        dn=(wz<0).to(x.dtype)
        stay=1.0-frac
        y=x*stay
        move=x*frac
        # positive z: lower->middle, middle->upper, upper leaves domain
        y[:,1:2] += move[:,0:1]*up
        y[:,2:3] += move[:,1:2]*up
        # negative z: upper->middle, middle->lower, lower leaves domain
        y[:,1:2] += move[:,2:3]*dn
        y[:,0:1] += move[:,1:2]*dn
        return y

    def forward(self,state,wind3,free):
        b=state.shape[0]
        mask=free.expand(b,-1,-1,-1)
        layers=[]
        xy=wind3[:,:2]
        for k in range(3):
            layers.append(self.horizontal(
                state[:,k:k+1],xy,mask,PHYSICS_DT_S,self.cell_m))
        x=torch.cat(layers,dim=1)
        x=self.vertical_exchange(x,wind3[:,2:3])
        return x*mask

class Model(nn.Module):
    def __init__(self,base_module,cell_m=0.2):
        super().__init__()
        self.transport=ThreeSlabVerticalTransport(base_module,cell_m)
        self.source_strength_raw=nn.Parameter(torch.tensor(0.0))
    def source_strength(self): return F.softplus(self.source_strength_raw)
    def init_state(self,source):
        return torch.zeros(source.shape[0],3,*source.shape[-2:],dtype=source.dtype,device=source.device)
    def step(self,state,source,wind3,free):
        x=self.transport(state,wind3,free)
        x[:,1:2] = x[:,1:2] + self.source_strength()*source
        return x
    def observe(self,state):
        return state[:,1:2]

def evolve(model,source,sch,free,use_checkpoint=True):
    steps=record_steps(); state=model.init_state(source); out=[]; start=0
    mask=free.expand(source.shape[0],-1,-1,-1)
    def seg(s,src,w,m):
        z=s
        for i in range(w.shape[0]): z=model.step(z,src,w[i],m)
        return z
    for end in steps:
        w=sch[start:end]
        if use_checkpoint and model.training:
            state=checkpoint(seg,state,source,w,mask,use_reentrant=False)
        else:
            state=seg(state,source,w,mask)
        out.append(model.observe(state))
        start=end
    return torch.stack(out,dim=1)

def free_mse(p,y,free):
    f=free[:,None]
    return float((((p-y)**2)*f).sum()/(f.sum()*p.shape[1]))

def flatten(x,free):
    m=free[0,0]>0.5
    return x[:,:,0][:,:,m].reshape(-1).double()

def delta_metrics(p,y,free):
    a=flatten(p,free); b=flatten(y,free)
    na=float(torch.linalg.vector_norm(a)); nb=float(torch.linalg.vector_norm(b))
    co=float(torch.dot(a,b)/(torch.linalg.vector_norm(a)*torch.linalg.vector_norm(b))) if na>0 and nb>0 else float("nan")
    return {"pred_norm":na,"true_norm":nb,"amplitude_ratio":na/nb if nb>0 else float("nan"),"cosine":co}

def centroid(field,free):
    a=field[0,:,0].clamp_min(0).double()*free[0,0].double()[None]
    rr,cc=torch.meshgrid(torch.arange(a.shape[-2],dtype=torch.double),
                         torch.arange(a.shape[-1],dtype=torch.double),indexing="ij")
    pts=[]
    for z in a:
        q=z.sum()
        pts.append((float((z*rr).sum()/q),float((z*cc).sum()/q)) if float(q)>1e-12 else (np.nan,np.nan))
    return np.asarray(pts)

def centroid_shift(a,b,free):
    d=centroid(b,free)-centroid(a,free); good=np.isfinite(d).all(1); v=d[good].mean(0)
    return {"vector":v.tolist(),"norm":float(np.linalg.norm(v))}

def superposition(model,s1,s2,sch,free):
    with torch.no_grad():
        a=.37; b=.61
        lhs=evolve(model,a*s1+b*s2,sch,free,False)[:,-1]
        rhs=a*evolve(model,s1,sch,free,False)[:,-1]+b*evolve(model,s2,sch,free,False)[:,-1]
    return float((lhs-rhs).abs().max())

def train(args):
    torch.use_deterministic_algorithms(True); torch.set_num_threads(args.cpu_threads)
    root=args.repo_root
    base=load_py(root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py","base")
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dynamic=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    src,free,meta=load_static(bank); winds,wmanifest=load_wind3(dynamic)
    device=torch.device("cpu"); source=torch.cat([src[s] for s,_ in TRAIN_PAIRS]).to(device); free=free.to(device)
    sch=schedule(base,winds,TRAIN_PAIRS,device)
    targets=torch.stack([torch.stack([target(bank,s,w,p) for p in PLUME_SEEDS]) for s,w in TRAIN_PAIRS]).to(device)
    args.out.mkdir(parents=True,exist_ok=False)
    man={"mode":"train","holdout_unopened":["S2_W2_A","S2_W2_B"],"train_pairs":["S1_W1","S2_W1","S1_W2"],
         "train_seeds":list(TRAIN_SEEDS),"epochs":EPOCHS,"lr":LR,"vertical_dz_m":DZ_M,
         "sensor_z_index":meta["sensor_z_index"],"sensor_z_m":meta["sensor_z_m"],"fits":{}}
    for seed in TRAIN_SEEDS:
        torch.manual_seed(seed); model=Model(base).to(device)
        with torch.no_grad():
            model.transport.horizontal.closure.logits.weight.normal_(0,0.01)
            model.transport.horizontal.closure.logits.bias[:]=torch.tensor([4.,0.,0.,0.,0.])
            model.transport.horizontal.closure.logits.bias.add_(.01*torch.randn_like(model.transport.horizontal.closure.logits.bias))
            model.transport.horizontal.loss_raw.fill_(-8.0); model.source_strength_raw.fill_(0.0)
        opt=torch.optim.Adam(model.parameters(),lr=LR)
        losses=[]
        for ep in range(EPOCHS):
            model.train(); pred=evolve(model,source,sch,free,True)
            plog=torch.log1p(pred.clamp_min(0))[:,None]
            diff=(plog-targets)**2; f=free[None,None]
            loss=(diff*f).sum()/(f.sum()*diff.shape[0]*diff.shape[1]*diff.shape[2])
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
            losses.append(float(loss.detach()))
            print(f"seed={seed} epoch={ep+1}/{EPOCHS} loss={losses[-1]:.8g}",flush=True)
        cp=args.out/f"vertical_seed{seed}.pt"; torch.save(model.state_dict(),cp)
        man["fits"][str(seed)]={"loss_first":losses[0],"loss_last":losses[-1],"checkpoint_sha256":sha256(cp)}
    (args.out/"train_manifest.json").write_text(json.dumps(man,indent=2)+"\n")
    print(json.dumps(man,indent=2))

def evaluate(args):
    torch.use_deterministic_algorithms(True); torch.set_num_threads(args.cpu_threads)
    root=args.repo_root
    base=load_py(root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py","base")
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dynamic=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    src,free,_=load_static(bank); winds,_=load_wind3(dynamic)
    man=json.loads((args.out/"train_manifest.json").read_text())
    if man["holdout_unopened"]!=["S2_W2_A","S2_W2_B"]: raise ValueError("holdout drift")
    cps={}
    for seed in TRAIN_SEEDS:
        p=args.out/f"vertical_seed{seed}.pt"
        if sha256(p)!=man["fits"][str(seed)]["checkpoint_sha256"]: raise ValueError("checkpoint drift")
        cps[seed]=p
    pairs=(("S2","W2"),("S2","W1"),("S1","W2"))
    source=torch.cat([src[s] for s,_ in pairs]); sch=schedule(base,winds,pairs,torch.device("cpu"))
    # Only after checkpoint validation.
    truth={(s,w):{p:target(bank,s,w,p)[None] for p in PLUME_SEEDS} for s,w in pairs}
    out={"mode":"evaluate","control":"fixed_three_slab_wz_exchange","fits":{}}
    allpass=True
    for seed in TRAIN_SEEDS:
        model=Model(base); model.load_state_dict(torch.load(cps[seed],map_location="cpu",weights_only=True)); model.eval()
        with torch.no_grad():
            pred=evolve(model,source,sch,free,False); plog=torch.log1p(pred.clamp_min(0))
        dw=plog[0:1]-plog[1:2]; ds=plog[0:1]-plog[2:3]
        # ablate vertical exchange by zeroing z in schedule
        zsch=sch.clone(); zsch[:,:,2]=0
        with torch.no_grad(): ab=torch.log1p(evolve(model,source,zsch,free,False).clamp_min(0))
        abl_dw=ab[0:1]-ab[1:2]
        norm=float(torch.linalg.vector_norm(flatten(dw,free))); an=float(torch.linalg.vector_norm(flatten(abl_dw,free)))
        one_sch=schedule(base,winds,(("S1","W2"),),torch.device("cpu"))
        sup=superposition(model,src["S1"],src["S2"],one_sch,free)
        sr={"vertical_ablation_wind_norm_ratio":an/norm if norm>0 else float("inf"),
            "superposition_max_abs_error":sup,"plumes":{}}
        seedpass=sup<1e-5
        for ps in PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]; y12=truth[("S1","W2")][ps]
            wm=delta_metrics(dw,y22-y21,free); sm=delta_metrics(ds,y22-y12,free)
            tws=wm["true_norm"]/sm["true_norm"]; pws=wm["pred_norm"]/sm["pred_norm"]; rws=pws/tws
            tc=centroid_shift(y21,y22,free); pc=centroid_shift(plog[1:2],plog[0:1],free)
            cr=pc["norm"]/tc["norm"]; mse=free_mse(plog[0:1],y22,free)
            gates={"wind_amplitude":.5<=wm["amplitude_ratio"]<=1.5,"wind_cosine":wm["cosine"]>.5,
                   "centroid_ratio":cr>.5,"relative_wind_source":rws>.5,
                   "source_amplitude":sm["amplitude_ratio"]>.5,
                   "beats_frozen_monolithic_mse":mse<MONO_MSE[seed][ps]}
            pp=all(gates.values()); seedpass &= pp
            sr["plumes"][ps]={"field_mse":mse,"wind_delta":wm,"source_delta":sm,
                              "relative_wind_to_source":rws,"centroid_shift_magnitude_ratio":cr,
                              "gates":gates,"pass":pp}
        sr["pass"]=seedpass; out["fits"][str(seed)]=sr; allpass &= seedpass
    out["decision"]="VERTICAL_CONTROL_PASSES_D0" if allpass else "VERTICAL_CONTROL_FAILS_D0"
    (args.out/"vertical_result.json").write_text(json.dumps(out,indent=2,allow_nan=True)+"\n")
    print(json.dumps(out,indent=2,allow_nan=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("train","evaluate"))
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--cpu-threads",type=int,default=4)
    a=ap.parse_args()
    train(a) if a.mode=="train" else evaluate(a)
if __name__=="__main__": main()
