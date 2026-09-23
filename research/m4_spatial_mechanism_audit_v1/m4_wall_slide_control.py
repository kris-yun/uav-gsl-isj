#!/usr/bin/env python3
"""M4 wall-slide physical control.

This is NOT a proposed learning innovation. It is a Tier-1 anti-overengineering
control: replace M4-v3 obstacle retention with a source-agnostic conservative
2-D tangential wall deflection derived only from occupancy geometry.

All other M4-v3 ingredients remain unchanged.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F

_BASE_PATH=(Path(__file__).resolve().parents[1]/
            "causal_compositional_plume_world_model_v1"/
            "m4_v3_interventional_evolution.py")
_spec=importlib.util.spec_from_file_location("m4v3_base",_BASE_PATH)
base=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(base)

gaden_wind_index_schedule=base.gaden_wind_index_schedule
schedule_from_sequence=base.schedule_from_sequence
superposition_error=base.superposition_error
conservative_local_mix=base.conservative_local_mix
WindConditionedConservativeClosure=base.WindConditionedConservativeClosure
_base_grid=base._base_grid
_path_is_clear=base._path_is_clear
_scatter_add_flat=base._scatter_add_flat

def _free_normals(free_mask:torch.Tensor):
    """Approximate inward-free-space wall normal from Sobel gradient."""
    dtype=free_mask.dtype; device=free_mask.device
    kr=torch.tensor([[-1.,-2.,-1.],[0.,0.,0.],[1.,2.,1.]],device=device,dtype=dtype).reshape(1,1,3,3)/8.0
    kc=torch.tensor([[-1.,0.,1.],[-2.,0.,2.],[-1.,0.,1.]],device=device,dtype=dtype).reshape(1,1,3,3)/8.0
    gr=F.conv2d(free_mask,kr,padding=1)
    gc=F.conv2d(free_mask,kc,padding=1)
    n=torch.sqrt(gr*gr+gc*gc).clamp_min(1e-8)
    return gr/n,gc/n

def _scatter_displacement(src,active,dr,dc,free_mask,path_clear):
    """Bilinear conservative scatter for selected source cells."""
    b,_,h,w=free_mask.shape
    dtype=src.dtype; device=src.device; n=h*w
    row,col=_base_grid(h,w,device,dtype)
    rowf=row.reshape(-1); colf=col.reshape(-1)
    dest_r=rowf[None]+dr
    dest_c=colf[None]+dc
    r0=torch.floor(dest_r); c0=torch.floor(dest_c)
    fr=dest_r-r0; fc=dest_c-c0
    corners=(
        (r0,c0,(1-fr)*(1-fc)),
        (r0+1,c0,fr*(1-fc)),
        (r0,c0+1,(1-fr)*fc),
        (r0+1,c0+1,fr*fc),
    )
    source_index=torch.arange(n,device=device)[None].expand(b,-1)
    free_flat=free_mask[:,0].reshape(b,n)>0.5
    out=torch.zeros_like(src)
    retained=torch.zeros_like(src)
    for rr_f,cc_f,weight in corners:
        rr=rr_f.long(); cc=cc_f.long()
        inside=(rr>=0)&(rr<h)&(cc>=0)&(cc<w)
        idx=rr.clamp(0,h-1)*w+cc.clamp(0,w-1)
        dest_free=torch.gather(free_flat,1,idx)
        valid=active & path_clear & inside & dest_free
        amount=src*weight
        _scatter_add_flat(out,idx,amount*valid.to(dtype))
        blocked=active & inside & (~(path_clear & dest_free))
        _scatter_add_flat(retained,source_index,amount*blocked.to(dtype))
        # active & ~inside is physical outflow and is not retained.
    return out,retained

def conservative_wall_slide_remap(
    state:torch.Tensor,wind_xy:torch.Tensor,free_mask:torch.Tensor,
    dt_s:float,cell_m:float,characteristic_scale:float=1.0
):
    """Forward characteristic remap with one-step tangential wall projection.

    Direct clear paths use native M4-v3 remap geometry.
    A source cell whose short characteristic intersects an obstacle gets one
    tangential retry: remove the component pointing into the local wall normal.
    If the tangential retry is still blocked, retain mass at the source.
    """
    b,_,h,w=state.shape
    if free_mask.shape[0]==1 and b>1:
        free_mask=free_mask.expand(b,-1,-1,-1)
    dtype=state.dtype; device=state.device; n=h*w
    row,col=_base_grid(h,w,device,dtype)
    rowf=row.reshape(-1); colf=col.reshape(-1)
    src=state[:,0].reshape(b,n)*free_mask[:,0].reshape(b,n)
    dr=float(characteristic_scale)*float(dt_s)*wind_xy[:,0].reshape(b,n)/float(cell_m)
    dc=float(characteristic_scale)*float(dt_s)*wind_xy[:,1].reshape(b,n)/float(cell_m)
    direct_clear=_path_is_clear(free_mask,rowf,colf,dr,dc,substeps=4)

    # Direct clear source cells.
    direct_active=direct_clear
    direct,ret_direct=_scatter_displacement(
        src,direct_active,dr,dc,free_mask,direct_clear)

    # For blocked source cells, estimate free-space normal and remove only the
    # velocity component that points into the wall.
    nr,nc=_free_normals(free_mask)
    nr=nr[:,0].reshape(b,n); nc=nc[:,0].reshape(b,n)
    dot=dr*nr+dc*nc
    toward=(dot<0)
    proj=torch.where(toward,dot,torch.zeros_like(dot))
    tdr=dr-proj*nr
    tdc=dc-proj*nc
    blocked_active=(~direct_clear)
    tangent_clear=_path_is_clear(free_mask,rowf,colf,tdr,tdc,substeps=4)
    tangent,ret_tangent=_scatter_displacement(
        src,blocked_active,tdr,tdc,free_mask,tangent_clear)

    return (direct+ret_direct+tangent+ret_tangent).reshape(b,1,h,w)*free_mask

class SourceAgnosticWallSlideTransport(nn.Module):
    def __init__(self):
        super().__init__()
        self.closure=WindConditionedConservativeClosure()
        self.loss_raw=nn.Parameter(torch.tensor(-8.0))
        self.characteristic_scale=1.0

    def forward(self,state,wind_xy,free_mask,dt_s:float,cell_m:float):
        x=conservative_wall_slide_remap(
            state,wind_xy,free_mask,dt_s,cell_m,self.characteristic_scale)
        x=self.closure(x,wind_xy,free_mask)
        retention=torch.exp(-F.softplus(self.loss_raw)*float(dt_s))
        return x*retention*free_mask

class InterventionalEvolutionPropagator(nn.Module):
    def __init__(self,cell_m:float=0.1,internal_dt_s:float=0.1):
        super().__init__()
        self.cell_m=float(cell_m)
        self.internal_dt_s=float(internal_dt_s)
        self.transport=SourceAgnosticWallSlideTransport()
        self.source_strength_raw=nn.Parameter(torch.tensor(0.0))

    def source_strength(self):
        return F.softplus(self.source_strength_raw)

    def step(self,state,source_map,wind_xy,free_mask):
        transported=self.transport(
            state,wind_xy,free_mask,self.internal_dt_s,self.cell_m)
        return (transported+self.source_strength()*source_map)*free_mask

    def forward(self,source_map,wind_schedule,free_mask,record_steps=None):
        if record_steps is None:
            record_steps=[wind_schedule.shape[0]]
        wanted=set(int(x) for x in record_steps)
        state=torch.zeros_like(source_map); outputs={}
        for k in range(wind_schedule.shape[0]):
            state=self.step(state,source_map,wind_schedule[k],free_mask)
            if k+1 in wanted: outputs[k+1]=state
        return [outputs[int(k)] for k in record_steps]

def wall_slide_smoke(device="cpu"):
    h=w=31
    state=torch.zeros(1,1,h,w,device=device); state[0,0,15,13]=1
    mask=torch.ones_like(state); mask[:,:,:,15]=0
    wind=torch.zeros(1,2,h,w,device=device)
    wind[:,0]=0.25
    wind[:,1]=4.0
    out=conservative_wall_slide_remap(state,wind,mask,0.5,1.0,1.0)
    return {
      "mass_in":float(state.sum()),
      "mass_out":float(out.sum()),
      "across_wall":float(out[0,0,:,16:].sum()),
      "moved_tangentially":bool(float(out[0,0,16:,13:15].sum())>0.0),
    }
