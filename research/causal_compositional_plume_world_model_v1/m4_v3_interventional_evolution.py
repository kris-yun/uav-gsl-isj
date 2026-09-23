#!/usr/bin/env python3
"""M4-v3 minimal source-agnostic interventional evolution propagator.

Core invariant: for fixed wind/geometry/parameters, the transport mapping is
linear in concentration/source state. Wind changes the characteristic map
itself via semi-Lagrangian backtracing.
"""
from __future__ import annotations
import math
import torch
from torch import nn
from torch.nn import functional as F

def _base_grid(h:int,w:int,device,dtype):
    yy,xx=torch.meshgrid(
        torch.arange(h,device=device,dtype=dtype),
        torch.arange(w,device=device,dtype=dtype),
        indexing="ij")
    return yy,xx

def semi_lagrangian_advect(state:torch.Tensor, wind_xy:torch.Tensor,
                            dt_s:float, cell_m:float)->torch.Tensor:
    """Backtrace state along local wind. state [B,1,H,W], wind [B,2,H,W].

    H is GADEN x-index and W is GADEN y-index.
    """
    if state.ndim!=4 or wind_xy.ndim!=4 or state.shape[0]!=wind_xy.shape[0]:
        raise ValueError("shape mismatch")
    b,_,h,w=state.shape
    row,col=_base_grid(h,w,state.device,state.dtype)
    # local wind component 0 moves GADEN x -> tensor row; component 1 moves y -> column
    src_row=row[None]-dt_s*wind_xy[:,0]/cell_m
    src_col=col[None]-dt_s*wind_xy[:,1]/cell_m
    gx=2.0*src_col/max(w-1,1)-1.0
    gy=2.0*src_row/max(h-1,1)-1.0
    grid=torch.stack((gx,gy),dim=-1)
    return F.grid_sample(state,grid,mode="bilinear",padding_mode="zeros",
                         align_corners=True)

class SourceAgnosticLinearTransport(nn.Module):
    """Linear-in-state advection + isotropic diffusion + decay.

    Trainable scalars are shared by every source. No source ID or coordinate is
    accepted by this module.
    """
    def __init__(self):
        super().__init__()
        self.diffusion_logit=nn.Parameter(torch.tensor(-2.0))
        self.decay_raw=nn.Parameter(torch.tensor(-5.0))

    def forward(self,state,wind_xy,free_mask,dt_s:float,cell_m:float):
        x=semi_lagrangian_advect(state,wind_xy,dt_s,cell_m)
        # Conservative 5-point diffusion; convex weights keep state nonnegative.
        nbr=(torch.roll(x,1,-2)+torch.roll(x,-1,-2)+
             torch.roll(x,1,-1)+torch.roll(x,-1,-1))/4.0
        alpha=torch.sigmoid(self.diffusion_logit)*0.5
        x=(1.0-alpha)*x+alpha*nbr
        decay=torch.exp(-F.softplus(self.decay_raw)*dt_s)
        x=x*decay
        return x*free_mask

class InterventionalEvolutionPropagator(nn.Module):
    """Continuous source forcing passed through source-independent transport."""
    def __init__(self,cell_m:float=0.1,internal_dt_s:float=1.0):
        super().__init__()
        self.cell_m=float(cell_m)
        self.internal_dt_s=float(internal_dt_s)
        self.transport=SourceAgnosticLinearTransport()
        self.source_rate_raw=nn.Parameter(torch.tensor(-1.0))
        self.output_scale_raw=nn.Parameter(torch.tensor(0.0))

    def source_rate(self):
        return F.softplus(self.source_rate_raw)

    def output_scale(self):
        return F.softplus(self.output_scale_raw)

    def step(self,state,source_map,wind_xy,free_mask):
        # Injection is separate forcing; transport never receives source_map.
        transported=self.transport(state,wind_xy,free_mask,
                                   self.internal_dt_s,self.cell_m)
        return (transported+self.source_rate()*source_map)*free_mask

    def forward(self,source_map,wind_schedule,free_mask,record_steps=None):
        """source_map [B,1,H,W], wind_schedule [T,B,2,H,W]."""
        if record_steps is None: record_steps=[wind_schedule.shape[0]]
        wanted=set(int(x) for x in record_steps)
        state=torch.zeros_like(source_map)
        outputs={}
        for k in range(wind_schedule.shape[0]):
            state=self.step(state,source_map,wind_schedule[k],free_mask)
            if k+1 in wanted: outputs[k+1]=state*self.output_scale()
        return [outputs[int(k)] for k in record_steps]

def superposition_error(model,source_a,source_b,wind_schedule,mask,a=0.37,b=0.61):
    with torch.no_grad():
        lhs=model(a*source_a+b*source_b,wind_schedule,mask)[0]
        rhs=a*model(source_a,wind_schedule,mask)[0]+b*model(source_b,wind_schedule,mask)[0]
        return float((lhs-rhs).abs().max())

def wind_reversal_displacement_smoke(device="cpu"):
    """Synthetic directional sanity test; no learned/plume data."""
    h=w=41
    m=InterventionalEvolutionPropagator(cell_m=1.0,internal_dt_s=1.0).to(device)
    with torch.no_grad():
        m.source_rate_raw.fill_(-20.0)  # isolate one transported impulse after manual state setup
        m.transport.diffusion_logit.fill_(-20.0)
        m.transport.decay_raw.fill_(-20.0)
    state=torch.zeros(1,1,h,w,device=device); state[0,0,20,20]=1
    mask=torch.ones_like(state)
    wp=torch.zeros(1,2,h,w,device=device); wp[:,1]=1.0
    wn=-wp
    p=m.transport(state,wp,mask,1.0,1.0)[0,0]
    n=m.transport(state,wn,mask,1.0,1.0)[0,0]
    col=torch.arange(w,device=device,dtype=p.dtype)[None,:]
    cp=float((p*col).sum()/p.sum())
    cn=float((n*col).sum()/n.sum())
    return {"positive_wind_centroid_col":cp,"negative_wind_centroid_col":cn,
            "reversal_pass":cp>20.5 and cn<19.5}
