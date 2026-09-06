from __future__ import annotations

import argparse, json, math, random, sys
from pathlib import Path
import torch
import torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from common.trace_io import load_manifest, load_episode
from m1_picr.model import PICRModel


def candidate_pool(specs, radius=1.0):
    base=sorted({tuple(map(float,s.source_xy)) for s in specs})
    offsets=((0,0),(radius,0),(-radius,0),(0,radius),(0,-radius),(radius,radius),(radius,-radius),(-radius,radius),(-radius,-radius))
    pool=[]
    for s in base:
        for dx,dy in offsets:
            p=(round(s[0]+dx,6),round(s[1]+dy,6))
            if p not in pool: pool.append(p)
    return pool


def history_tensor(ep, max_steps=256):
    idx=list(range(max(0,len(ep.time)-max_steps),len(ep.time)))
    rows=[]
    for i in idx:
        rows.append([math.log1p(ep.gas[i]),ep.sensor_state[i],ep.wind_u[i],ep.wind_v[i],ep.pose_x[i],ep.pose_y[i],ep.time[i],ep.measuring[i]])
    return torch.tensor(rows,dtype=torch.float32)


def batch_examples(episodes,pool,device):
    hs=[history_tensor(e) for e in episodes]
    T=max(x.shape[0] for x in hs)
    H=torch.zeros(len(hs),T,8,device=device); V=torch.zeros(len(hs),T,dtype=torch.bool,device=device)
    targets=[]
    for b,(e,h) in enumerate(zip(episodes,hs)):
        H[b,-h.shape[0]:]=h.to(device); V[b,-h.shape[0]:]=True
        targets.append(pool.index(tuple(map(float,e.spec.source_xy))))
    C=torch.tensor(pool,dtype=torch.float32,device=device)[None,:,:].expand(len(hs),-1,-1)
    return H,C,V,torch.tensor(targets,dtype=torch.long,device=device)


def train_model(episodes,pool,causal:bool,steps:int,seed:int,device):
    torch.manual_seed(seed); random.seed(seed)
    model=PICRModel(d_model=48,nhead=4,layers=2,z_source_dim=24,z_nuisance_dim=16).to(device)
    opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4)
    by_source={}
    for e in episodes: by_source.setdefault(tuple(e.spec.source_xy),[]).append(e)
    for _ in range(steps):
        batch=random.sample(episodes,min(len(episodes),8))
        H,C,V,y=batch_examples(batch,pool,device)
        out=model(H,C,V)
        loss=F.cross_entropy(out.source_logits,y)
        if causal:
            keys=[k for k,v in by_source.items() if len(v)>=2]
            if keys:
                k=random.choice(keys); a,b=random.sample(by_source[k],2)
                H2,C2,V2,_=batch_examples([a,b],pool,device); po=model(H2,C2,V2)
                loss=loss+0.25*(po.source_representation[0]-po.source_representation[1]).pow(2).mean()
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5.0); opt.step()
    return model

@torch.no_grad()
def evaluate(model,episodes,pool,device):
    H,C,V,y=batch_examples(episodes,pool,device); out=model(H,C,V)
    ce=float(F.cross_entropy(out.source_logits,y)); pred=out.source_posterior.argmax(-1)
    acc=float((pred==y).float().mean())
    xy=torch.tensor(pool,dtype=torch.float32,device=device); pxy=xy[pred]; txy=xy[y]
    err=float(torch.linalg.vector_norm(pxy-txy,dim=-1).mean())
    zs=out.source_representation.cpu(); same=[]; diff=[]
    for i in range(len(episodes)):
        for j in range(i+1,len(episodes)):
            d=float(torch.linalg.vector_norm(zs[i]-zs[j]))
            (same if episodes[i].spec.source_xy==episodes[j].spec.source_xy else diff).append(d)
    return {"cross_entropy":ce,"top1_accuracy":acc,"mean_source_error_m":err,"same_source_z_distance":sum(same)/len(same) if same else None,"different_source_z_distance":sum(diff)/len(diff) if diff else None}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--steps",type=int,default=400); ap.add_argument("--seed",type=int,default=7)
    args=ap.parse_args(); specs=load_manifest(args.manifest); episodes=[load_episode(s) for s in specs]
    if len(episodes)<3: raise RuntimeError("CSTAR_M1_NEED_AT_LEAST_3_EPISODES")
    pool=candidate_pool(specs); device=torch.device("cpu")
    houses=sorted({e.spec.house for e in episodes if e.spec.house}); folds=[]
    for held in houses or [""]:
        tr=[e for e in episodes if not held or e.spec.house!=held]; te=[e for e in episodes if not held or e.spec.house==held]
        if not tr or not te: continue
        causal=train_model(tr,pool,True,args.steps,args.seed,device); base=train_model(tr,pool,False,args.steps,args.seed,device)
        cm=evaluate(causal,te,pool,device); bm=evaluate(base,te,pool,device)
        folds.append({"heldout_house":held or "NONE","causal":cm,"unconstrained":bm,"directional":{"error_better":cm["mean_source_error_m"]<bm["mean_source_error_m"],"invariance_better":cm["same_source_z_distance"] is not None and bm["same_source_z_distance"] is not None and cm["same_source_z_distance"]<bm["same_source_z_distance"]}})
    report={"contract":"CSTAR_M1_OFFLINE_GATE_V1","episodes":len(episodes),"candidate_count":len(pool),"folds":folds,"limitations":["Spent closed-loop traces test route/transport nuisance invariance but do not by themselves provide controlled source-strength interventions unless such episodes are added to the manifest."]}
    report["pass"]=bool(folds) and all(f["directional"]["error_better"] and f["directional"]["invariance_better"] for f in folds)
    report["verdict"]="M1_OFFLINE_PASS" if report["pass"] else "M1_OFFLINE_NO_GO"
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(report["verdict"]); return 0 if report["pass"] else 2

if __name__=="__main__": raise SystemExit(main())
