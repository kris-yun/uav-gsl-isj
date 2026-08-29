#!/usr/bin/env python3
"""Direct physics-conditioned Set-NRE v2.

This version removes the historical-PMFS residual construction.  It learns a
candidate likelihood-ratio factor from a fixed source proposal independent of
the generated observation.  The final posterior uses only the geometry prior.

No temporal convolution, recurrence, Transformer, TrajCast, A0, temperature or
blend coefficient is used.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import numpy as np
import torch
from torch import nn

REFERENCE_PPM = 0.1
BLOCK_SAMPLES = 10
BLOCKS_PER_STOP = 8
SOURCE_UPDATE_STOP_STRIDE = 3

@dataclass(frozen=True)
class BlockLayout:
    sample_indices: np.ndarray
    stop_index: np.ndarray
    block_within_stop: np.ndarray
    stop_x: np.ndarray
    stop_y: np.ndarray
    available_updates: tuple[int, ...]
    def visible_blocks(self, update: int) -> int:
        if update not in self.available_updates:
            raise ValueError(f"source update {update} unavailable")
        return BLOCKS_PER_STOP * (1 + SOURCE_UPDATE_STOP_STRIDE * update)

def build_block_layout(x, y, stop_start, length: int) -> BlockLayout:
    x=np.asarray(x[:length],dtype=np.float64); y=np.asarray(y[:length],dtype=np.float64)
    starts=np.flatnonzero(np.asarray(stop_start[:length])>0.5)
    if len(starts)<4 or starts[0]!=0: raise ValueError("invalid physical-stop schedule")
    groups=[]; stop_ids=[]; within=[]; xs=[]; ys=[]; complete=0
    for stop_id,start in enumerate(starts):
        sx,sy=x[start],y[start]; end=int(start)
        while end<length and abs(x[end]-sx)<=1e-6 and abs(y[end]-sy)<=1e-6: end+=1
        stationary=np.arange(start,end,dtype=np.int64)
        if stationary.size < BLOCKS_PER_STOP*BLOCK_SAMPLES:
            if stop_id != len(starts)-1:
                raise ValueError(f"non-trailing stop {stop_id+1} incomplete")
            break
        used=stationary[-80:] if stop_id==0 else stationary[:80]
        for b in range(BLOCKS_PER_STOP):
            groups.append(used[b*10:(b+1)*10]); stop_ids.append(stop_id); within.append(b); xs.append(sx); ys.append(sy)
        complete+=1
    available=tuple(range(1,(complete-1)//SOURCE_UPDATE_STOP_STRIDE+1))
    if not available: raise ValueError("trajectory has no source-update prefix")
    return BlockLayout(np.stack(groups),np.asarray(stop_ids),np.asarray(within),np.asarray(xs,dtype=np.float32),np.asarray(ys,dtype=np.float32),available)

def log_measurement(values):
    v=np.asarray(values,dtype=np.float32)
    if np.any(v<0) or not np.all(np.isfinite(v)): raise ValueError("invalid measured ppm")
    return np.log1p(v/REFERENCE_PPM).astype(np.float32)

def candidate_features(carrier: dict, xy_center, xy_scale) -> np.ndarray:
    cx,cy=float(carrier["centroid_x"]),float(carrier["centroid_y"])
    # Deliberately excludes PMFS posterior and q0 prior mass.  This network learns
    # the likelihood factor; q0 is applied only after scoring.
    return np.asarray([
        (cx-xy_center[0])/xy_scale[0],
        (cy-xy_center[1])/xy_scale[1],
        float(carrier["width_m"])/xy_scale[0],
        float(carrier["height_m"])/xy_scale[1],
        math.log1p(float(carrier["free_count"]))/math.log(5.0),
    ],dtype=np.float32)

def block_context(layout: BlockLayout, visible: int, carrier: dict, xy_center, xy_scale) -> np.ndarray:
    cx,cy=float(carrier["centroid_x"]),float(carrier["centroid_y"])
    sx=layout.stop_x[:visible]; sy=layout.stop_y[:visible]
    max_stop=max(int(layout.stop_index[:visible].max()),1)
    return np.column_stack([
        (sx-xy_center[0])/xy_scale[0],(sy-xy_center[1])/xy_scale[1],
        (cx-sx)/xy_scale[0],(cy-sy)/xy_scale[1],
        2.0*layout.block_within_stop[:visible]/7.0-1.0,
        layout.stop_index[:visible]/max_stop,
    ]).astype(np.float32)

def masked_moments(x: torch.Tensor, mask: torch.Tensor, dim: int):
    m=mask.to(x.dtype)
    while m.ndim<x.ndim: m=m.unsqueeze(-1)
    count=m.sum(dim=dim).clamp_min(1.0); total=(x*m).sum(dim=dim); mean=total/count
    centered=(x-mean.unsqueeze(dim))*m; var=(centered*centered).sum(dim=dim)/count
    neg=torch.finfo(x.dtype).min; maximum=x.masked_fill(~m.bool(),neg).amax(dim=dim)
    sqrt_sum=total/torch.sqrt(count)
    return mean,maximum,torch.sqrt(var.clamp_min(0.0)+1e-8),sqrt_sum

class ConditionedDeepSetDirectNRE(nn.Module):
    def __init__(self,candidate_dim: int=5,block_context_dim: int=6,hidden: int=32):
        super().__init__(); self.candidate_dim=candidate_dim; self.block_context_dim=block_context_dim
        self.member_encoder=nn.Sequential(nn.Linear(40,hidden),nn.SiLU(),nn.Linear(hidden,hidden),nn.SiLU())
        self.block_encoder=nn.Sequential(nn.Linear(4*hidden+4+block_context_dim+candidate_dim,64),nn.SiLU(),nn.Linear(64,hidden),nn.SiLU())
        self.head=nn.Sequential(nn.Linear(4*hidden+1+candidate_dim,64),nn.SiLU(),nn.Linear(64,32),nn.SiLU(),nn.Linear(32,1))
    def forward(self,observation,prediction_set,block_context_tensor,candidate,block_mask,member_mask):
        obs=observation.unsqueeze(2).expand_as(prediction_set)
        member_input=torch.cat([obs,prediction_set,obs-prediction_set,torch.abs(obs-prediction_set)],dim=-1)
        encoded=self.member_encoder(member_input)
        mm=member_mask[:,None,:].expand(-1,prediction_set.shape[1],-1)
        member_pool=torch.cat(masked_moments(encoded,mm,dim=2),dim=-1)
        obs_mean=observation.mean(dim=-1,keepdim=True); obs_std=observation.std(dim=-1,correction=0,keepdim=True)
        obs_slope=(observation[...,-1:]-observation[...,:1])/9.0; obs_max=observation.amax(dim=-1,keepdim=True)
        cand=candidate[:,None,:].expand(-1,observation.shape[1],-1)
        block_input=torch.cat([member_pool,obs_mean,obs_std,obs_slope,obs_max,block_context_tensor,cand],dim=-1)
        block_encoded=self.block_encoder(block_input)
        block_pool=torch.cat(masked_moments(block_encoded,block_mask,dim=1),dim=-1)
        count=block_mask.sum(dim=1,keepdim=True).to(observation.dtype)
        return self.head(torch.cat([block_pool,torch.log1p(count),candidate],dim=-1)).squeeze(-1)

def direct_posterior(geometry_prior, log_likelihood_ratio):
    q=np.asarray(geometry_prior,dtype=np.float64); r=np.asarray(log_likelihood_ratio,dtype=np.float64)
    if q.shape!=r.shape or np.any(q<=0) or not np.all(np.isfinite(r)): raise ValueError("invalid direct posterior inputs")
    q=q/q.sum(); z=np.log(q)+r; z-=np.max(z); p=np.exp(z); return p/p.sum()

def sha256(path: Path) -> str:
    import hashlib
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
