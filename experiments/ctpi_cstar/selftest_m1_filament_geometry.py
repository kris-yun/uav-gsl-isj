import numpy as np
from m1_causal.occupancy3d import Occupancy3D
from m1_causal.filament_geometry import FilamentGeometry

def main():
    cells=np.zeros((3,5,5),dtype=np.uint8)
    cells[:,:,2]=1
    cells[1,4,1]=2
    m=Occupancy3D((0,0,0),(5,5,3),(5,5,3),1,cells,'synthetic')
    g=FilamentGeometry(m)
    assert g.visible((.5,.5,1.5),(1.5,.5,1.5))
    assert not g.visible((.5,.5,1.5),(3.5,.5,1.5))
    assert g.visible((.5,.5,1.5),(.5,.5,1.5))
    q=g.step_boundary((1.5,.5,1.5),(3.5,.8,1.5))
    assert m.is_free(q) and q[0]<2 and q[1]>.5
    assert g.step_boundary((1.5,3.5,1.5),(1.5,4.5,1.5)) is None
    q=g.step_boundary((.5,.5,1.5),(-2,.5,1.5))
    assert m.is_free(q)
    try: g.step_boundary((2.5,.5,1.5),(1.5,.5,1.5))
    except ValueError: pass
    else: raise AssertionError('obstacle start accepted')
    print('M1_FILAMENT_GEOMETRY_SELFTEST_PASS')
if __name__=='__main__': main()
