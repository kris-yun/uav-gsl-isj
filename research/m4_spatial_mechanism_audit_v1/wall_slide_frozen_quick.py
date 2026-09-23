#!/usr/bin/env python3
import argparse, importlib.util, json
from pathlib import Path
import torch

def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    root=a.repo_root; cr=root/"research/causal_compositional_plume_world_model_v1"
    d0=load(cr/"m4_v3_d0_house02.py","d0"); modelmod=load(root/"research/m4_spatial_mechanism_audit_v1/m4_wall_slide_control.py","wall")
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"; dyn=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"; outd=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923"
    src,free=d0.load_static_context(bank); winds,_=d0.load_dynamic_winds(dyn); man=json.loads((outd/"train_manifest.json").read_text())
    pairs=(("S2","W2"),("S2","W1")); sb=torch.cat([src[s] for s,_ in pairs]); sch=d0.build_batch_schedule(modelmod,winds,pairs,torch.device("cpu"))
    truth={p:{ps:d0.target(bank,*p,ps)[None] for ps in d0.PLUME_SEEDS} for p in pairs}
    res={"mode":"WALL_SLIDE_FROZEN_QUICK","refit":False,"fits":{}}
    for seed in d0.TRAIN_SEEDS:
        cp=outd/f"m4v3_seed{seed}.pt"
        if d0.sha256(cp)!=man["fits"][f"m4v3_seed{seed}"]["checkpoint_sha256"]: raise RuntimeError("hash")
        m=modelmod.InterventionalEvolutionPropagator(cell_m=.2,internal_dt_s=d0.PHYSICS_DT_S); m.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True)); m.eval()
        with torch.no_grad(): p=torch.log1p(d0.evolve_to_records(m,sb,sch,free,False).clamp_min(0))
        dw=p[0:1]-p[1:2]; rr={}
        for ps in d0.PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]
            rr[ps]={"wind_delta":d0.delta_metrics(dw,y22-y21,free),"field_mse":d0.free_mse(p[0:1],y22,free)}
        res["fits"][str(seed)]=rr
    res["all_cosine_gt_0p5"]=all(res["fits"][str(s)][p]["wind_delta"]["cosine"]>.5 for s in d0.TRAIN_SEEDS for p in d0.PLUME_SEEDS)
    a.output.write_text(json.dumps(res,indent=2)+"\n"); print(json.dumps(res,indent=2))
if __name__=="__main__": main()
