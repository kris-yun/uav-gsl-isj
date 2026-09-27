"""Deterministic amplitude readout. No simulator, fitting, or probability calibration.

The returned exposure is a two-dimensional count-density proxy, NOT calibrated ppm.
`scale_profile_sse` reproduces the archived B2 rule; its scores are NOT posteriors.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np


def mean_count_maps(root: Path, environment: int, source: int, kind: str) -> np.ndarray:
    if kind not in {'rawu','u'}:
        raise ValueError('kind must be rawu or u')
    directory = root / f'forward/env_{environment}/source_{source}'
    files = sorted(directory.glob(f'*.{kind}.f32'))
    if len(files) != 88:
        raise ValueError(f'Expected the frozen 11 x 8 maps, found {len(files)}')
    arrays = [np.fromfile(f,dtype='<f4').astype(np.float64) for f in files]
    stack=np.stack(arrays)
    if not np.isfinite(stack).all() or (stack<0).any():
        raise ValueError('Invalid count map')
    return stack.mean(axis=0)


def rectangular_average_matrix(metadata: dict, centers: np.ndarray,
                               sizes: np.ndarray) -> np.ndarray:
    """Piecewise-constant cell-field -> area-average over a rectangular footprint.

    No wall renormalization and no extra blur. Reports outside-domain support by
    row sums below one; callers must inspect it rather than silently renormalize.
    To convert cell counts to areal density, divide input by cell area first.
    """
    c=np.asarray(centers,dtype=np.float64);s=np.asarray(sizes,dtype=np.float64)
    if c.ndim!=2 or c.shape[1]!=2 or s.shape!=c.shape or (s<=0).any():
        raise ValueError('centers and positive sizes must have shape (n,2)')
    nx,ny=int(metadata['width']),int(metadata['height'])
    delta=float(metadata['resolution']);ox=float(metadata['origin_x']);oy=float(metadata['origin_y'])
    x=ox+np.arange(nx)*delta;y=oy+np.arange(ny)*delta
    rows=[]
    for (cx,cy),(sx,sy) in zip(c,s):
        wx=np.maximum(0,np.minimum(x+delta,cx+sx/2)-np.maximum(x,cx-sx/2))
        wy=np.maximum(0,np.minimum(y+delta,cy+sy/2)-np.maximum(y,cy-sy/2))
        rows.append((wy[:,None]*wx[None,:]/(sx*sy)).ravel())
    return np.array(rows)


def scale_profile_sse(observed: np.ndarray, templates: np.ndarray,
                      archived_epsilon: float = 1e-9) -> tuple[np.ndarray,np.ndarray]:
    """One shared functional rule for all candidates, one positive gain per fit.

    archived_epsilon reproduces B2's existing template clip. It is NOT tuned here.
    Templates have shape (candidate, *observed.shape).
    """
    y=np.asarray(observed,dtype=np.float64)
    f=np.asarray(templates,dtype=np.float64)
    if f.shape[1:]!=y.shape or not np.isfinite(y).all() or not np.isfinite(f).all():
        raise ValueError('Nonfinite values or mismatched shapes')
    if (f<0).any() or archived_epsilon<0:
        raise ValueError('Negative template or epsilon')
    f=np.maximum(f,archived_epsilon).reshape(len(f),-1);y=y.ravel()
    denom=np.einsum('ij,ij->i',f,f)
    gain=np.divide(f@y,denom,out=np.zeros(len(f)),where=denom>0)
    gain=np.maximum(gain,0)
    residual=y[None,:]-gain[:,None]*f
    return np.einsum('ij,ij->i',residual,residual),gain


def ranks_and_unique_top1(sse: np.ndarray, true_index: int) -> tuple[int,bool]:
    score=np.asarray(sse,float)
    if not np.isfinite(score).all():raise ValueError('Nonfinite SSE')
    rank=int(1+(score<score[true_index]).sum())
    return rank, bool(rank==1 and np.sum(score==score.min())==1)
