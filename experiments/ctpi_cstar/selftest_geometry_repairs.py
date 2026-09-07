"""Destructive checks for physical metrics, pixel identity and source curvature."""
import math
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
import torch

from common.map_geometry import load_map_info, world_cell
from m2_cpo.physical_prior import PhysicalPriorConfig, _cell
from m1_picr.model import PICRModel
from controlled_screen import load_data, inputs


def main():
    root = Path(__file__).resolve().parents[2]
    for h in ['H01','H02','H03']:
        path = root/'evidence/cstar_environment_20260906/maps_v1'/h
        w,ht,free,ox,oy,dx = load_map_info(path)
        # Independent decoder, ROS free_thresh=0.1, negate=0 in these assets.
        expected = (np.asarray(Image.open(path/'navigation_slice.pgm')) > 229.5)[::-1].flatten()
        assert np.array_equal(free,expected)
        cfg = PhysicalPriorConfig(w,ht,dx,.01,free,(ox,oy))
        for index in np.flatnonzero(expected):
            y,x = divmod(int(index),w)
            assert _cell(cfg,(ox+(x+.5)*dx,oy+(y+.5)*dx)) == index
    assert world_cell(-.001,.1,0,0,1) == (-1,0)
    assert world_cell(.99,.99,0,0,1) == (0,0)
    # Header whitespace must not consume a first pixel whose byte is 10.
    from validate_environment_alignment_v2 import read_pgm
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'pixel.pgm'
        p.write_bytes(b'P5\n2 1\n255\n'+bytes([10,255]))
        assert read_pgm(p)[3] == [10,255]
    for records in load_data(True).values():
        for r in records:
            ox,oy,sx,sy=r['geometry_bounds']
            recovered=r['candidates']*torch.tensor([sx,sy])+torch.tensor([ox,oy])
            assert torch.allclose(recovered,r['candidates_m'],atol=2e-6)
            nearest=r['candidates_m'][r['target']]
            assert abs(float(torch.linalg.vector_norm(nearest-torch.tensor(r['source_xy'])))-r['source_quantization_m'])<1e-6
    model=PICRModel(d_model=16,nhead=4,layers=1,z_source_dim=4,z_nuisance_dim=4,
                    coordinate_equivariant=True,radial_source_score=True)
    with torch.no_grad():
        model.location_head.weight.zero_(); model.location_head.bias.zero_()
    c=torch.tensor([[[0.,.5],[.5,.5],[1.,.5]]])
    z=torch.ones(1,4,requires_grad=True)
    logits=model.score_source(z,c)
    assert logits.argmax(-1).item()==1, 'INTERIOR_MODE_LOST'
    assert (logits[0,0]-2*logits[0,1]+logits[0,2]).item()<0, 'CURVATURE_CANCELLED'
    assert torch.equal(model.score_source(torch.zeros_like(z),c),torch.zeros(1,3))
    (-logits[0,1]+torch.logsumexp(logits,dim=-1)).backward()
    assert z.grad.abs().sum()>0
    model.radial_source_score=False
    legacy=model.score_source(z.detach(),c)
    assert torch.allclose(legacy,torch.zeros_like(legacy))
    print('CSTAR_GEOMETRY_REPAIRS_SELFTEST_PASS')


if __name__ == '__main__': main()
