#!/usr/bin/env python3
"""M4-v3 minimal source-agnostic interventional evolution propagator.

Core invariant: for fixed wind/geometry/parameters, transport is linear in the
concentration/source state. Wind changes the characteristic map itself through
semi-Lagrangian backtracing. Source identity never conditions transport.
"""
from __future__ import annotations

import struct
import torch
from torch import nn
from torch.nn import functional as F


def _base_grid(h:int,w:int,device,dtype):
    row,col=torch.meshgrid(
        torch.arange(h,device=device,dtype=dtype),
        torch.arange(w,device=device,dtype=dtype),
        indexing="ij")
    return row,col


def semi_lagrangian_advect(state:torch.Tensor, wind_xy:torch.Tensor,
                            dt_s:float, cell_m:float)->torch.Tensor:
    """Backtrace state along local wind.

    state: [B,1,H,W]; wind_xy: [B,2,H,W].
    H is GADEN x-index and W is GADEN y-index.
    """
    if state.ndim!=4 or wind_xy.ndim!=4 or state.shape[0]!=wind_xy.shape[0]:
        raise ValueError("shape mismatch")
    _,_,h,w=state.shape
    row,col=_base_grid(h,w,state.device,state.dtype)
    src_row=row[None]-dt_s*wind_xy[:,0]/cell_m
    src_col=col[None]-dt_s*wind_xy[:,1]/cell_m
    gx=2.0*src_col/max(w-1,1)-1.0
    gy=2.0*src_row/max(h-1,1)-1.0
    grid=torch.stack((gx,gy),dim=-1)
    return F.grid_sample(state,grid,mode="bilinear",padding_mode="zeros",
                         align_corners=True)


def zero_boundary_neighbor_mean(x:torch.Tensor)->torch.Tensor:
    """4-neighbour mean with zero exterior; never wraps across map boundaries."""
    p=F.pad(x,(1,1,1,1),mode="constant",value=0.0)
    up=p[:,:,0:-2,1:-1]
    down=p[:,:,2:,1:-1]
    left=p[:,:,1:-1,0:-2]
    right=p[:,:,1:-1,2:]
    return (up+down+left+right)/4.0


class SourceAgnosticLinearTransport(nn.Module):
    """Linear-in-state characteristic advection + local diffusion + decay.

    Trainable scalars are shared by all source hypotheses. The module's
    signature intentionally accepts no source ID, source map, or coordinates.
    """
    def __init__(self):
        super().__init__()
        self.diffusion_logit=nn.Parameter(torch.tensor(-2.0))
        self.decay_raw=nn.Parameter(torch.tensor(-5.0))

    def forward(self,state,wind_xy,free_mask,dt_s:float,cell_m:float):
        x=semi_lagrangian_advect(state,wind_xy,dt_s,cell_m)
        nbr=zero_boundary_neighbor_mean(x)
        alpha=torch.sigmoid(self.diffusion_logit)*0.5
        x=(1.0-alpha)*x+alpha*nbr
        decay=torch.exp(-F.softplus(self.decay_raw)*dt_s)
        return x*decay*free_mask


class InterventionalEvolutionPropagator(nn.Module):
    """Continuous source forcing passed through source-independent transport."""
    def __init__(self,cell_m:float=0.1,internal_dt_s:float=0.1):
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
        transported=self.transport(
            state,wind_xy,free_mask,self.internal_dt_s,self.cell_m)
        # Separate forcing term. Source never enters transport parameters.
        return (transported+self.source_rate()*source_map)*free_mask

    def forward(self,source_map,wind_schedule,free_mask,record_steps=None):
        """source_map [B,1,H,W], wind_schedule [T,B,2,H,W]."""
        if record_steps is None:
            record_steps=[wind_schedule.shape[0]]
        wanted=set(int(x) for x in record_steps)
        if not wanted or min(wanted)<1 or max(wanted)>wind_schedule.shape[0]:
            raise ValueError("record_steps outside schedule")
        state=torch.zeros_like(source_map)
        outputs={}
        for k in range(wind_schedule.shape[0]):
            state=self.step(state,source_map,wind_schedule[k],free_mask)
            if k+1 in wanted:
                outputs[k+1]=state*self.output_scale()
        return [outputs[int(k)] for k in record_steps]


