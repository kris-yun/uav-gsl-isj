#!/usr/bin/env python3
"""Truth-free carrier descriptors and causal sequence features for PF-DEI V3."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pf_dei_v3_schema import FEATURE_NAMES, INPUT_DIM


THRESHOLD_GAS_PPM = 0.1
PMFS_CELL_SIZE_M = 0.3


@dataclass(frozen=True)
class CarrierDescriptor:
    house: str
    carrier_index: int
    carrier_id: str
    centroid_x: float
    centroid_y: float
    width_m: float
    height_m: float
    free_mask: tuple[float, float, float, float]
    free_count: int
    prior_mass: float


def load_carriers(path: Path) -> dict[str, list[CarrierDescriptor]]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            grouped.setdefault((row["house"], row["carrier_id"]), []).append(row)
    houses: dict[str, list[CarrierDescriptor]] = {}
    for (house, carrier_id), rows in grouped.items():
        first = rows[0]
        origin_i, origin_j = int(first["origin_i"]), int(first["origin_j"])
        size_i, size_j = int(first["size_i"]), int(first["size_j"])
        mask = [0.0] * 4
        for row in rows:
            di = int(row["pmfs_grid_i"]) - origin_i
            dj = int(row["pmfs_grid_j"]) - origin_j
            if not (0 <= di < 2 and 0 <= dj < 2):
                raise ValueError("PF_DEI_V3_CARRIER_MASK_OUT_OF_RANGE")
            mask[2 * di + dj] = 1.0
        free_count = len(rows)
        descriptor = CarrierDescriptor(
            house=house,
            carrier_index=int(first["carrier_index"]),
            carrier_id=carrier_id,
            centroid_x=sum(float(row["pmfs_x"]) for row in rows) / free_count,
            centroid_y=sum(float(row["pmfs_y"]) for row in rows) / free_count,
            width_m=size_i * PMFS_CELL_SIZE_M,
            height_m=size_j * PMFS_CELL_SIZE_M,
            free_mask=tuple(mask),
            free_count=free_count,
            prior_mass=0.0,
        )
        houses.setdefault(house, []).append(descriptor)
    for house, descriptors in houses.items():
        descriptors.sort(key=lambda item: item.carrier_index)
        if [item.carrier_index for item in descriptors] != list(range(len(descriptors))):
            raise ValueError(f"PF_DEI_V3_NONCONTIGUOUS_CARRIER_INDEX:{house}")
        total = sum(item.free_count for item in descriptors)
        houses[house] = [
            CarrierDescriptor(**{**item.__dict__, "prior_mass": item.free_count / total})
            for item in descriptors
        ]
    return houses


def read_schedule(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("PF_DEI_V3_EMPTY_SCHEDULE")
    time = np.asarray([float(row["t_sim_s"]) for row in rows], dtype=np.float64)
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float32)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float32)
    moving = np.asarray([int(row.get("is_moving", "0")) for row in rows], dtype=np.int8)
    dt = np.diff(np.concatenate(([0.0], time))).astype(np.float32)
    if (dt <= 0).any():
        raise ValueError("PF_DEI_V3_NONCAUSAL_SCHEDULE_TIME")
    if "stop_start" in rows[0]:
        stop_start = np.asarray([int(row["stop_start"]) for row in rows], dtype=np.float32)
        block_boundary = np.asarray([int(row["block_boundary"]) for row in rows], dtype=np.float32)
    else:
        stop_start = np.zeros(len(rows), dtype=np.float32)
        stop_start[0] = float(moving[0] == 0)
        stop_start[1:] = ((moving[1:] == 0) & (moving[:-1] != 0)).astype(np.float32)
        block_boundary = np.zeros(len(rows), dtype=np.float32)
        stop_number = 0
        for index in np.flatnonzero(stop_start):
            stop_number += 1
            if stop_number % 3 == 1:
                block_boundary[index] = 1.0
    return {
        "time": time, "x": x, "y": y, "dt": dt,
        "stop_start": stop_start, "block_boundary": block_boundary,
    }


def build_features(
    schedule: dict[str, np.ndarray],
    measured_ppm: np.ndarray,
    measured_wind: np.ndarray,
    carrier: CarrierDescriptor,
) -> np.ndarray:
    measured = np.asarray(measured_ppm, dtype=np.float64)
    wind = np.asarray(measured_wind, dtype=np.float32)
    length = schedule["x"].size
    if measured.shape != (length,) or wind.shape != (length, 3):
        raise ValueError("PF_DEI_V3_FEATURE_LENGTH_MISMATCH")
    if not np.isfinite(measured).all() or (measured < 0).any() or not np.isfinite(wind).all():
        raise ValueError("PF_DEI_V3_FEATURE_NONFINITE")
    output = np.empty((length, INPUT_DIM), dtype=np.float32)
    output[:, 0] = schedule["x"] - carrier.centroid_x
    output[:, 1] = schedule["y"] - carrier.centroid_y
    output[:, 2] = carrier.width_m
    output[:, 3] = carrier.height_m
    output[:, 4:8] = np.asarray(carrier.free_mask, dtype=np.float32)
    output[:, 8] = carrier.free_count / 4.0
    output[:, 9] = np.log1p(measured / THRESHOLD_GAS_PPM).astype(np.float32)
    output[:, 10:13] = wind
    output[:, 13] = schedule["dt"]
    output[:, 14] = schedule["stop_start"]
    output[:, 15] = schedule["block_boundary"]
    assert output.shape[1] == len(FEATURE_NAMES)
    return output
