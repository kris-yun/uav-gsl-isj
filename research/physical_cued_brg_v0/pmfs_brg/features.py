"""Fixed, unit-aware feature map: no per-domain fitted z-score, no batch statistics."""
import numpy as np
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class FeatureConfig:
    concentration_unit_ppm: float = 1.0
    count_unit: float = 1.0
    geometry_unit_m: float = 10.0
    hit_threshold_ppm: float = 0.0
    def __post_init__(self):
        if min(self.concentration_unit_ppm,self.count_unit,self.geometry_unit_m)<=0:
            raise ValueError("positive feature units required")
        if self.hit_threshold_ppm < 0: raise ValueError("negative threshold")

def encode(concentrations, positions, source_positions, p, rawu, cfg=FeatureConfig()):
    """T observations, S sources, p/rawu shape[T,S]. No source labels as inputs.

    rawu remains an area-averaged cell-count proxy, NOT claimed to be ppm.
    Two monotone magnitude channels keep magnitude; no trajectory normalization.
    The first model does not use time intervals or wind measurements as learned
    features: those fields are still logged in the runtime contract.
    """
    c=np.asarray(concentrations,dtype=np.float64); x=np.asarray(positions,dtype=np.float64)
    s=np.asarray(source_positions,dtype=np.float64); p=np.asarray(p,dtype=np.float64)
    u=np.asarray(rawu,dtype=np.float64)
    if c.ndim!=1 or x.shape!=(len(c),2) or s.ndim!=2 or s.shape[1]!=2 or p.shape!=(len(c),len(s)) or u.shape!=p.shape:
        raise ValueError("feature shape mismatch")
    if any(not np.isfinite(v).all() for v in [c,x,s,p,u]) or (c<0).any() or (u<0).any() or ((p<0)|(p>1)).any():
        raise ValueError("invalid physical input")
    a=c/cfg.concentration_unit_ppm; b=u/cfg.count_unit
    obs=np.stack((np.log1p(a)/8,a/(1+a),(c>cfg.hit_threshold_ppm).astype(float)),-1)
    d=(x[:,None,:]-s[None,:,:])/cfg.geometry_unit_m
    cues=np.concatenate((p[...,None],(np.log1p(b)/8)[...,None],(b/(1+b))[...,None],d,np.linalg.norm(d,axis=-1)[...,None]),-1)
    obs=obs.astype('float32');cues=cues.astype('float32')
    if not np.isfinite(obs).all() or not np.isfinite(cues).all(): raise ValueError("feature overflow")
    return obs,cues
