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
mass=m.transport_mass_balance_smoke()
wall=m.wall_nonpenetration_smoke()

# Structural source-leakage audit.
transport_args=list(model.transport.forward.__code__.co_varnames[:model.transport.forward.__code__.co_argcount])

# Conservative local closure must not wrap across the exterior boundary.
edge=torch.zeros(1,1,9,9); edge[0,0,4,0]=1.0
edge_mask=torch.ones_like(edge)
logits=torch.full((1,5,9,9),-20.0)
logits[:,4]=20.0  # push right; still cannot wrap around an exterior boundary.
mixed=m.conservative_local_mix(edge,logits,edge_mask)
boundary_wrap=float(mixed[0,0,4,-1].abs())

# D0 trains three source-wind cells together. The local scatter must preserve
# that batch dimension in both forward and backward passes.
batch_state=torch.rand(3,1,9,9)
batch_logits=torch.randn(3,5,9,9,requires_grad=True)
batch_mask=torch.ones(1,1,9,9)
batch_mixed=m.conservative_local_mix(batch_state,batch_logits,batch_mask)
spatial_weight=torch.arange(81,dtype=batch_mixed.dtype).reshape(1,1,9,9)
(batch_mixed*spatial_weight).sum().backward()
batch_backward_pass=(batch_mixed.shape==(3,1,9,9) and
                     batch_logits.grad is not None and
                     bool(torch.isfinite(batch_logits.grad).all()) and
                     bool((batch_logits.grad.abs()>0).any()))
batch_mass_error=float((batch_mixed.sum(dim=(1,2,3))-
                        batch_state.sum(dim=(1,2,3))).abs().max())

# GADEN timing contract: first wind is used before update; dynamic sequence must
# advance and loop only inside [1,10].
ids=m.gaden_wind_index_schedule(140,0.1,1.0,11,1,10)
timing_pass=(ids[0]==0 and 1 in ids and max(ids)<=10 and min(ids)>=0 and ids[-1] in range(1,11))

result={
  "superposition_max_abs_error":err,
  "superposition_pass":err<1e-5,
  "wind_reversal":rev,
  "mass_balance":mass,
  "mass_balance_pass":mass["abs_error"]<1e-6,
  "wall_nonpenetration":wall,
  "transport_forward_args":transport_args,
  "source_leakage_signature_pass":"source" not in " ".join(transport_args).lower(),
  "zero_boundary_wrap_value":boundary_wrap,
  "zero_boundary_pass":boundary_wrap<1e-8,
  "batch_backward_pass":batch_backward_pass,
  "batch_mass_error":batch_mass_error,
  "wind_schedule_prefix":ids[:30],
  "wind_schedule_suffix":ids[-20:],
  "wind_schedule_pass":timing_pass,
}
checks=[
  result["superposition_pass"],
  rev["reversal_pass"],
  rev["no_advection_pass"],
  result["mass_balance_pass"],
  wall["nonpenetration_pass"],
  result["source_leakage_signature_pass"],
  result["zero_boundary_pass"],
  result["batch_backward_pass"],
  result["batch_mass_error"]<1e-5,
  result["wind_schedule_pass"],
]
if not all(checks):
    raise SystemExit(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
