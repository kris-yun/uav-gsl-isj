#!/usr/bin/env python3
"""Strict readers and native sensor transform for the frozen H01 CTT bank."""

from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

import numpy as np


STREAM_MAGIC = b"PFV3STR1"
WIND_MAGIC = b"PFV3WND1"
U32 = struct.Struct("<I")
DT_S = 0.2
SENSOR_TAU_S = 1.2
SENSOR_DEAD_S = 0.4
FIRST_PASSAGE_THRESHOLD_PPM = 0.1
STOP_SAMPLES = 80


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: str | Path, magic: bytes, width: int) -> list[np.ndarray]:
    raw = Path(path).read_bytes()
    if len(raw) < 12 or raw[:8] != magic:
        raise ValueError(f"CTT_H01_BANK_BAD_MAGIC:{path}")
    (count,) = U32.unpack_from(raw, 8)
    if count == 0:
        raise ValueError(f"CTT_H01_BANK_EMPTY:{path}")
    offset = 12
    end = offset + 4 * count
    if end > len(raw):
        raise ValueError(f"CTT_H01_BANK_TRUNCATED_LENGTHS:{path}")
    lengths = struct.unpack_from(f"<{count}I", raw, offset)
    if any(length == 0 for length in lengths):
        raise ValueError(f"CTT_H01_BANK_ZERO_LENGTH:{path}")
    expected = end + 4 * width * sum(lengths)
    if expected != len(raw):
        raise ValueError(f"CTT_H01_BANK_SIZE_MISMATCH:{path}:{len(raw)}:{expected}")
    flat = np.frombuffer(raw, dtype="<f4", offset=end)
    if not np.isfinite(flat).all():
        raise ValueError(f"CTT_H01_BANK_NONFINITE:{path}")
    if magic == STREAM_MAGIC and (flat < 0).any():
        raise ValueError(f"CTT_H01_BANK_NEGATIVE_PPM:{path}")
    result: list[np.ndarray] = []
    start = 0
    for length in lengths:
        size = width * length
        values = flat[start : start + size].copy()
        result.append(values if width == 1 else values.reshape(length, width))
        start += size
    return result


def read_physical(path: str | Path) -> list[np.ndarray]:
    return _read(path, STREAM_MAGIC, 1)


def read_wind(path: str | Path) -> list[np.ndarray]:
    return _read(path, WIND_MAGIC, 3)


def sensor_forward(physical: np.ndarray) -> np.ndarray:
    values = np.asarray(physical, dtype=np.float64)
    if values.ndim not in (1, 2) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("CTT_H01_SENSOR_INVALID_PHYSICAL")
    if values.ndim == 2:
        return np.stack([sensor_forward(row) for row in values])
    # Preserve the operation order of the authoritative run-persistent sensor
    # exactly.  The delay happens to be an integer number of samples here, but
    # retaining its causal interpolation avoids a numerically different
    # vectorized shortcut at the 0.1-ppm decision boundary.
    history_time = [0.0]
    history_value = [0.0]
    history_left = 0
    time_s = 0.0
    state = 0.0
    measured = np.empty_like(values)

    def delayed_input(query_time_s: float) -> float:
        nonlocal history_left
        if query_time_s <= 0.0:
            return 0.0
        if query_time_s >= history_time[-1]:
            return history_value[-1]
        while history_left + 1 < len(history_time) and query_time_s > history_time[history_left + 1]:
            history_left += 1
        previous_time, previous_value = history_time[history_left], history_value[history_left]
        next_time, next_value = history_time[history_left + 1], history_value[history_left + 1]
        width = next_time - previous_time
        if width <= 0.0:
            return next_value
        weight = (query_time_s - previous_time) / width
        return previous_value + weight * (next_value - previous_value)

    for index, value in enumerate(values):
        time_s += DT_S
        history_time.append(time_s)
        history_value.append(float(value))
        target = delayed_input(time_s - SENSOR_DEAD_S)
        alpha = math.exp(-DT_S / SENSOR_TAU_S)
        state = alpha * state + (1.0 - alpha) * target
        measured[index] = np.clip(state, 0.0, 1.0e6)
    return measured


def first_passage(measured_stop: np.ndarray) -> int:
    values = np.asarray(measured_stop)
    if values.shape != (STOP_SAMPLES,):
        raise ValueError(f"CTT_H01_FIRST_PASSAGE_SHAPE:{values.shape}")
    hit = values > FIRST_PASSAGE_THRESHOLD_PPM
    return int(np.argmax(hit)) if bool(hit.any()) else STOP_SAMPLES
