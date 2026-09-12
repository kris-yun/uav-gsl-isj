"""Map-bound reference of inspected GADEN filament geometry (not UAV planning).

Uses native sample-spacing/slide laws, not exact ray tracing or float parity.
The algorithm can miss corner intersections between samples; do not interpret
this as collision certification. No silent empty-map fallback is permitted.
"""
import math
import numpy as np
from .occupancy3d import Occupancy3D


class FilamentGeometry:
    def __init__(self, grid: Occupancy3D):
        self.grid=grid

    def visible(self, start, end):
        if not self.grid.is_free(start) or not self.grid.is_free(end): return False
        a,b=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
        distance=float(np.linalg.norm(b-a))
        steps=int(distance/self.grid.cell_size)
        # Native loop has no interior samples in these cases; avoid 0/0.
        if steps<=1: return True
        return all(self.grid.is_free(a+(b-a)*(i/steps)) for i in range(1,steps))

    def step_boundary(self, start, end):
        if not self.grid.is_free(start): raise ValueError('M1_BOUNDARY_START_NOT_FREE')
        a,b=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
        if b.shape!=(3,) or not np.isfinite(b).all(): raise ValueError('M1_BOUNDARY_ENDPOINT')
        return self._slide(a,b,0)

    def _raw_index(self, p):
        return np.floor((np.asarray(p,dtype=np.float32)-np.asarray(self.grid.minimum,dtype=np.float32))/np.float32(self.grid.cell_size)).astype(int)

    def _slide(self, a, b, depth):
        if depth>=32: raise ValueError('M1_BOUNDARY_SLIDE_NOT_CONVERGED')
        if np.array_equal(self._raw_index(a),self._raw_index(b)): return tuple(b)
        distance=float(np.linalg.norm(b-a))
        if distance==0: return tuple(a)
        steps=math.ceil(distance/self.grid.cell_size)
        increment=(b-a)/steps
        current=a.copy()
        for _ in range(steps):
            previous=current.copy(); current+=increment
            state=self.grid.state(current)
            if state==2: return None
            if state in (1,3):
                normal=self._raw_index(previous)-self._raw_index(current)
                norm2=float(normal@normal)
                if norm2==0: raise ValueError('M1_BOUNDARY_ZERO_NORMAL')
                remaining=b-previous
                tangential=remaining-normal*(float(remaining@normal)/norm2)
                return self._slide(previous,previous+tangential,depth+1)
        return tuple(current)
