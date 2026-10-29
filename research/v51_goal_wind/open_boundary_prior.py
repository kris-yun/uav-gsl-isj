"""Isolated patch helper for the V48 custom GMRF, not original PMFS.
Requires the existing flow geometry and its INTERNAL-only div definition.
Use in a cloned arm once; do not apply twice. Makes no data-driven claims.
"""
import numpy as np
from scipy.sparse import coo_matrix

def open_boundary_precision(flow, divergence_weight=1e4):
    N=flow.N;rr=[];cc=[];vv=[]
    for k,(a,b) in enumerate(flow.edges):
        ax=flow.axis[k];area=flow.area[k]
        for row,sign in [(a,1),(b,-1)]:
            rr.extend([row,row]);cc.extend([ax*N+a,ax*N+b]);vv.extend([sign*area/(2*flow.volume[row])]*2)
    D=coo_matrix((vv,(rr,cc)),shape=(N,3*N)).tocsr()
    B=coo_matrix(([sign*area/flow.volume[k] for k,ax,sign,area in flow.outlets],
                 ([k for k,ax,sign,area in flow.outlets],
                  [ax*N+k for k,ax,sign,area in flow.outlets])),shape=(N,3*N)).tocsr()
    new=(flow.Q+divergence_weight*((D+B).T@(D+B)-D.T@D)).tocsc()
    if not np.isfinite(new.data).all():raise ValueError('Invalid precision')
    return new
