#!/usr/bin/env python3
"""M4-v3 source-agnostic interventional evolution propagator.

Scientific invariants:
- source hypotheses enter only as external forcing;
- prescribed wind changes a forward characteristic transport map;
- transport/closure are nonnegative and linear in concentration/source state
  for fixed wind and geometry;
- obstacle cells cannot transmit mass;
- characteristic remap and local closure conserve in-domain mass except for
  explicit outflow and a separately parameterized source-independent sink.
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


def _scatter_add_flat(out:torch.Tensor,index:torch.Tensor,value:torch.Tensor):
    out.scatter_add_(1,index,value)


def _path_is_clear(free_mask:torch.Tensor,row:torch.Tensor,col:torch.Tensor,
                   dr:torch.Tensor,dc:torch.Tensor,substeps:int=4)->torch.Tensor:
    """Nearest-cell visibility along a short forward characteristic segment."""
    b,_,h,w=free_mask.shape
    free=free_mask[:,0].reshape(b,-1)>0.5
    clear=torch.ones_like(dr,dtype=torch.bool)
    for k in range(1,substeps+1):
        frac=float(k)/float(substeps)
        rr=torch.round(row[None]+frac*dr).long()
        cc=torch.round(col[None]+frac*dc).long()
        inside=(rr>=0)&(rr<h)&(cc>=0)&(cc<w)
        idx=rr.clamp(0,h-1)*w+cc.clamp(0,w-1)
        sampled=torch.gather(free,1,idx)
        # Out-of-domain is outflow, not an obstacle. In-domain obstacle
        # intersections block the segment.
        clear &= (~inside) | sampled
    return clear


def conservative_characteristic_remap(
    state:torch.Tensor,wind_xy:torch.Tensor,free_mask:torch.Tensor,
    dt_s:float,cell_m:float,characteristic_scale:float=1.0
)->torch.Tensor:
    """Forward bilinear characteristic remap with obstacle retention.

    Each free source cell sends scalar mass to its bilinear destination under
    x_{k+1}=x_k+dt*W(x_k). Contributions aimed through/into obstacles are
    retained at the source. Contributions leaving the map are physical outflow.
    """
    if state.ndim!=4 or wind_xy.ndim!=4 or free_mask.ndim!=4:
        raise ValueError("all inputs must be 4D")
    b,_,h,w=state.shape
    if wind_xy.shape!=(b,2,h,w):
        raise ValueError("wind shape mismatch")
    if free_mask.shape[-2:]!=(h,w):
        raise ValueError("mask geometry mismatch")
    if free_mask.shape[0] not in (1,b):
        raise ValueError("mask batch mismatch")
    if free_mask.shape[0]==1 and b>1:
        free_mask=free_mask.expand(b,-1,-1,-1)

    dtype=state.dtype; device=state.device; n=h*w
    row,col=_base_grid(h,w,device,dtype)
    rowf=row.reshape(-1); colf=col.reshape(-1)
    src=state[:,0].reshape(b,n)*free_mask[:,0].reshape(b,n)
    dr=float(characteristic_scale)*float(dt_s)*wind_xy[:,0].reshape(b,n)/float(cell_m)
    dc=float(characteristic_scale)*float(dt_s)*wind_xy[:,1].reshape(b,n)/float(cell_m)
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
    path_clear=_path_is_clear(free_mask,rowf,colf,dr,dc,substeps=4)
    out=torch.zeros_like(src)

    for rr_f,cc_f,weight in corners:
        rr=rr_f.long(); cc=cc_f.long()
        inside=(rr>=0)&(rr<h)&(cc>=0)&(cc<w)
        idx=rr.clamp(0,h-1)*w+cc.clamp(0,w-1)
        dest_free=torch.gather(free_flat,1,idx)
        valid=inside & dest_free & path_clear
        amount=src*weight
        _scatter_add_flat(out,idx,amount*valid.to(dtype))
        blocked=inside & (~(dest_free & path_clear))
        _scatter_add_flat(out,source_index,amount*blocked.to(dtype))
        # ~inside is deliberate outflow.
    return out.reshape(b,1,h,w)*free_mask


def conservative_local_mix(state:torch.Tensor,logits:torch.Tensor,
                           free_mask:torch.Tensor)->torch.Tensor:
    """Conservative 5-way source-cell mixing: stay/up/down/left/right."""
    b,_,h,w=state.shape
    if logits.shape!=(b,5,h,w):
        raise ValueError("local-mix logits shape mismatch")
    if free_mask.shape[0]==1 and b>1:
        free_mask=free_mask.expand(b,-1,-1,-1)
    weights=torch.softmax(logits,dim=1)
    src=(state[:,0]*free_mask[:,0]).reshape(b,-1)
    n=h*w
    out=torch.zeros_like(src)
    source_index=torch.arange(n,device=state.device)[None].expand(b,-1)
    rows=torch.arange(h,device=state.device)[:,None].expand(h,w).reshape(-1)
    cols=torch.arange(w,device=state.device)[None,:].expand(h,w).reshape(-1)
    free=free_mask[:,0].reshape(b,-1)>0.5
    directions=((0,0),(-1,0),(1,0),(0,-1),(0,1))

    for k,(di,dj) in enumerate(directions):
        rr=rows[None]+di; cc=cols[None]+dj
        inside=(rr>=0)&(rr<h)&(cc>=0)&(cc<w)
        idx=rr.clamp(0,h-1)*w+cc.clamp(0,w-1)
        dest_free=torch.gather(free,1,idx)
        valid=inside & dest_free
        amount=src*weights[:,k].reshape(b,-1)
        _scatter_add_flat(out,idx,amount*valid.to(state.dtype))
        _scatter_add_flat(out,source_index,amount*(~valid).to(state.dtype))
    return out.reshape(b,1,h,w)*free_mask


class WindConditionedConservativeClosure(nn.Module):
    """Wind-conditioned conservative local mixing; never sees source."""
    def __init__(self):
        super().__init__()
        self.logits=nn.Conv2d(3,5,1,bias=True)
        with torch.no_grad():
            self.logits.weight.zero_()
            self.logits.bias[:] = torch.tensor([4.0,0.0,0.0,0.0,0.0])

    def forward(self,state,wind_xy,free_mask):
        speed=torch.linalg.vector_norm(wind_xy,dim=1,keepdim=True)
        context=torch.cat((wind_xy,speed),dim=1)
        return conservative_local_mix(state,self.logits(context),free_mask)


class SourceAgnosticLinearTransport(nn.Module):
    """Characteristic remap + conservative local closure + explicit sink."""
    def __init__(self):
        super().__init__()
        self.closure=WindConditionedConservativeClosure()
        self.loss_raw=nn.Parameter(torch.tensor(-8.0))
        self.characteristic_scale=1.0  # 1 method; 0 frozen ablation.

    def forward(self,state,wind_xy,free_mask,dt_s:float,cell_m:float):
        x=conservative_characteristic_remap(
            state,wind_xy,free_mask,dt_s,cell_m,self.characteristic_scale)
        x=self.closure(x,wind_xy,free_mask)
        retention=torch.exp(-F.softplus(self.loss_raw)*float(dt_s))
        return x*retention*free_mask


class InterventionalEvolutionPropagator(nn.Module):
    """Continuous source forcing passed through one shared transport operator."""
    def __init__(self,cell_m:float=0.1,internal_dt_s:float=0.1):
        super().__init__()
        self.cell_m=float(cell_m)
        self.internal_dt_s=float(internal_dt_s)
        self.transport=SourceAgnosticLinearTransport()
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
        if not wanted or min(wanted)<1 or max(wanted)>wind_schedule.shape[0]:
            raise ValueError("record_steps outside schedule")
        state=torch.zeros_like(source_map)
        outputs={}
        for k in range(wind_schedule.shape[0]):
            state=self.step(state,source_map,wind_schedule[k],free_mask)
            if k+1 in wanted:
                outputs[k+1]=state
        return [outputs[int(k)] for k in record_steps]


def _f32(x:float)->float:
    return struct.unpack("<f",struct.pack("<f",float(x)))[0]


def gaden_wind_index_schedule(num_steps:int,physics_dt_s:float=0.1,
                              wind_iteration_dt_s:float=1.0,
                              iteration_count:int=11,
                              loop_from:int=1,loop_to:int=10)->list[int]:
    """Emulate GADEN RunningSimulation wind timing/order."""
    if not (0<=loop_from<=loop_to<iteration_count):
        raise ValueError("bad loop bounds")
    current=_f32(0.0); last=_f32(0.0)
    dt=_f32(physics_dt_s); wind_dt=_f32(wind_iteration_dt_s)
    idx=0; out=[]
    for _ in range(int(num_steps)):
        out.append(idx)
        if current > _f32(last+wind_dt):
            idx+=1
            if idx>loop_to: idx=loop_from
            elif idx>=iteration_count: idx=iteration_count-1
            last=current
        current=_f32(current+dt)
    return out


def schedule_from_sequence(wind_sequence:torch.Tensor,num_steps:int,
                           batch_size:int=1,physics_dt_s:float=0.1,
                           wind_iteration_dt_s:float=1.0,
                           loop_from:int=1,loop_to:int=10)->torch.Tensor:
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


def transport_mass_balance_smoke(device="cpu"):
    h=w=31
    m=SourceAgnosticLinearTransport().to(device)
    with torch.no_grad():
        m.loss_raw.fill_(-30.0)
        m.closure.logits.weight.zero_()
        m.closure.logits.bias[:] = torch.tensor([2.,0.,0.,0.,0.],device=device)
    state=torch.zeros(1,1,h,w,device=device); state[0,0,15,15]=1
    mask=torch.ones_like(state)
    wind=torch.zeros(1,2,h,w,device=device); wind[:,1]=0.35
    out=m(state,wind,mask,0.5,1.0)
    return {"mass_in":float(state.sum()),"mass_out":float(out.sum()),
            "abs_error":abs(float(out.sum()-state.sum()))}


def wall_nonpenetration_smoke(device="cpu"):
    h=w=31
    state=torch.zeros(1,1,h,w,device=device); state[0,0,15,13]=1
    mask=torch.ones_like(state); mask[:,:,:,15]=0
    wind=torch.zeros(1,2,h,w,device=device); wind[:,1]=4.0
    out=conservative_characteristic_remap(state,wind,mask,0.5,1.0,1.0)
    across=float(out[0,0,:,16:].sum())
    return {"mass_across_wall":across,"mass_total":float(out.sum()),
            "nonpenetration_pass":across<1e-8}


def wind_reversal_displacement_smoke(device="cpu"):
    h=w=41
    state=torch.zeros(1,1,h,w,device=device); state[0,0,20,20]=1
    mask=torch.ones_like(state)
    wp=torch.zeros(1,2,h,w,device=device); wp[:,1]=1.0
    wn=-wp; z=torch.zeros_like(wp)
    p=conservative_characteristic_remap(state,wp,mask,1.0,1.0)
    n=conservative_characteristic_remap(state,wn,mask,1.0,1.0)
    q=conservative_characteristic_remap(state,z,mask,1.0,1.0)
    col=torch.arange(w,device=device,dtype=state.dtype)[None,:]
    def centroid_col(a):
        a=a[0,0]; return float((a*col).sum()/a.sum())
    cp,cn,cq=centroid_col(p),centroid_col(n),centroid_col(q)
    return {"positive_wind_centroid_col":cp,
            "negative_wind_centroid_col":cn,
            "zero_wind_centroid_col":cq,
            "reversal_pass":cp>20.5 and cn<19.5,
            "no_advection_pass":abs(cq-20.0)<1e-4}
