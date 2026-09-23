#!/usr/bin/env python3
from pathlib import Path
import importlib.util, json, torch

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py"
spec=importlib.util.spec_from_file_location("m4v3",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

torch.manual_seed(1)
model=m.InterventionalEvolutionPropagator(cell_m=1.0,internal_dt_s=1.0)
h=w=25
s1=torch.zeros(1,1,h,w); s1[0,0,8,8]=1
s2=torch.zeros(1,1,h,w); s2[0,0,16,17]=1
mask=torch.ones_like(s1)
wind=torch.zeros(8,1,2,h,w); wind[:,:,0]=0.2; wind[:,:,1]=0.5
err=m.superposition_error(model,s1,s2,wind,mask)
rev=m.wind_reversal_displacement_smoke()
# Structural source-leakage audit: transport.forward accepts only state, wind, mask, dt, cell.
transport_args=list(model.transport.forward.__code__.co_varnames[:model.transport.forward.__code__.co_argcount])
result={"superposition_max_abs_error":err,"superposition_pass":err<1e-5,
        "wind_reversal":rev,"transport_forward_args":transport_args,
        "source_leakage_signature_pass":"source" not in " ".join(transport_args).lower()}
if not all([result["superposition_pass"],rev["reversal_pass"],result["source_leakage_signature_pass"]]):
    raise SystemExit(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
