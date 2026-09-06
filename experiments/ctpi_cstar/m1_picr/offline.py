from __future__ import annotations
import argparse,json,math,random,sys
from pathlib import Path
import torch
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from common.trace_io import load_manifest,load_episode
from m1_picr.model import PICRModel


def history_tensor(ep,window_s=60.0):
    end=len(ep.time)
    if end == 0:
        raise ValueError("CSTAR_M1_EMPTY_EPISODE")
    cutoff=ep.time[-1]-float(window_s)
    lo=0
    while lo < end and ep.time[lo] < cutoff:
        lo += 1
    return torch.tensor([
        [
            math.log1p(ep.gas[i]),ep.gas_ema_aux[i],
            ep.wind_u[i],ep.wind_v[i],ep.pose_x[i],ep.pose_y[i],
            ep.time[i],ep.measuring[i],
        ]
        for i in range(lo,end)
    ],dtype=torch.float32)


def candidate_grid(ep,side=9,margin=2.0):
    # Premise replay only. Candidate domain is route-envelope-derived, not GT.
    xmin,xmax=min(ep.pose_x)-margin,max(ep.pose_x)+margin
    ymin,ymax=min(ep.pose_y)-margin,max(ep.pose_y)+margin
    xs=[xmin+(xmax-xmin)*i/(side-1) for i in range(side)]
    ys=[ymin+(ymax-ymin)*j/(side-1) for j in range(side)]
    return [(x,y) for y in ys for x in xs]


def batch_examples(episodes,device,window_s):
    hs=[history_tensor(e,window_s=window_s) for e in episodes]
    grids=[candidate_grid(e) for e in episodes]
    T=max(x.shape[0] for x in hs); N=len(grids[0])
    H=torch.zeros(len(hs),T,8,device=device)
    V=torch.zeros(len(hs),T,dtype=torch.bool,device=device)
    C=torch.zeros(len(hs),N,2,device=device);Y=[]
    for b,(e,h,g) in enumerate(zip(episodes,hs,grids)):
        # Right padding is mandatory: valid prefix followed by invalid suffix.
        H[b,:h.shape[0]]=h.to(device);V[b,:h.shape[0]]=True
        C[b]=torch.tensor(g,dtype=torch.float32,device=device)
        sx,sy=e.spec.source_xy
        Y.append(min(range(N),key=lambda k:(g[k][0]-sx)**2+(g[k][1]-sy)**2))
    return H,C,V,torch.tensor(Y,dtype=torch.long,device=device)


def train_model(episodes,causal,steps,seed,device,window_s):
    torch.manual_seed(seed);random.seed(seed)
    m=PICRModel(d_model=48,nhead=4,layers=2,z_source_dim=24,z_nuisance_dim=16).to(device)
    o=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-4)
    by={}
    for e in episodes:
        by.setdefault(tuple(e.spec.source_xy),[]).append(e)
    for _ in range(steps):
        batch=random.sample(episodes,min(8,len(episodes)))
        H,C,V,y=batch_examples(batch,device,window_s)
        out=m(H,C,V)
        loss=F.cross_entropy(out.source_logits,y)
        if causal:
            keys=[k for k,v in by.items() if len(v)>=2]
            if keys:
                a,b=random.sample(by[random.choice(keys)],2)
                H2,C2,V2,_=batch_examples([a,b],device,window_s)
                z=m(H2,C2,V2).source_representation
                loss=loss+0.25*(z[0]-z[1]).pow(2).mean()
        o.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);o.step()
    return m


@torch.no_grad()
def evaluate(m,episodes,device,window_s):
    H,C,V,y=batch_examples(episodes,device,window_s)
    out=m(H,C,V)
    if bool(out.abstain.any()):
        raise RuntimeError("CSTAR_M1_PREMISE_UNEXPECTED_ABSTAIN")
    pred=out.source_posterior.argmax(-1);b=torch.arange(len(episodes),device=device)
    pxy=C[b,pred]
    true=torch.tensor([e.spec.source_xy for e in episodes],dtype=torch.float32,device=device)
    err=torch.linalg.vector_norm(pxy-true,dim=-1);zs=out.source_representation.cpu();same=[]
    for i in range(len(episodes)):
        for j in range(i+1,len(episodes)):
            if episodes[i].spec.source_xy==episodes[j].spec.source_xy:
                same.append(float(torch.linalg.vector_norm(zs[i]-zs[j])))
    return {
        'cross_entropy':float(F.cross_entropy(out.source_logits,y)),
        'mean_source_error_m':float(err.mean()),
        'median_source_error_m':float(err.median()),
        'same_source_z_distance':sum(same)/len(same) if same else None,
        'candidate_domain_source':'executed_route_envelope_plus_fixed_margin_premise_only',
        'candidate_count':C.shape[1],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--steps',type=int,default=400)
    ap.add_argument('--seed',type=int,default=7)
    ap.add_argument('--history-window-s',type=float,default=60.0)
    a=ap.parse_args()
    eps=[load_episode(s) for s in load_manifest(a.manifest)]
    houses=sorted({e.spec.house for e in eps if e.spec.house});device=torch.device('cpu');folds=[]
    for held in houses or ['']:
        tr=[e for e in eps if not held or e.spec.house!=held]
        te=[e for e in eps if not held or e.spec.house==held]
        if not tr or not te:continue
        cm=evaluate(train_model(tr,True,a.steps,a.seed,device,a.history_window_s),te,device,a.history_window_s)
        bm=evaluate(train_model(tr,False,a.steps,a.seed,device,a.history_window_s),te,device,a.history_window_s)
        folds.append({
            'heldout_house':held or 'NONE','causal_regularized':cm,'unconstrained':bm,
            'directional':{
                'error_better':cm['mean_source_error_m']<bm['mean_source_error_m'],
                'invariance_better':cm['same_source_z_distance'] is not None and bm['same_source_z_distance'] is not None and cm['same_source_z_distance']<bm['same_source_z_distance'],
            }
        })
    r={
        'contract':'CSTAR_M1_SPENT_REPLAY_PREMISE_V3',
        'episodes':len(eps),'folds':folds,
        'truth_usage':'source truth is offline target/error only; candidate coordinates are route-domain-derived',
        'history_semantics':f'bounded final history window {a.history_window_s:g}s; this is not the formal online-prefix causal gate',
        'sensor_aux_semantics':'gas EMA derived from measured ppm; explicitly not audited FOPDT internal state',
        'formal_gate_authority':False,
        'limitations':[
            'not the formal CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1 producer',
            'no controlled intervention identity is inferred from historical arms',
            'no zS destructive/context-only/label-permutation controls in this premise screen',
            'no checkpoint from this premise screen may authorize closed loop',
        ],
    }
    r['pass']=bool(folds) and all(f['directional']['error_better'] and f['directional']['invariance_better'] for f in folds)
    r['verdict']='M1_SPENT_PREMISE_PASS' if r['pass'] else 'M1_SPENT_PREMISE_NO_GO'
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(r['verdict']);return 0 if r['pass'] else 2


if __name__=='__main__':raise SystemExit(main())
