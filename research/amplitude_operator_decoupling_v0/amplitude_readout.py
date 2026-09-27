"""Saved PMFS amplitude products -> explicit sampling operator -> archived B2.

This development interface does not read/write occurrence products or construct
posteriors. Values are cell-count proxies, not calibrated concentration in ppm.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import numpy as np

EPS = 1e-9  # Archived B2 contract, never selected on targets.


class Arm(str, Enum):
    U_NEAREST = 'u_nearest'
    U_FOOTPRINT = 'u_footprint'
    RAWU_NEAREST = 'rawu_nearest'
    RAWU_FOOTPRINT = 'rawu_footprint'

    @property
    def map_kind(self):
        return self.value.split('_')[0]

    @property
    def projection(self):
        return self.value.split('_')[1]


DEFAULT_ARM = Arm.RAWU_FOOTPRINT


def readonly(array):
    value = np.array(array, dtype=np.float64, copy=True)
    value.setflags(write=False)
    return value


@dataclass(frozen=True)
class ObservationOperator:
    name: str
    weights: np.ndarray

    def __post_init__(self):
        w = readonly(self.weights)
        if self.name not in ('nearest', 'footprint'):
            raise ValueError('Explicit nearest/footprint operator required')
        if w.ndim != 2 or not np.isfinite(w).all() or (w < 0).any():
            raise ValueError('Invalid projection weights')
        # Reject missing support. Do not redistribute mass onto in-map cells.
        if not np.allclose(w.sum(axis=1), 1., rtol=0., atol=1e-10):
            raise ValueError('Footprint outside map support; no renormalization')
        object.__setattr__(self, 'weights', w)

    def project(self, maps):
        m = np.asarray(maps, dtype=np.float64)
        if m.ndim != 2 or m.shape[1] != self.weights.shape[1]:
            raise ValueError('Expected candidate x row-major map cells')
        if not np.isfinite(m).all() or (m < 0).any():
            raise ValueError('Invalid amplitude maps')
        # Keep nearest's direct indexing, matching the archived arithmetic.
        if self.name == 'nearest':
            if not np.all((self.weights == 0) | (self.weights == 1)):
                raise ValueError('Nearest requires one-hot weights')
            return m[:, self.weights.argmax(axis=1)]
        return m @ self.weights.T


def rectangular_weights(metadata, centers, sizes):
    """Area-average piecewise-constant cells; no blur, occupancy mask, or rescale.

    Row sums explicitly retain lost outside-map area. ObservationOperator rejects
    such rows. Walls are not removed or renormalized. Flat order is x+width*y.
    """
    c = np.asarray(centers, dtype=np.float64)
    s = np.asarray(sizes, dtype=np.float64)
    if c.ndim != 2 or c.shape[1] != 2 or s.shape != c.shape:
        raise ValueError('centers/sizes must have shape (n,2)')
    if not np.isfinite(c).all() or not np.isfinite(s).all() or (s <= 0).any():
        raise ValueError('Finite centers and positive sizes required')
    nx, ny = int(metadata['width']), int(metadata['height'])
    a, ox, oy = (float(metadata[k]) for k in ('resolution', 'origin_x', 'origin_y'))
    if nx <= 0 or ny <= 0 or not np.isfinite([a, ox, oy]).all() or a <= 0:
        raise ValueError('Invalid map geometry')
    x, y = ox + np.arange(nx)*a, oy + np.arange(ny)*a
    rows = []
    for (cx, cy), (sx, sy) in zip(c, s):
        hx, hy = sx/2, sy/2
        wx = np.maximum(0, np.minimum(x+a, cx+hx)-np.maximum(x, cx-hx))
        wy = np.maximum(0, np.minimum(y+a, cy+hy)-np.maximum(y, cy-hy))
        rows.append((wy[:, None]*wx[None, :]/(4*hx*hy)).ravel())
    return np.array(rows)


def frozen_operators(metadata, probe_contract, probe_inputs):
    """Geometry only: derive native grid spacing from the frozen probe contract.

    No target, field, score, or source label is an input to this construction.
    """
    pc = probe_contract.sort_values('probe_rank')
    pi = probe_inputs.sort_values('probe_rank')
    if len(pc) != 30 or not np.array_equal(pc.probe_rank, pi.probe_rank):
        raise ValueError('Frozen 30-probe ordering mismatch')
    spacing = []
    for axis in ('x', 'y'):
        c = pc['center_'+axis+'_m'].to_numpy()
        i = (pc['native_'+axis+'0'].to_numpy()+pc['native_'+axis+'1_exclusive'].to_numpy())/2
        denom = np.dot(i-i.mean(), i-i.mean())
        if denom <= 0:
            raise ValueError('Unresolved native grid spacing')
        spacing.append(np.dot(c-c.mean(), i-i.mean())/denom)
    centers = pc[['center_x_m', 'center_y_m']].to_numpy()
    sizes = np.column_stack([
        (pc['native_'+axis+'1_exclusive']-pc['native_'+axis+'0']).to_numpy()*d
        for axis, d in zip(('x', 'y'), spacing)])
    w = rectangular_weights(metadata, centers, sizes)
    ncells = int(metadata['width'])*int(metadata['height'])
    idx = pi.cell_index.to_numpy(dtype=int)
    if (idx < 0).any() or (idx >= ncells).any():
        raise ValueError('Nearest cell outside map')
    nearest = np.zeros((len(idx), ncells))
    nearest[np.arange(len(idx)), idx] = 1.
    operators = {name: ObservationOperator(name, mat)
                 for name, mat in [('nearest', nearest), ('footprint', w)]}
    geometry = dict(native_spacing_m=spacing, footprint_sizes_m=sizes.tolist(),
                    centers_m=centers.tolist(), footprint_coverage=w.sum(axis=1).tolist(),
                    units='area-averaged cell count proxy; no cell-area conversion',
                    flat_order='x + width*y', outside_support_policy='reject')
    return operators, geometry


def load_saved_mean_maps(root: Path, environment: int, kind: str, cell_count: int):
    if kind not in ('u', 'rawu'):
        raise ValueError('Explicit u or rawu required; occurrence is a separate channel')
    maps = []
    for source in range(6):
        directory = root / f'forward/env_{environment}/source_{source}'
        expected = {f'state_{k}_replica_{r}.{kind}.f32' for k in range(11) for r in range(1, 9)}
        files = sorted(directory.glob(f'*.{kind}.f32'))
        if {f.name for f in files} != expected:
            raise ValueError('Frozen 11-state x 8-replica amplitude bank incomplete')
        stack = np.stack([np.fromfile(f, '<f4').astype(np.float64) for f in files])
        if stack.shape != (88, cell_count) or not np.isfinite(stack).all() or (stack < 0).any():
            raise ValueError('Invalid amplitude product shape/value')
        maps.append(stack.mean(axis=0))
    return readonly(maps)


@dataclass(frozen=True)
class AmplitudeTemplates:
    arm: Arm
    fields: np.ndarray
    values: np.ndarray

    @classmethod
    def prepare(cls, maps, operators, arm=DEFAULT_ARM):
        arm = Arm(arm)
        field = readonly(operators[arm.projection].project(maps[arm.map_kind]))
        # Exactly the archived B2 EPS and static -> 10-time template broadcast.
        pred = readonly(np.tile(np.maximum(field[:, None, :], EPS), (1, 10, 1)))
        return cls(arm, field, pred)

    def score(self, observed):
        # Preserve archived B2 arithmetic, including strict tie semantics.
        y = np.asarray(observed)
        if y.shape != self.values.shape[1:] or not np.isfinite(y).all():
            raise ValueError('Invalid target observation')
        pred = self.values
        norm = (pred*pred).sum(axis=(1, 2))
        gain = np.maximum(0, (pred*y[None]).sum(axis=(1, 2))/norm)
        sse = ((y[None]-gain[:, None, None]*pred)**2).sum(axis=(1, 2))
        return sse, gain


def ranking(sse, truth):
    sse = np.asarray(sse)
    if sse.ndim != 1 or not np.isfinite(sse).all() or not 0 <= truth < len(sse):
        raise ValueError('Invalid scores/truth index')
    rank = int(1+(sse < sse[truth]).sum())
    return rank, bool(rank == 1 and (sse == sse.min()).sum() == 1)
