"""Map-only GADEN ASCII occupancy adapter; no gas/source/wind truth loading.

File order: z layers separated by ';', x rows, y columns.
Storage: cells[z,y,x], canonical flat index x+nx*y+nx*ny*z.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class Occupancy3D:
    minimum: tuple
    maximum: tuple
    dimensions: tuple
    cell_size: float
    cells: np.ndarray
    sha256: str

    @classmethod
    def read(cls, path):
        raw = Path(path).read_bytes()
        lines = raw.decode('utf-8').splitlines()
        meta = {}
        for line in lines[:4]:
            key, *values = line.split()
            meta[key.split('(')[0]] = values
        lo, hi = (tuple(map(float,meta[k])) for k in ('#env_min','#env_max'))
        dims = tuple(map(int,meta['#num_cells']))
        cell = float(meta['#cell_size'][0])
        if (len(lo)!=3 or len(hi)!=3 or len(dims)!=3 or min(dims)<=0
                or not np.isfinite(lo+hi+(cell,)).all() or cell<=0 or any(b<=a for a,b in zip(lo,hi))):
            raise ValueError('M1_MAP_HEADER')
        # Historical headers need not equal origin+dimensions*cell exactly:
        # the last voxel may cover a partial physical interval.
        if any(abs((b-a)-n*cell) > cell for a,b,n in zip(lo,hi,dims)):
            raise ValueError('M1_MAP_EXTENT')
        layers, rows = [], []
        for line in lines[4:]:
            if not line.strip():
                continue
            if line.strip() == ';':
                if not rows:
                    raise ValueError('M1_MAP_EMPTY_LAYER')
                layers.append(rows)
                rows = []
            else:
                values = list(map(int,line.split()))
                if len(values)!=dims[1] or any(v not in (0,1,2) for v in values):
                    raise ValueError('M1_MAP_ROW')
                rows.append(values)
        if rows:
            layers.append(rows)
        if len(layers)!=dims[2] or any(len(layer)!=dims[0] for layer in layers):
            raise ValueError('M1_MAP_LAYOUT')
        cells = np.ascontiguousarray(np.asarray(layers,dtype=np.uint8).transpose(0,2,1))
        cells.flags.writeable = False
        return cls(lo,hi,dims,cell,cells,hashlib.sha256(raw).hexdigest())

    def index(self, point):
        if len(point)!=3 or not np.isfinite(point).all():
            raise ValueError('M1_MAP_POINT')
        # Same float32 coordinate convention as the existing audited reader.
        with np.errstate(over='ignore',invalid='ignore'):
            scaled = (np.asarray(point,dtype=np.float32)-np.asarray(self.minimum,dtype=np.float32))/np.float32(self.cell_size)
        if not np.isfinite(scaled).all():
            return None
        idx = tuple(int(v) for v in np.floor(scaled))
        return idx if all(0<=v<n for v,n in zip(idx,self.dimensions)) else None

    def state(self, point):
        idx = self.index(point)
        if idx is None:
            return 3
        x,y,z = idx
        return int(self.cells[z,y,x])

    def is_free(self, point):
        return self.state(point)==0
