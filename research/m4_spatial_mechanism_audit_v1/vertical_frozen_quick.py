#!/usr/bin/env python3
import argparse, importlib.util, json
from pathlib import Path
import torch
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    root=a.repo_root; v=load(root/"research/m4_spatial_mechanism_audit_v1/m4_vertical_three_slab_control.py","v"); base=load(root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py","base")
    d0=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923"; bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"; dyn=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    src,free,_=v.load_static(bank); winds,_=v.load_wind3(dyn); man=json.loads((d0/"train_manifest.json").read_text())
    pairs=(("S2","W2"),("S2","W1")); sb=torch.cat([src[s] for s,_ in pairs]); sch=v.schedule(base,winds,pairs,torch.device("cpu"))
    truth={p:{ps:v.target(bank,*p,ps)[None] for ps in v.PLUME_SEEDS} for p in pairs}
    res={"mode":"VERTICAL_FROZEN_QUICK","refit":False,"fits":{}}
    for seed in v.TRAIN_SEEDS:
        cp=d0/f"m4v3_seed{seed}.pt"
        if v.sha256(cp)!=man["fits"][f"m4v3_seed{seed}"]["checkpoint_sha256"]: raise RuntimeError("hash")
        sd=torch.load(cp,map_location="cpu",weights_only=True); m=v.Model(base)
        m.load_state_dict({
          "source_strength_raw":sd["source_strength_raw"],
          "transport.horizontal.loss_raw":sd["transport.loss_raw"],
          "transport.horizontal.closure.logits.weight":sd["transport.closure.logits.weight"],
          "transport.horizontal.closure.logits.bias":sd["transport.closure.logits.bias"]},strict=True); m.eval()
        with torch.no_grad(): p=torch.log1p(v.evolve(m,sb,sch,free,False).clamp_min(0))
        dw=p[0:1]-p[1:2]; rr={}
        for ps in v.PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]
            rr[ps]={"wind_delta":v.delta_metrics(dw,y22-y21,free),"field_mse":v.free_mse(p[0:1],y22,free)}
        res["fits"][str(seed)]=rr
    res["all_cosine_gt_0p5"]=all(res["fits"][str(s)][p]["wind_delta"]["cosine"]>.5 for s in v.TRAIN_SEEDS for p in v.PLUME_SEEDS)
    a.output.write_text(json.dumps(res,indent=2)+"\n"); print(json.dumps(res,indent=2))
if __name__=="__main__": main()
