"""Export a two-dimensional candidate-cell probability mass map."""
from pathlib import Path
import json
import numpy as np


def export_source_map(source_xy,probabilities,path):
    xy=np.asarray(source_xy,dtype=float);p=np.asarray(probabilities,dtype=float)
    if xy.shape!=(len(p),2) or not np.isfinite(xy).all() or not np.isfinite(p).all() or np.any(p<0) or not np.isclose(p.sum(),1):
        raise ValueError('finite source coordinates and normalized probability masses required')
    xs=np.unique(xy[:,0]);ys=np.unique(xy[:,1]);mass=np.zeros((len(ys),len(xs)));legal=np.zeros_like(mass,dtype=bool)
    for point,value in zip(xy,p):
        ix=int(np.searchsorted(xs,point[0]));iy=int(np.searchsorted(ys,point[1]))
        mass[iy,ix]+=value;legal[iy,ix]=True
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(target,x_m=xs,y_m=ys,probability_mass=mass,legal_source_mask=legal,
                        metadata_json=np.array(json.dumps({'normalization':'sum over legal candidate cells = 1',
                            'interpolated':False,'z_marginalization':'candidate ids at the same xy are summed',
                            'not_a_continuous_area_density':True})))
    return mass,legal
