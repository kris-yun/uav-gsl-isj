from __future__ import annotations
import argparse, json, math, random, sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from common.trace_io import load_manifest, load_episode
from m2_cpo.model import CPOResidualOperator, cpo_first_passage_nll, cpo_brier

THRESH=0.1


def plume_prior(source, route_xy, wind_uv):
    sx,sy=source; wu,wv=wind_uv; ws=max(1e-6,math.hypot(wu,wv)); cd,sd=wu/ws,wv/ws
    logits=[]; mus=[]
    for ax,ay in route_xy:
        dx=(ax-sx)*cd+(ay-sy)*sd; dy=-(ax-sx)*sd+(ay-sy)*cd; val=0.0
        if dx>0.15:
            sig=0.5*dx+0.3; val=(1.0/sig)*math.exp(-dy*dy/(2*sig*sig))/dx
        p=min(1-1e-5,max(1e-5,val/(val+0.3))); logits.append(math.log(p/(1-p))); mus.append(math.log1p(val))
    return logits,mus


def samples_from_episode(ep,horizon=20,stride=10):
    """Build retrospective path-conditioned replay samples.

    IMPORTANT: ``route`` below is the *subsequently executed* trajectory. It is
    not evidence that the route was fixed at the decision time. These samples
    therefore support only an observational/path-conditioned premise screen,
    never the formal do(route) gate.
    """
    out=[]; n=len(ep.time)
    for i in range(10,n-horizon,stride):
        route=list(zip(ep.pose_x[i+1:i+1+horizon],ep.pose_y[i+1:i+1+horizon]))
        wind=(ep.wind_u[i],ep.wind_v[i]); prior_l,prior_mu=plume_prior(ep.spec.source_xy,route,wind)
        sx,sy=ep.spec.source_xy; x0,y0=ep.pose_x[i],ep.pose_y[i]
        ws=max(1e-6,math.hypot(*wind)); cd,sd=wind[0]/ws,wind[1]/ws
        feats=[]
        for j,(x,y) in enumerate(route,1):
            rx,ry=x-sx,y-sy; dist=math.hypot(rx,ry); along=rx*cd+ry*sd; cross=abs(-rx*sd+ry*cd)
            feats.append([
                rx,ry,dist,along,cross,wind[0],wind[1],x-x0,y-y0,j/horizon,
                math.log1p(ep.gas[i]),ep.gas_ema_aux[i],
                math.sin(j/horizon*math.pi),math.cos(j/horizon*math.pi),
            ])
        future=ep.gas[i+1:i+1+horizon]
        hit=next((j for j,g in enumerate(future) if g>THRESH),horizon)
        out.append((feats,prior_l,prior_mu,hit))
    return out


def tensorize(rows,device):
    return (
        torch.tensor([r[0] for r in rows],dtype=torch.float32,device=device),
        torch.tensor([r[1] for r in rows],dtype=torch.float32,device=device),
        torch.tensor([r[2] for r in rows],dtype=torch.float32,device=device),
        torch.tensor([r[3] for r in rows],dtype=torch.long,device=device),
    )


def baseline_metrics(rows):
    nll=[]; brier=[]
    for _,logits,_,target in rows:
        h=[1/(1+math.exp(-z)) for z in logits]; surv=1.0; law=[]
        for p in h: law.append(surv*p); surv*=1-p
        law.append(surv); s=sum(law); law=[p/s for p in law]
        nll.append(-math.log(max(law[target],1e-12)))
        brier.append(sum((p-(1 if k==target else 0))**2 for k,p in enumerate(law)))
    return {"nll":sum(nll)/len(nll),"brier":sum(brier)/len(brier)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--steps",type=int,default=500)
    ap.add_argument("--seed",type=int,default=7)
    args=ap.parse_args()
    eps=[load_episode(s) for s in load_manifest(args.manifest)]
    device=torch.device("cpu")
    houses=sorted({e.spec.house for e in eps if e.spec.house}); folds=[]
    for held in houses or [""]:
        tr=[];te=[]
        for e in eps:
            (te if held and e.spec.house==held else tr).extend(samples_from_episode(e))
        if not held:
            te=tr[::5]; tr=[r for k,r in enumerate(tr) if k%5]
        if len(tr)<20 or len(te)<5: continue
        torch.manual_seed(args.seed); random.seed(args.seed)
        model=CPOResidualOperator(feature_dim=14,d_model=48,nhead=4,layers=2).to(device)
        opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-4)
        for _ in range(args.steps):
            batch=random.sample(tr,min(32,len(tr))); X,L,M,Y=tensorize(batch,device)
            out=model(X,L,M); loss=cpo_first_passage_nll(out,Y)+0.2*cpo_brier(out,Y)
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5.0); opt.step()
        X,L,M,Y=tensorize(te,device)
        with torch.no_grad():
            out=model(X,L,M)
            learned={
                "nll":float(cpo_first_passage_nll(out,Y)),
                "brier":float(cpo_brier(out,Y)),
                "mean_route_committor":float(out.route_committor.mean()),
            }
        base=baseline_metrics(te)
        folds.append({
            "heldout_house":held or "NONE","learned":learned,
            "baseline_instant_plume":base,
            "directional":{
                "nll_better":learned["nll"]<base["nll"],
                "brier_better":learned["brier"]<base["brier"],
            },
        })
    report={
        "contract":"CSTAR_M2_SPENT_OBSERVATIONAL_REPLAY_V2",
        "folds":folds,
        "formal_gate_authority":False,
        "route_identity":"retrospective subsequently executed path; NOT decision-locked do(route)",
        "input_rule":"future wind is not an input; future gas is label only",
        "sensor_aux_semantics":"gas EMA derived from measured ppm; not audited FOPDT internal state",
        "limitations":[
            "not the formal CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1 producer",
            "does not establish sequential intervention identification",
            "does not use decision-time recorded route plans or controlled open-loop route interventions",
            "contains only the simple instantaneous plume baseline, not the required plume/FOPDT and verified-physics baselines",
            "does not freeze a deployable checkpoint",
        ],
    }
    report["pass"]=bool(folds) and all(
        f["directional"]["nll_better"] and f["directional"]["brier_better"]
        for f in folds
    )
    report["verdict"]="M2_SPENT_OBSERVATIONAL_PREMISE_PASS" if report["pass"] else "M2_SPENT_OBSERVATIONAL_PREMISE_NO_GO"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(report["verdict"])
    return 0 if report["pass"] else 2


if __name__=="__main__": raise SystemExit(main())
