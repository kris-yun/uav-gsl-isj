#!/usr/bin/env python3
"""Ordered occupancy I/O for frozen CTT V13 truth-free trace banks.

This module exposes the time axis that ctt_bank_io.read_trace_fields() reduces
to a mean hit frequency. Binary layout is unchanged:
  <7Q> header
  activeFilamentCounts[T] uint32
  firstHitBins[cell_count] int32
  occupancyWords[T,words_per_step] uint64
"""
from __future__ import annotations

import struct
from pathlib import Path
import numpy as np

MAGIC = 0x32564B4E42545443
HEADER = struct.Struct("<7Q")
VERSION = 1


def _read_header(handle, path, expected_carrier=None, expected_member=None):
    raw = handle.read(HEADER.size)
    if len(raw) != HEADER.size:
        raise ValueError(f"short header: {path}")
    magic, version, carrier, member, timesteps, cell_count, words = HEADER.unpack(raw)
    if magic != MAGIC or version != VERSION or timesteps < 1:
        raise ValueError(f"contract mismatch: {path}")
    if words != (cell_count + 63) // 64:
        raise ValueError(f"word-count mismatch: {path}")
    if expected_carrier is not None and int(carrier) != int(expected_carrier):
        raise ValueError("carrier header mismatch")
    if expected_member is not None and int(member) != int(expected_member):
        raise ValueError("member header mismatch")
    return int(carrier), int(member), int(timesteps), int(cell_count), int(words)


def read_selected_occupancy(path: Path, selected_cells, expected_carrier=None,
                            expected_member=None):
    """Return ordered binary occupancy [T,D] at selected global cell indices."""
    path = Path(path)
    with path.open("rb") as handle:
        carrier, member, T, C, W = _read_header(handle, path, expected_carrier, expected_member)
        handle.seek(HEADER.size + 4 * T + 4 * C)
        raw = handle.read(8 * T * W)
        if len(raw) != 8 * T * W:
            raise ValueError(f"short occupancy payload: {path}")
    occ = np.frombuffer(raw, dtype="<u8").reshape(T, W)
    idx = np.asarray(selected_cells, dtype=np.int64).reshape(-1)
    if len(idx) < 1 or np.any(idx < 0) or np.any(idx >= C):
        raise ValueError("selected cell out of range")
    words = idx // 64
    bits = (idx % 64).astype(np.uint64, copy=False)
    out = ((occ[:, words] >> bits[None, :]) & np.uint64(1)).astype(np.uint8)
    return out, {"carrier": carrier, "member": member, "timesteps": T,
                 "cell_count": C, "words_per_step": W}


def occupancy_frequency(ordered_occupancy):
    x = np.asarray(ordered_occupancy)
    if x.ndim != 2 or not np.all((x == 0) | (x == 1)):
        raise ValueError("ordered_occupancy must be binary [T,D]")
    return x.mean(axis=0, dtype=np.float64).astype(np.float32)
