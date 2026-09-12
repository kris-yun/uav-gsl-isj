"""Strict chronological ingress for native GMRF diagnostic field exports.

Planar extrusion is an explicit model hypothesis, NOT validated 3-D transport.
No source/gas/true-wind loader belongs in this module.
"""
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import numpy as np
from .filament_transport import WindSnapshot


@dataclass(frozen=True)
class EstimatedWindHistory:
    times: np.ndarray
    centres: np.ndarray
    velocities: np.ndarray
    origin_xy: tuple
    cell_size: float
    indices: dict
    sha256: str

    @classmethod
    def read(cls, path, *, origin_xy, cell_size, expected_end_s):
        if len(origin_xy)!=2 or not np.isfinite((*origin_xy,cell_size,expected_end_s)).all() or cell_size<=0:
            raise ValueError('M1_WIND_GEOMETRY')
        raw=Path(path).read_bytes()
        import io
        rows=np.loadtxt(io.BytesIO(raw),ndmin=2)
        if rows.shape[1]!=5 or len(rows)==0 or not np.isfinite(rows).all():
            raise ValueError('M1_WIND_ROWS')
        times,starts,counts=np.unique(rows[:,0],return_index=True,return_counts=True)
        if times[0]<=0 or times[-1]!=expected_end_s or np.any(np.diff(rows[:,0])<0) or len(set(counts))!=1:
            raise ValueError('M1_WIND_INCOMPLETE_OR_CLOCK')
        n=int(counts[0]); centres=rows[:n,1:3].copy()
        blocks=rows.reshape(len(times),n,5)
        if not np.array_equal(blocks[:,:,1:3],np.broadcast_to(centres,blocks[:,:,1:3].shape)):
            raise ValueError('M1_WIND_SUPPORT_CHANGED')
        scaled=(centres-np.asarray(origin_xy))/cell_size-.5
        keys=np.rint(scaled).astype(int)
        if np.max(np.abs(scaled-keys))>1e-4 or np.any(keys<0):
            raise ValueError('M1_WIND_CENTRE_ALIGNMENT')
        indices={tuple(k):i for i,k in enumerate(keys)}
        if len(indices)!=n: raise ValueError('M1_WIND_DUPLICATE_CELL')
        velocities=blocks[:,:,3:5].copy()
        for a in (times,centres,velocities): a.flags.writeable=False
        return cls(times,centres,velocities,tuple(origin_xy),cell_size,indices,hashlib.sha256(raw).hexdigest())

    def snapshot_at(self, time_s, *, vertical_model, initial_velocity_m_s):
        """At t only fields available <=t are used, never backward-smoothed.

        Before the first solve use a separately declared constant prior. The
        caller must report this prior and planar closure in its manifest.
        Missing horizontal support fails closed, not nearest-free snapping.
        """
        if vertical_model!='planar_extrusion_zero_vertical':
            raise ValueError('M1_WIND_VERTICAL_MODEL_REQUIRED')
        if not math.isfinite(time_s) or time_s<0:
            raise ValueError('M1_WIND_QUERY_TIME')
        if len(initial_velocity_m_s)!=3 or not np.isfinite(initial_velocity_m_s).all() or initial_velocity_m_s[2]!=0:
            raise ValueError('M1_WIND_INITIAL_PRIOR_REQUIRED')
        idx=int(np.searchsorted(self.times,time_s,side='right'))-1
        def velocity(point):
            if len(point)!=3 or not np.isfinite(point).all():
                raise ValueError('M1_WIND_QUERY_POINT')
            # Same float32 mapping as Occupancy3D and native environment.
            # Mixed float64 indexing can select the opposite side of a wall.
            key=tuple(np.floor((np.asarray(point[:2],dtype=np.float32)-np.asarray(self.origin_xy,dtype=np.float32))/np.float32(self.cell_size)).astype(int))
            if key not in self.indices:
                raise ValueError(f'M1_WIND_UNSUPPORTED_HORIZONTAL_CELL point={tuple(float(v) for v in point)} cell={tuple(int(v) for v in key)} field_s={0.0 if idx<0 else float(self.times[idx])}')
            if idx<0: return tuple(initial_velocity_m_s)
            uv=self.velocities[idx,self.indices[key]]
            return float(uv[0]),float(uv[1]),0.0
        return WindSnapshot(0.0 if idx<0 else float(self.times[idx]),velocity)
