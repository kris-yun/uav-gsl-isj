#!/usr/bin/env python3
"""Spatial posterior semantics and deterministic qualification utilities for PF-SNRE."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


def load_carrier_cells(carriers_path: Path):
    carriers = json.loads(Path(carriers_path).read_text(encoding="utf-8"))
    ids = []
    centroids = []
    prior = []
    cells = []
    ptr = [0]
    for c in carriers:
        ids.append(str(c["carrier_id"]))
        centroids.append([float(c["centroid_x"]), float(c["centroid_y"])])
        prior.append(float(c["prior_mass"]))
        if "free_cells" not in c:
            raise ValueError("final spatial metrics require exact free_cells=[[x,y],...] in carrier manifest")
        cc = np.asarray(c["free_cells"], dtype=np.float64)
        if cc.ndim != 2 or cc.shape[1] != 2 or len(cc) != int(c["free_count"]):
            raise ValueError(f"carrier {ids[-1]} free-cell geometry mismatch")
        mean = cc.mean(axis=0)
        if np.max(np.abs(mean - np.asarray(centroids[-1]))) > 1e-9:
            raise ValueError(f"carrier {ids[-1]} centroid is not exact free-cell mean")
        cells.append(cc)
        ptr.append(ptr[-1] + len(cc))
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate carrier IDs")
    prior = np.asarray(prior, dtype=np.float64)
    prior /= prior.sum()
    counts = np.diff(ptr).astype(np.float64)
    area = counts / counts.sum()
    if np.max(np.abs(prior - area)) > 1e-12:
        raise ValueError("q0 must be proportional to equal-area free-cell count")
    return (np.asarray(ids), np.asarray(centroids), prior,
            np.concatenate(cells, axis=0), np.asarray(ptr, dtype=np.int64))


def expand_region_mass_to_cells(region_mass, ptr):
    q = np.asarray(region_mass, dtype=np.float64)
    ptr = np.asarray(ptr, dtype=np.int64)
    if len(ptr) != len(q) + 1 or np.any(q < 0) or not np.isclose(q.sum(), 1.0, atol=1e-10):
        raise ValueError("invalid region posterior")
    out = np.empty(ptr[-1], dtype=np.float64)
    for s in range(len(q)):
        n = ptr[s + 1] - ptr[s]
        if n <= 0:
            raise ValueError("empty carrier")
        out[ptr[s]:ptr[s + 1]] = q[s] / n
    return out


def posterior_mean_xy(cell_mass, cells):
    p = np.asarray(cell_mass, dtype=np.float64)
    xy = np.asarray(cells, dtype=np.float64)
    if p.shape != (len(xy),) or np.any(p < 0) or not np.isclose(p.sum(), 1.0, atol=1e-10):
        raise ValueError("invalid cell posterior")
    return np.sum(p[:, None] * xy, axis=0)


def spatial_energy_score(cell_mass, cells, true_xy, distance_matrix=None):
    p = np.asarray(cell_mass, dtype=np.float64)
    xy = np.asarray(cells, dtype=np.float64)
    y = np.asarray(true_xy, dtype=np.float64)
    first = float(np.sum(p * np.linalg.norm(xy - y[None, :], axis=1)))
    if distance_matrix is None:
        d = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1)
    else:
        d = np.asarray(distance_matrix, dtype=np.float64)
        if d.shape != (len(xy), len(xy)):
            raise ValueError("distance matrix shape mismatch")
    second = 0.5 * float(p @ d @ p)
    return first - second


def hpd_cell_mask(cell_mass, level=0.9):
    p = np.asarray(cell_mass, dtype=np.float64)
    if not 0 < level < 1 or np.any(p < 0) or not np.isclose(p.sum(), 1.0, atol=1e-10):
        raise ValueError("invalid HPD input")
    order = np.argsort(-p, kind="stable")
    cum = np.cumsum(p[order])
    k = int(np.searchsorted(cum, level, side="left")) + 1
    mask = np.zeros(len(p), dtype=bool)
    mask[order[:k]] = True
    return mask


def mass_within_radius(cell_mass, cells, true_xy, radius_m):
    p = np.asarray(cell_mass, dtype=np.float64)
    xy = np.asarray(cells, dtype=np.float64)
    y = np.asarray(true_xy, dtype=np.float64)
    return float(p[np.linalg.norm(xy - y[None, :], axis=1) <= radius_m].sum())


def density_rank(log_ratio, target_source, ids):
    r = np.asarray(log_ratio, dtype=np.float64)
    ids = np.asarray(ids).astype(str)
    if r.shape != ids.shape:
        raise ValueError("rank shape mismatch")
    order = np.lexsort((ids, -r))
    return int(np.flatnonzero(order == int(target_source))[0]) + 1


def deterministic_kcenter(centroids, ids, k=32):
    """Geometry-only farthest-point panel, initialized by lexicographically smallest ID."""
    xy = np.asarray(centroids, dtype=np.float64)
    ids = np.asarray(ids).astype(str)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) != len(ids) or not 1 <= k <= len(ids):
        raise ValueError("invalid k-center input")
    first = int(np.argsort(ids, kind="stable")[0])
    selected = [first]
    min_d = np.linalg.norm(xy - xy[first], axis=1)
    min_d[first] = -np.inf
    while len(selected) < k:
        best_val = np.max(min_d)
        candidates = np.flatnonzero(np.isclose(min_d, best_val, rtol=0, atol=1e-12))
        pick = int(candidates[np.argmin(ids[candidates])])
        selected.append(pick)
        min_d = np.minimum(min_d, np.linalg.norm(xy - xy[pick], axis=1))
        min_d[selected] = -np.inf
    return np.asarray(selected, dtype=np.int64)


def precompute_distance_matrix(cells):
    xy = np.asarray(cells, dtype=np.float64)
    return np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1).astype(np.float32)
