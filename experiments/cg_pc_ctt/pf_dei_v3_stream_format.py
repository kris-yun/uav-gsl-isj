#!/usr/bin/env python3
"""Reader for the frozen PF-DEI V3 native trajectory-bank shard format."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np


MAGIC = b"PFV3STR1"
WIND_MAGIC = b"PFV3WND1"
UINT32 = struct.Struct("<I")


def read_multistream(path: str | Path) -> list[np.ndarray]:
    raw = Path(path).read_bytes()
    if len(raw) < len(MAGIC) + UINT32.size:
        raise ValueError("PF_DEI_V3_STREAM_TRUNCATED_HEADER")
    if raw[: len(MAGIC)] != MAGIC:
        raise ValueError("PF_DEI_V3_STREAM_BAD_MAGIC")

    offset = len(MAGIC)
    (count,) = UINT32.unpack_from(raw, offset)
    offset += UINT32.size
    if count == 0:
        raise ValueError("PF_DEI_V3_STREAM_EMPTY")
    header_end = offset + count * UINT32.size
    if header_end > len(raw):
        raise ValueError("PF_DEI_V3_STREAM_TRUNCATED_LENGTHS")

    lengths = struct.unpack_from(f"<{count}I", raw, offset)
    offset = header_end
    if any(length == 0 for length in lengths):
        raise ValueError("PF_DEI_V3_STREAM_ZERO_LENGTH_TRAJECTORY")
    expected = offset + sum(lengths) * np.dtype("<f4").itemsize
    if expected != len(raw):
        raise ValueError("PF_DEI_V3_STREAM_SIZE_MISMATCH")

    flat = np.frombuffer(raw, dtype="<f4", offset=offset)
    if not np.isfinite(flat).all() or (flat < 0).any():
        raise ValueError("PF_DEI_V3_STREAM_INVALID_PPM")
    trajectories: list[np.ndarray] = []
    start = 0
    for length in lengths:
        trajectories.append(flat[start : start + length].copy())
        start += length
    return trajectories


def write_multistream_for_test(path: str | Path, trajectories: list[np.ndarray]) -> None:
    """Test-only writer. Production shards are written only by native C++."""
    if not trajectories:
        raise ValueError("PF_DEI_V3_STREAM_EMPTY")
    arrays = [np.asarray(values, dtype="<f4") for values in trajectories]
    with Path(path).open("wb") as output:
        output.write(MAGIC)
        output.write(UINT32.pack(len(arrays)))
        output.write(struct.pack(f"<{len(arrays)}I", *(a.size for a in arrays)))
        for values in arrays:
            output.write(values.tobytes(order="C"))


def read_wind_multistream(path: str | Path) -> list[np.ndarray]:
    raw = Path(path).read_bytes()
    if len(raw) < len(WIND_MAGIC) + UINT32.size:
        raise ValueError("PF_DEI_V3_WIND_TRUNCATED_HEADER")
    if raw[: len(WIND_MAGIC)] != WIND_MAGIC:
        raise ValueError("PF_DEI_V3_WIND_BAD_MAGIC")
    offset = len(WIND_MAGIC)
    (count,) = UINT32.unpack_from(raw, offset)
    offset += UINT32.size
    if count == 0:
        raise ValueError("PF_DEI_V3_WIND_EMPTY")
    header_end = offset + count * UINT32.size
    if header_end > len(raw):
        raise ValueError("PF_DEI_V3_WIND_TRUNCATED_LENGTHS")
    lengths = struct.unpack_from(f"<{count}I", raw, offset)
    offset = header_end
    if any(length == 0 for length in lengths):
        raise ValueError("PF_DEI_V3_WIND_ZERO_LENGTH_TRAJECTORY")
    expected = offset + 3 * sum(lengths) * np.dtype("<f4").itemsize
    if expected != len(raw):
        raise ValueError("PF_DEI_V3_WIND_SIZE_MISMATCH")
    flat = np.frombuffer(raw, dtype="<f4", offset=offset)
    if not np.isfinite(flat).all():
        raise ValueError("PF_DEI_V3_WIND_NONFINITE")
    trajectories = []
    start = 0
    for length in lengths:
        size = 3 * length
        trajectories.append(flat[start : start + size].reshape(length, 3).copy())
        start += size
    return trajectories
