"""Only static public obstacles, ROI and vehicle limits are loaded here.

No native gas frame, source label, ideal gas query or full wind array is read.
Closed-voxel collision and AGL definitions match the released S2 agent.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np


class PublicGeometry:
    def __init__(self, dataset_root):
        root = Path(dataset_root)
        config = json.loads((root / "assets/geometry.json").read_text())
        meta = json.loads((root / "dataset.json").read_text())
        self.origin = np.array(config["origin_ENU_m"], float)
        self.shape = np.array(config["shape_xyz"], int)
        self.h = float(config["cell_size_m"])
        nx, ny, nz = self.shape
        self.cells = np.memmap(root / "assets/obstacles.bin", mode="r", dtype="u1", shape=(nz, ny, nx))
        self.roi = np.array(meta["observation_ROI_ENU_m"], float)
        self.agl_range = tuple(meta["vehicle"]["AGL_range_m"])
        self._ground_cache = {}

    def indices(self, positions):
        p = np.asarray(positions, float).reshape(-1, 3)
        if not np.isfinite(p).all():
            raise ValueError("NONFINITE_POSITION")
        return np.floor((p-self.origin)/self.h).astype(int)

    def valid(self, positions):
        p = np.asarray(positions, float).reshape(-1, 3)
        indices = self.indices(p)
        good = ((indices >= 0) & (indices < self.shape)).all(axis=1)
        inside = indices[good]
        good[good] = self.cells[inside[:, 2], inside[:, 1], inside[:, 0]] == 0
        return good

    def ground(self, positions):
        output = []
        for x, y, _ in self.indices(positions):
            key = int(x), int(y)
            if not (0 <= x < self.shape[0] and 0 <= y < self.shape[1]):
                raise ValueError("OUTSIDE_XY")
            if key not in self._ground_cache:
                solid = np.flatnonzero(self.cells[:, y, x] == 1)
                self._ground_cache[key] = self.origin[2] + (int(solid[-1])+1)*self.h if len(solid) else self.origin[2]
            output.append(self._ground_cache[key])
        return np.asarray(output)

    def valid_uav(self, positions):
        p = np.asarray(positions, float).reshape(-1, 3)
        if not ((p >= self.roi[0]) & (p < self.roi[1])).all():
            return False
        if not self.valid(p).all():
            return False
        agl = p[:, 2]-self.ground(p)
        return bool(((agl >= self.agl_range[0]) & (agl <= self.agl_range[1])).all())

    @staticmethod
    def _segment_box(a, delta, cell):
        lo, hi = np.float32(0), np.float32(1)
        for k in range(3):
            lower = np.float32(cell[k]); upper = np.float32(lower+1)
            if delta[k] == 0:
                if a[k] < lower or a[k] > upper:
                    return False
            else:
                u = np.float32((lower-a[k])/delta[k]); v = np.float32((upper-a[k])/delta[k])
                if u > v:
                    u, v = v, u
                lo, hi = max(lo, u), min(hi, v)
                if lo > hi:
                    return False
        return True

    def segment_legal(self, start, end):
        # This helper is intentionally limited to short motion commands.
        start = np.asarray(start, dtype="<f4"); end = np.asarray(end, dtype="<f4")
        if not self.valid_uav([start, end]):
            return False
        a = np.asarray((start-self.origin.astype("<f4"))/np.float32(self.h), dtype="<f4")
        b = np.asarray((end-self.origin.astype("<f4"))/np.float32(self.h), dtype="<f4")
        delta = b-a
        low = np.maximum(0, np.minimum(np.floor(a), np.floor(b)).astype(int)-1)
        high = np.minimum(self.shape-1, np.maximum(np.floor(a), np.floor(b)).astype(int)+1)
        for z in range(low[2], high[2]+1):
            for y in range(low[1], high[1]+1):
                for x in range(low[0], high[0]+1):
                    if self.cells[z, y, x] != 0 and self._segment_box(a, delta, [x, y, z]):
                        return False
        # Check every crossed XY column plus both adjacent sides, as in AgentSession.
        ts = [0., 1.]
        for k in [0, 1]:
            if abs(end[k]-start[k]) < 1e-12:
                continue
            lower, upper = sorted([float(start[k]), float(end[k])])
            for i in range(math.floor((lower-self.origin[k])/self.h)+1,
                           math.floor((upper-self.origin[k])/self.h)+1):
                t = (self.origin[k]+self.h*i-start[k])/(end[k]-start[k])
                if 0 < t < 1:
                    ts += [max(0, t-1e-8), t, min(1, t+1e-8)]
        ts = sorted(set(ts))
        ts += [(u+v)/2 for u, v in zip(ts, ts[1:])]
        return self.valid_uav([start+(end-start)*t for t in ts])