def _f32(x:float)->float:
    return struct.unpack("<f",struct.pack("<f",float(x)))[0]


def gaden_wind_index_schedule(num_steps:int, physics_dt_s:float=0.1,
                              wind_iteration_dt_s:float=1.0,
                              iteration_count:int=11,
                              loop_from:int=1,loop_to:int=10)->list[int]:
    """Emulate GADEN RunningSimulation's float32 wind-index timing.

    In GADEN each MoveFilaments() uses the current wind, then the wind index is
    advanced when currentTime > lastWindUpdateTime + windIterationDeltaTime,
    and only afterwards currentTime is incremented by deltaTime.
    """
    if not (0<=loop_from<=loop_to<iteration_count):
        raise ValueError("bad loop bounds")
    current=_f32(0.0)
    last=_f32(0.0)
    dt=_f32(physics_dt_s)
    wind_dt=_f32(wind_iteration_dt_s)
    idx=0
    out=[]
    for _ in range(int(num_steps)):
        out.append(idx)
        if current > _f32(last+wind_dt):
            idx+=1
            if idx>loop_to:
                idx=loop_from
            elif idx>=iteration_count:
                idx=iteration_count-1
            last=current
        current=_f32(current+dt)
    return out


def schedule_from_sequence(wind_sequence:torch.Tensor,num_steps:int,
                           batch_size:int=1,physics_dt_s:float=0.1,
                           wind_iteration_dt_s:float=1.0,
                           loop_from:int=1,loop_to:int=10)->torch.Tensor:
    """Expand [I,2,H,W] sequence to exact GADEN-style [T,B,2,H,W]."""
    if wind_sequence.ndim!=4 or wind_sequence.shape[1]!=2:
        raise ValueError("wind_sequence must be [I,2,H,W]")
    ids=gaden_wind_index_schedule(
        num_steps,physics_dt_s,wind_iteration_dt_s,
        wind_sequence.shape[0],loop_from,loop_to)
    s=wind_sequence[torch.as_tensor(ids,device=wind_sequence.device)]
    return s[:,None].expand(-1,batch_size,-1,-1,-1)


def superposition_error(model,source_a,source_b,wind_schedule,mask,a=0.37,b=0.61):
    with torch.no_grad():
        lhs=model(a*source_a+b*source_b,wind_schedule,mask)[0]
        rhs=(a*model(source_a,wind_schedule,mask)[0]+
             b*model(source_b,wind_schedule,mask)[0])
        return float((lhs-rhs).abs().max())


def wind_reversal_displacement_smoke(device="cpu"):
    h=w=41
    m=InterventionalEvolutionPropagator(cell_m=1.0,internal_dt_s=1.0).to(device)
    with torch.no_grad():
        m.transport.diffusion_logit.fill_(-20.0)
        m.transport.decay_raw.fill_(-20.0)
    state=torch.zeros(1,1,h,w,device=device); state[0,0,20,20]=1
    mask=torch.ones_like(state)
    wp=torch.zeros(1,2,h,w,device=device); wp[:,1]=1.0
    wn=-wp
    z=torch.zeros_like(wp)
    p=m.transport(state,wp,mask,1.0,1.0)[0,0]
    n=m.transport(state,wn,mask,1.0,1.0)[0,0]
    q=m.transport(state,z,mask,1.0,1.0)[0,0]
    col=torch.arange(w,device=device,dtype=p.dtype)[None,:]
    cp=float((p*col).sum()/p.sum())
    cn=float((n*col).sum()/n.sum())
    cq=float((q*col).sum()/q.sum())
    return {
        "positive_wind_centroid_col":cp,
        "negative_wind_centroid_col":cn,
        "zero_wind_centroid_col":cq,
        "reversal_pass":cp>20.5 and cn<19.5,
        "no_advection_pass":abs(cq-20.0)<1e-4,
    }
