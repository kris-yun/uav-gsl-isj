#!/usr/bin/env python3
"""Frozen M4-v3 checkpoint surgery: add fixed three-slab Wz exchange, no refit."""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import torch

def load_py(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); root=a.repo_root
    v=load_py(root/"research/m4_spatial_mechanism_audit_v1/m4_vertical_three_slab_control.py","v")
    base=load_py(root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py","base")
    d0=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dynamic=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    src,free,_=v.load_static(bank); winds,_=v.load_wind3(dynamic)
    man=json.loads((d0/"train_manifest.json").read_text())
    pairs=(("S2","W2"),("S2","W1"),("S1","W2"))
    source=torch.cat([src[s] for s,_ in pairs]); sch=v.schedule(base,winds,pairs,torch.device("cpu"))
    truth={(s,w):{p:v.target(bank,s,w,p)[None] for p in v.PLUME_SEEDS} for s,w in pairs}
    out={"mode":"FROZEN_M4_CHECKPOINT_VERTICAL_SURGERY","refit":False,"fits":{}}
    allpass=True
    for seed in v.TRAIN_SEEDS:
        cp=d0/f"m4v3_seed{seed}.pt"
        if v.sha256(cp)!=man["fits"][f"m4v3_seed{seed}"]["checkpoint_sha256"]:
            raise RuntimeError("base checkpoint hash mismatch")
        sd=torch.load(cp,map_location="cpu",weights_only=True)
        model=v.Model(base)
        mapped={
          "source_strength_raw":sd["source_strength_raw"],
          "transport.horizontal.loss_raw":sd["transport.loss_raw"],
          "transport.horizontal.closure.logits.weight":sd["transport.closure.logits.weight"],
          "transport.horizontal.closure.logits.bias":sd["transport.closure.logits.bias"],
        }
        model.load_state_dict(mapped,strict=True); model.eval()
        with torch.no_grad():
            pred=v.evolve(model,source,sch,free,False); plog=torch.log1p(pred.clamp_min(0))
        dw=plog[0:1]-plog[1:2]; ds=plog[0:1]-plog[2:3]
        zsch=sch.clone(); zsch[:,:,2]=0
        with torch.no_grad(): ab=torch.log1p(v.evolve(model,source,zsch,free,False).clamp_min(0))
        abl=ab[0:1]-ab[1:2]
        wn=float(torch.linalg.vector_norm(v.flatten(dw,free))); an=float(torch.linalg.vector_norm(v.flatten(abl,free)))
        one=v.schedule(base,winds,(("S1","W2"),),torch.device("cpu"))
        sup=v.superposition(model,src["S1"],src["S2"],one,free)
        sr={"vertical_ablation_wind_norm_ratio":an/wn if wn>0 else float("inf"),
            "superposition_max_abs_error":sup,"plumes":{}}
        seedpass=sup<1e-5
        for ps in v.PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]; y21=truth[("S2","W1")][ps]; y12=truth[("S1","W2")][ps]
            wm=v.delta_metrics(dw,y22-y21,free); sm=v.delta_metrics(ds,y22-y12,free)
            tws=wm["true_norm"]/sm["true_norm"]; pws=wm["pred_norm"]/sm["pred_norm"]; rws=pws/tws
            tc=v.centroid_shift(y21,y22,free); pc=v.centroid_shift(plog[1:2],plog[0:1],free)
            cr=pc["norm"]/tc["norm"]; mse=v.free_mse(plog[0:1],y22,free)
            gates={"wind_amplitude":.5<=wm["amplitude_ratio"]<=1.5,"wind_cosine":wm["cosine"]>.5,
                   "centroid_ratio":cr>.5,"relative_wind_source":rws>.5,
                   "source_amplitude":sm["amplitude_ratio"]>.5,
                   "beats_frozen_monolithic_mse":mse<v.MONO_MSE[seed][ps]}
            pp=all(gates.values()); seedpass &= pp
            sr["plumes"][ps]={"field_mse":mse,"wind_delta":wm,"source_delta":sm,
                              "relative_wind_to_source":rws,"centroid_shift_magnitude_ratio":cr,
                              "gates":gates,"pass":pp}
        sr["pass"]=seedpass; out["fits"][str(seed)]=sr; allpass &= seedpass
    out["decision"]="VERTICAL_FROZEN_SURGERY_PASSES_D0" if allpass else "VERTICAL_FROZEN_SURGERY_FAILS_D0"
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,allow_nan=True)+"\n"); print(json.dumps(out,indent=2,allow_nan=True))
if __name__=="__main__": main()
