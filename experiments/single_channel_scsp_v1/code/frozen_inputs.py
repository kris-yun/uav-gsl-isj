"""Load the frozen fixed-support input set for the GW-MAIN offline gate.

Inputs per update snapshot:
  - snapshot dir (/home/zyc/m0v3_snapshots/<HOUSE>_UPDATE_<k>)
  - trace-replay candidate package (/home/zyc/m1_final/<HOUSE>_UPDATE_<k>)
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class FrozenUpdate:
    house: str
    update_id: int
    grid_x: int
    grid_y: int
    cell_size: float
    origin: tuple
    occupancy: np.ndarray  # bool, free=True, length N
    measured: np.ndarray  # HitProbability raw fields, length N
    measured_prob: np.ndarray  # probability()
    measured_conf: np.ndarray
    prior: np.ndarray  # length N
    posterior_official: np.ndarray
    internal_official: np.ndarray
    settings: dict
    candidates: list = field(default_factory=list)  # dicts with rect + map
    maps: np.ndarray = None  # (C, N) float32
    simulated: np.ndarray = None  # (C, N) float64 recomputed sim maps (same as maps)

    @property
    def n_cells(self) -> int:
        return len(self.occupancy)

    @property
    def free(self) -> np.ndarray:
        return self.occupancy


def _read_vec(path: Path, dtype, count=None):
    data = path.read_bytes()
    n = struct.unpack("<Q", data[:8])[0]
    if count is not None and n != count:
        raise ValueError(f"count mismatch {path}: {n} != {count}")
    arr = np.frombuffer(data, dtype=dtype, offset=8, count=n)
    return arr.copy()


def log_odds_to_prob(l):
    return 1.0 - 1.0 / (1.0 + np.exp(l))


def load_update(snap_dir: str, candidate_dir: str) -> FrozenUpdate:
    snap = Path(snap_dir)
    cand = Path(candidate_dir)
    meta = json.loads((snap / "snapshot_meta.json").read_text())
    occ = (snap / "occupancy.bin").read_bytes()
    occ = np.frombuffer(occ, dtype=np.uint8).astype(bool)
    measured = _read_vec(snap / "measured_state_before.bin", np.dtype(
        [("logOdds", "<f8"), ("auxWeight", "<f8"),
         ("dirx", "<f4"), ("diry", "<f4"),
         ("omega", "<f8"), ("confidence", "<f8"),
         ("distance", "<f8")]))
    prior = _read_vec(snap / "source_probability_before.bin", "<f8")
    post = _read_vec(snap / "source_probability_after.bin", "<f8")
    internal = _read_vec(snap / "source_probability_internal_after.bin", "<f8")
    settings = json.loads((snap / "settings.json").read_text())
    ct = json.loads((cand / "candidate_trace.json").read_text())
    n = ct["cell_count"]
    maps_bytes = (cand / "candidate_maps.f32").read_bytes()
    maps = np.frombuffer(maps_bytes, dtype="<f4").reshape(-1, n).astype(np.float64)
    candidates = []
    for i, c in enumerate(ct["candidates"]):
        candidates.append({
            "id": c["candidate_id"],
            "origin": (c["origin_x"], c["origin_y"]),
            "size": (c["size_x"], c["size_y"]),
            "valid": c["valid"],
            "source_prob": c["source_prob"],
            "map": maps[i],
        })
    fu = FrozenUpdate(
        house=meta["house"], update_id=meta["update_id"],
        grid_x=meta["grid_x"], grid_y=meta["grid_y"],
        cell_size=meta["cell_size"], origin=(meta["origin_x"], meta["origin_y"]),
        occupancy=occ, measured=measured,
        measured_prob=log_odds_to_prob(measured["logOdds"]),
        measured_conf=measured["confidence"],
        prior=prior, posterior_official=post, internal_official=internal, settings=settings,
        candidates=candidates, maps=maps,
    )
    return fu


def candidate_response(fu: FrozenUpdate) -> np.ndarray:
    """(C, N) simulated hit maps on the frozen support."""
    return fu.maps


def source_contrast(fu: FrozenUpdate, conf_threshold: float = 1e-9):
    """Prior-weighted source contrast matrix D (only high-confidence cells)."""
    g = candidate_response(fu)
    conf = fu.measured_conf
    keep = conf > conf_threshold
    pi = fu.prior
    gbar = np.einsum("s,sc->c", pi, g)
    d = g - gbar  # (C, N)
    return d[:, keep], keep
