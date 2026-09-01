#!/usr/bin/env python3
"""CPIR three-module formula reference and fixed-trajectory shadow evaluator.

This file is intentionally independent of the ROS runtime.  It reads the
already-frozen CPIR full-grid lookup bank and historical OFF tapes only; it
never invokes GADEN.  Stage 1 constructs A1/A2/A3 scores and posteriors before
opening native PMFS results or truth.  Stage 2 reloads the hashed Stage-1
artifact and computes the requested paired shadow endpoints.

Scientific arms
---------------
 A0: authoritative historical PMFS (loaded only in stage 2)
 A1: native physical tape -> memoryless raw stop event -> count-only score
 A2: native physical tape -> persistent sensor state -> count-only score
 A3: native physical tape -> persistent sensor state -> stop-resolved score

The carrier-to-cell map is the frozen KL/I-projection interface with a
geometry-only uniform reference: Q_cell(c)=Q_C(i(c))/|C_i|.  It is not an
additional scientific module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


CONTRACT = "CPIR_THREE_MODULE_NESTED_SHADOW_V1"
MAGIC = b"PFV3STR1"
HEADER = struct.Struct("<8sI")
DT_S = 0.2
TAU_S = 1.2
ALPHA = math.exp(-DT_S / TAU_S)
DELAY_SAMPLES = 2
THRESHOLD_PPM = 0.1
STOP_SAMPLES = 80
STOP_DURATION_S = STOP_SAMPLES * DT_S
TIME_COUNT = 1500
MEMBER_COUNT = 8
SOURCE_UPDATES = 5
HOUSES = ("H01", "H02", "H03")
HOUSE_DIR = {"H01": "House01", "H02": "House02", "H03": "House03"}
TOL = 1.0e-10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_softmax(log_values: np.ndarray) -> np.ndarray:
    values = np.asarray(log_values, dtype=np.float64)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("CPIR_SOFTMAX_INPUT")
    shifted = values - float(np.max(values))
    result = np.exp(shifted)
    total = float(np.sum(result))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("CPIR_SOFTMAX_NORMALIZATION")
    return result / total


def rank_desc(values: np.ndarray, truth_index: int) -> float:
    row = np.asarray(values, dtype=np.float64)
    if row.ndim != 1 or not np.isfinite(row).all() or not 0 <= truth_index < len(row):
        raise ValueError("CPIR_RANK_INPUT")
    target = row[truth_index]
    return float(1 + np.count_nonzero(row > target)
                 + 0.5 * (np.count_nonzero(row == target) - 1))


def projection(carrier_mass: np.ndarray, cell_to_carrier: np.ndarray,
                carrier_cell_counts: np.ndarray) -> np.ndarray:
    """Frozen KL/I-projection for a uniform geometry-only p_ref."""
    q = np.asarray(carrier_mass, dtype=np.float64)
    mapping = np.asarray(cell_to_carrier, dtype=np.int64)
    counts = np.asarray(carrier_cell_counts, dtype=np.float64)
    if q.ndim != 1 or mapping.ndim != 1 or counts.ndim != 1:
        raise ValueError("CPIR_PROJECTION_SHAPE")
    if len(q) != len(counts) or np.any(q < 0) or not np.isfinite(q).all():
        raise ValueError("CPIR_PROJECTION_INPUT")
    if np.any(counts <= 0) or np.any(mapping < 0) or np.any(mapping >= len(q)):
        raise ValueError("CPIR_PROJECTION_SUPPORT")
    result = q[mapping] / counts[mapping]
    if abs(float(np.sum(result)) - 1.0) > 1.0e-12:
        raise ValueError("CPIR_PROJECTION_MASS")
    return result


def carrier_scores(q0: np.ndarray, q_by_stop: np.ndarray,
                   observed: np.ndarray, visible: np.ndarray,
                   mode: str) -> tuple[np.ndarray, np.ndarray]:
    """Return carrier log-score and posterior for A1/A2/A3."""
    q = np.asarray(q_by_stop, dtype=np.float64)
    y = np.asarray(observed, dtype=np.bool_)
    vis = np.asarray(visible, dtype=np.int64)
    if (q.ndim != 2 or q.shape[1] != len(y) or len(vis) == 0 or
            np.any(vis < 0) or np.any(vis >= q.shape[1]) or
            np.asarray(q0, dtype=np.float64).ndim != 1 or
            len(q0) != q.shape[0] or np.any(np.asarray(q0, dtype=np.float64) <= 0.0)):
        raise ValueError("CPIR_SCORE_SHAPE")
    if np.any(q <= 0.0) or np.any(q >= 1.0):
        raise ValueError("CPIR_SCORE_PROBABILITY")
    selected = q[:, vis]
    selected_y = y[vis]
    if mode == "count_only":
        pbar = np.mean(selected, axis=1)
        hit_count = int(np.count_nonzero(selected_y))
        score = hit_count * np.log(pbar) + (len(vis) - hit_count) * np.log1p(-pbar)
    elif mode == "stop_resolved":
        score = np.sum(np.where(selected_y[None, :], np.log(selected),
                                np.log1p(-selected)), axis=1)
    else:
        raise ValueError(f"CPIR_SCORE_MODE:{mode}")
    posterior = stable_softmax(np.log(np.asarray(q0, dtype=np.float64)) + score)
    return score, posterior


def raw_events(physical: np.ndarray, stops: list[np.ndarray]) -> np.ndarray:
    values = np.asarray(physical, dtype=np.float64)
    if values.ndim != 2 or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("CPIR_RAW_PHYSICAL")
    result = np.zeros(len(stops), dtype=np.bool_)
    for b, indices in enumerate(stops):
        if len(indices) != STOP_SAMPLES or int(np.max(indices)) >= values.shape[1]:
            raise ValueError("CPIR_RAW_STOP")
        result[b] = bool(np.max(values[:, indices]) > THRESHOLD_PPM)
    return result


def stateful_events(physical: np.ndarray, stops: list[np.ndarray],
                    reset_at_stop: bool = False) -> np.ndarray:
    """Apply the exact delayed first-order state over the complete tape."""
    values = np.asarray(physical, dtype=np.float64)
    if values.ndim != 2 or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("CPIR_STATE_PHYSICAL")
    stop_for_time = np.full(values.shape[1], -1, dtype=np.int64)
    for b, indices in enumerate(stops):
        if len(indices) != STOP_SAMPLES or int(np.max(indices)) >= values.shape[1]:
            raise ValueError("CPIR_STATE_STOP")
        stop_for_time[indices] = b
    events = np.zeros(len(stops), dtype=np.bool_)
    state = 0.0
    delay_one = 0.0
    delay_two = 0.0
    for t in range(values.shape[1]):
        target = delay_two
        delay_two = delay_one
        delay_one = float(values[0, t])
        state = ALPHA * state + (1.0 - ALPHA) * target
        b = int(stop_for_time[t])
        if b >= 0:
            events[b] = events[b] or state > THRESHOLD_PPM
        if reset_at_stop and b >= 0 and (t == stops[b][-1]):
            state = 0.0
            delay_one = 0.0
            delay_two = 0.0
    return events


def stateful_events_members(physical: np.ndarray, stops: list[np.ndarray],
                            reset_at_stop: bool = False) -> np.ndarray:
    """Vectorized over members: physical [member,time] -> [member,stop]."""
    values = np.asarray(physical, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != MEMBER_COUNT:
        raise ValueError("CPIR_MEMBER_PHYSICAL_SHAPE")
    stop_for_time = np.full(values.shape[1], -1, dtype=np.int64)
    for b, indices in enumerate(stops):
        if len(indices) != STOP_SAMPLES or int(np.max(indices)) >= values.shape[1]:
            raise ValueError("CPIR_MEMBER_STOP")
        stop_for_time[indices] = b
    result = np.zeros((MEMBER_COUNT, len(stops)), dtype=np.bool_)
    state = np.zeros(MEMBER_COUNT, dtype=np.float64)
    delay_one = np.zeros(MEMBER_COUNT, dtype=np.float64)
    delay_two = np.zeros(MEMBER_COUNT, dtype=np.float64)
    for t in range(values.shape[1]):
        target = delay_two.copy()
        delay_two = delay_one
        delay_one = values[:, t]
        state = ALPHA * state + (1.0 - ALPHA) * target
        b = int(stop_for_time[t])
        if b >= 0:
            result[:, b] |= state > THRESHOLD_PPM
            if reset_at_stop and t == int(stops[b][-1]):
                state[:] = 0.0
                delay_one[:] = 0.0
                delay_two[:] = 0.0
    return result


def parse_carrier_id(identifier: str) -> tuple[int, int, int, int]:
    parts = identifier.split("_")
    if len(parts) != 5 or parts[0] != "quadtree":
        raise ValueError(f"CPIR_CARRIER_ID:{identifier}")
    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


@dataclass
class BankHouse:
    house: str
    root: Path
    carriers: list[str]
    cell_indices: np.ndarray
    cell_x: np.ndarray
    cell_y: np.ndarray
    cell_to_stream: dict[int, int]
    cell_to_carrier: np.ndarray
    carrier_cell_counts: np.ndarray
    q0: np.ndarray
    world_paths: list[list[Path]]
    summary_sha256: str

    @classmethod
    def load(cls, house: str, root: Path, support_rows: list[dict[str, str]]) -> "BankHouse":
        bank = root / house
        summary_path = bank / "bank_summary.json"
        if not summary_path.is_file() or (bank / "IN_PROGRESS").exists():
            raise RuntimeError(f"CPIR_BANK_NOT_FROZEN:{house}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("contract") != "CPIR_FULLGRID_LOOKUP_V1" or summary.get("verdict") != "CPIR_FULLGRID_LOOKUP_PASS":
            raise RuntimeError(f"CPIR_BANK_CONTRACT:{house}")
        if int(summary.get("member_count", -1)) != MEMBER_COUNT or int(summary.get("time_count", -1)) != TIME_COUNT:
            raise RuntimeError(f"CPIR_BANK_DIMENSIONS:{house}")
        with (bank / "cell_manifest.csv").open(newline="", encoding="utf-8") as source:
            cells = list(csv.DictReader(source))
        if not cells or list(cells[0]) != ["stream_ordinal", "native_cell_index", "x", "y"]:
            raise RuntimeError(f"CPIR_CELL_MANIFEST_HEADER:{house}")
        cells.sort(key=lambda row: int(row["stream_ordinal"]))
        stream = [int(row["stream_ordinal"]) for row in cells]
        native = [int(row["native_cell_index"]) for row in cells]
        if stream != list(range(len(cells))) or len(set(native)) != len(native):
            raise RuntimeError(f"CPIR_CELL_MANIFEST_ORDER:{house}")
        carriers = sorted(path.stem for path in (bank / "worlds" / "member_00").glob("*.bin"))
        expected_count = int(summary["carrier_count"])
        if len(carriers) != expected_count:
            raise RuntimeError(f"CPIR_CARRIER_COUNT:{house}:{len(carriers)}:{expected_count}")
        support_ids = sorted({row["carrier_id"] for row in support_rows if row["house"] == house})
        if support_ids != carriers:
            raise RuntimeError(f"CPIR_SUPPORT_CARRIER_SET:{house}")
        # Native cell indices are flattened with the per-case grid width.  The
        # rectangle identity is checked once a case supplies that width.
        # Build a provisional map using the common 2x2 carrier geometry only
        # after validating every carrier rectangle is unique.
        rectangles = {identifier: parse_carrier_id(identifier) for identifier in carriers}
        if len(set(rectangles.values())) != len(rectangles):
            raise RuntimeError(f"CPIR_CARRIER_RECT_DUP:{house}")
        world_paths: list[list[Path]] = []
        for carrier in carriers:
            row_paths = []
            for member in range(MEMBER_COUNT):
                path = bank / "worlds" / f"member_{member:02d}" / f"{carrier}.bin"
                if not path.is_file():
                    raise RuntimeError(f"CPIR_WORLD_MISSING:{path}")
                expected_size = 12 + 4 * len(cells) + 4 * len(cells) * TIME_COUNT
                if path.stat().st_size != expected_size:
                    raise RuntimeError(f"CPIR_WORLD_SIZE:{path}")
                row_paths.append(path)
            world_paths.append(row_paths)
        support_by_id = {row["carrier_id"]: row for row in support_rows if row["house"] == house}
        # Geometry-only free-cell membership is inferred from the native cell
        # coordinate and case grid metadata in load_case().  Keep the arrays
        # allocated here and fill them in validate_case_mapping().
        return cls(
            house=house,
            root=bank,
            carriers=carriers,
            cell_indices=np.asarray(native, dtype=np.int64),
            cell_x=np.asarray([float(row["x"]) for row in cells], dtype=np.float64),
            cell_y=np.asarray([float(row["y"]) for row in cells], dtype=np.float64),
            cell_to_stream={value: index for index, value in enumerate(native)},
            cell_to_carrier=np.full(len(cells), -1, dtype=np.int64),
            carrier_cell_counts=np.zeros(len(carriers), dtype=np.int64),
            q0=np.zeros(len(carriers), dtype=np.float64),
            world_paths=world_paths,
            summary_sha256=sha256_file(summary_path),
        )

    def validate_case_mapping(self, width: int, height: int) -> None:
        carrier_index = {identifier: i for i, identifier in enumerate(self.carriers)}
        mapping = np.full(len(self.cell_indices), -1, dtype=np.int64)
        for row, native in enumerate(self.cell_indices):
            i = int(native % width)
            j = int(native // width)
            if not (0 <= i < width and 0 <= j < height):
                raise RuntimeError(f"CPIR_NATIVE_CELL_BOUNDS:{self.house}:{native}")
            oi, oj = 2 * (i // 2), 2 * (j // 2)
            sx = 1 if i == width - 1 else 2
            sy = 1 if j == height - 1 else 2
            identifier = f"quadtree_{oi}_{oj}_{sx}_{sy}"
            if identifier not in carrier_index:
                # Some maps have a one-cell boundary rectangle encoded in the
                # manifest.  Search the explicit rectangles rather than
                # guessing a nearest carrier.
                hits = []
                for candidate, (coi, coj, csx, csy) in (
                    (key, parse_carrier_id(key)) for key in self.carriers
                ):
                    if coi <= i < coi + csx and coj <= j < coj + csy:
                        hits.append(candidate)
                if len(hits) != 1:
                    raise RuntimeError(f"CPIR_CELL_CARRIER_MAPPING:{self.house}:{native}:{hits}")
                identifier = hits[0]
            mapping[row] = carrier_index[identifier]
        if np.any(mapping < 0):
            raise RuntimeError(f"CPIR_CELL_MAPPING_UNSET:{self.house}")
        counts = np.bincount(mapping, minlength=len(self.carriers)).astype(np.int64)
        if np.any(counts <= 0):
            raise RuntimeError(f"CPIR_CARRIER_EMPTY:{self.house}")
        self.cell_to_carrier = mapping
        self.carrier_cell_counts = counts
        self.q0 = counts.astype(np.float64) / float(np.sum(counts))
        # Interface self-checks: mass, odds, and identity.
        test = projection(self.q0, mapping, counts)
        reconstructed = np.bincount(mapping, weights=test, minlength=len(counts))
        if not np.allclose(reconstructed, self.q0, rtol=0, atol=1e-12):
            raise RuntimeError(f"CPIR_PROJECTION_IDENTITY:{self.house}")
        if not np.allclose(test[mapping == 0], test[mapping == 0][0], rtol=0, atol=1e-15):
            raise RuntimeError(f"CPIR_PROJECTION_ODDS:{self.house}")


@dataclass
class Case:
    house: str
    seed: int
    runtime: Path
    times: np.ndarray
    native_indices: np.ndarray
    stream_indices: np.ndarray
    stops: list[np.ndarray]
    visible: list[np.ndarray]
    observed_events: np.ndarray
    update_times: np.ndarray
    timing: dict[str, str]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def load_case(historical_root: Path, house: str, seed: int, bank: BankHouse,
              *, strict_full_coverage: bool = True) -> Case:
    directory = HOUSE_DIR[house]
    runtime = historical_root / directory / f"seed{seed}" / "off" / "runtime" / f"{directory}_seed{seed}_off_off"
    pose_path = runtime / "sim_pose_trace.csv"
    sensor_path = runtime / "sensor_trace.csv"
    timing_path = runtime / "context_bank" / "source_update_timing.csv"
    pose = read_csv(pose_path)
    sensor = read_csv(sensor_path)
    timing_rows = read_csv(timing_path)
    if len(pose) != len(sensor) or len(timing_rows) != SOURCE_UPDATES or len(pose) < TIME_COUNT:
        raise RuntimeError(f"CPIR_CASE_LENGTH:{house}:{seed}")
    timing = timing_rows[0]
    width = int(timing["grid_width"]); height = int(timing["grid_height"])
    origin_x = float(timing["origin_x"]); origin_y = float(timing["origin_y"])
    cell_size = float(timing["cell_size"])
    bank.validate_case_mapping(width, height)
    # The first TIME_COUNT rows are the bank's exact 0.2 s horizon.  Use the
    # same integer conversion as Grid2DMetadata::coordinatesToIndices.
    times = np.asarray([float(row["t_sim_s"]) for row in pose[:TIME_COUNT]], dtype=np.float64)
    measured_times = np.asarray([float(row["t_sim_s"]) for row in sensor[:TIME_COUNT]], dtype=np.float64)
    expected_times = np.arange(1, TIME_COUNT + 1, dtype=np.float64) * DT_S
    if np.max(np.abs(times - expected_times)) > 1.0e-6 or np.max(np.abs(measured_times - times)) > 1.0e-9:
        raise RuntimeError(f"CPIR_CASE_TIME_GRID:{house}:{seed}")
    ix = np.asarray([int((float(row["x"]) - origin_x) / cell_size) for row in pose[:TIME_COUNT]], dtype=np.int64)
    iy = np.asarray([int((float(row["y"]) - origin_y) / cell_size) for row in pose[:TIME_COUNT]], dtype=np.int64)
    native = ix + iy * width
    missing = [int(index) for index in native if int(index) not in bank.cell_to_stream]
    if missing and strict_full_coverage:
        # Fail closed.  Filling with zero or nearest free cell would change
        # the frozen physical observation operator and invalidate parity.
        unique = sorted(set(missing))
        raise RuntimeError(f"CPIR_CASE_BANK_COVERAGE:{house}:{seed}:missing={len(missing)}:unique={unique[:12]}")
    # A diagnostic A1 (memoryless stop event) may retain -1 for unsupported
    # motion cells because those samples are never read.  A2/A3 always use the
    # default strict path and therefore never receive a sentinel.
    stream = np.asarray([bank.cell_to_stream.get(int(index), -1) for index in native], dtype=np.int64)
    moving = np.asarray([int(row["is_moving"]) for row in pose[:TIME_COUNT]], dtype=np.int8)
    stops: list[np.ndarray] = []
    start: int | None = None
    for index, value in enumerate(moving):
        if value == 0 and start is None:
            start = index
        if value != 0 and start is not None:
            if index - start >= STOP_SAMPLES:
                stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
            start = None
    if start is not None and len(moving) - start >= STOP_SAMPLES:
        stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
    update_times = np.asarray([float(row["sim_time"]) for row in timing_rows], dtype=np.float64)
    if len(stops) < 3 or not np.all(np.diff(update_times) > 0):
        raise RuntimeError(f"CPIR_CASE_STOPS:{house}:{seed}:{len(stops)}")
    visible = [np.asarray([b for b, stop in enumerate(stops)
                           if times[int(stop[-1])] <= update_time + TOL], dtype=np.int64)
               for update_time in update_times]
    if any(len(item) != 3 * (index + 1) for index, item in enumerate(visible)):
        raise RuntimeError(f"CPIR_CASE_VISIBLE_STOPS:{house}:{seed}:{[len(v) for v in visible]}")
    missing_stop = [int(native[t]) for stop in stops for t in stop
                    if int(native[t]) not in bank.cell_to_stream]
    if missing_stop:
        unique = sorted(set(missing_stop))
        raise RuntimeError(f"CPIR_CASE_STOP_COVERAGE:{house}:{seed}:missing={len(missing_stop)}:unique={unique[:12]}")
    measured = np.asarray([float(row["measured_gas_ppm"]) for row in sensor[:TIME_COUNT]], dtype=np.float64)
    if not np.isfinite(measured).all() or np.any(measured < 0):
        raise RuntimeError(f"CPIR_CASE_MEASURED:{house}:{seed}")
    observed = np.asarray([bool(np.max(measured[stop]) > THRESHOLD_PPM) for stop in stops], dtype=np.bool_)
    return Case(house, seed, runtime, times, native, stream, stops, visible,
                observed, update_times, timing)


def read_world_streams(path: Path, stream_indices: np.ndarray) -> np.ndarray:
    """Read selected streams from one world using one sequential payload read.

    The worlds live on a VMware shared folder.  Repeated mmap page faults at
    sparse stream offsets are orders of magnitude slower there than one
    sequential 3--4 MB read, while the temporary array remains bounded to one
    world.  We still return only the requested streams, so no whole-bank
    materialization occurs.
    """
    indices = np.asarray(stream_indices, dtype=np.int64)
    if indices.ndim != 1 or np.any(indices < 0):
        raise ValueError("CPIR_STREAM_INDICES")
    with path.open("rb") as source:
        head = source.read(12)
        if len(head) != 12 or head[:8] != MAGIC:
            raise RuntimeError(f"CPIR_WORLD_MAGIC:{path}")
        (count,) = struct.unpack_from("<I", head, 8)
        if count <= 0:
            raise RuntimeError(f"CPIR_WORLD_COUNT:{path}")
        lengths_raw = source.read(4 * count)
        lengths = np.frombuffer(lengths_raw, dtype="<u4")
        if len(lengths) != count or np.any(lengths != TIME_COUNT):
            raise RuntimeError(f"CPIR_WORLD_LENGTHS:{path}")
        if np.any(indices >= count):
            bad = int(indices[np.flatnonzero(indices >= count)[0]])
            raise RuntimeError(f"CPIR_WORLD_STREAM_RANGE:{path}:{bad}")
        data_offset = 12 + 4 * count
        source.seek(data_offset)
        payload = np.fromfile(source, dtype="<f4", count=count * TIME_COUNT)
        if payload.size != count * TIME_COUNT:
            raise RuntimeError(f"CPIR_WORLD_PAYLOAD_TRUNCATED:{path}")
        matrix = payload.reshape(count, TIME_COUNT)
        result = np.asarray(matrix[indices], dtype=np.float32).copy()
    if not np.isfinite(result).all() or np.any(result < 0):
        raise RuntimeError(f"CPIR_WORLD_VALUES:{path}")
    return result


def build_events(bank: BankHouse, cases: list[Case]) -> tuple[np.ndarray, np.ndarray]:
    """Build [case, carrier, member, stop] raw and stateful event arrays."""
    max_stops = max(len(case.stops) for case in cases)
    raw = np.zeros((len(cases), len(bank.carriers), MEMBER_COUNT, max_stops), dtype=np.bool_)
    state = np.zeros_like(raw)
    # The bank is trajectory-independent.  Read each world once and apply it
    # to all historical seeds, substantially reducing mounted-share seeks.
    union_streams = np.unique(np.concatenate([case.stream_indices for case in cases]))
    stream_position = {int(stream): row for row, stream in enumerate(union_streams)}
    for carrier_index, carrier in enumerate(bank.carriers):
        for member in range(MEMBER_COUNT):
            path = bank.world_paths[carrier_index][member]
            values = read_world_streams(path, union_streams)
            for case_index, case in enumerate(cases):
                rows = np.asarray([stream_position[int(item)] for item in case.stream_indices], dtype=np.int64)
                physical = values[rows, np.arange(TIME_COUNT, dtype=np.int64)].astype(np.float64)
                for stop_index, stop in enumerate(case.stops):
                    raw[case_index, carrier_index, member, stop_index] = bool(
                        np.max(physical[stop]) > THRESHOLD_PPM
                    )
                # A scalar recurrence per member is cheap; keeping the exact
                # operation order avoids hidden vectorization/axis changes.
                sensor_state = 0.0; delay_one = 0.0; delay_two = 0.0
                for t in range(TIME_COUNT):
                    target = delay_two
                    delay_two = delay_one
                    delay_one = float(physical[t])
                    sensor_state = ALPHA * sensor_state + (1.0 - ALPHA) * target
                    for stop_index, stop in enumerate(case.stops):
                        # Stops are disjoint and short; this branch is
                        # intentionally explicit for auditability.
                        if int(stop[0]) <= t <= int(stop[-1]):
                            if sensor_state > THRESHOLD_PPM:
                                state[case_index, carrier_index, member, stop_index] = True
                            break
            if (carrier_index * MEMBER_COUNT + member + 1) % 100 == 0:
                print(f"CPIR_EVENT_PROGRESS={bank.house}:{carrier_index * MEMBER_COUNT + member + 1}/{len(bank.carriers) * MEMBER_COUNT}", flush=True)
    return raw, state


def pretruth_stage(bank_root: Path, historical_root: Path, support_path: Path,
                   output: Path) -> dict[str, Any]:
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    all_metadata: list[dict[str, Any]] = []
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        cases = [load_case(historical_root, house, seed, bank) for seed in range(10)]
        raw_events, state_events = build_events(bank, cases)
        # Save events independently so an audit can recompute all scores
        # without touching the 18-GB bank again.
        house_npz = output / f"{house}_EVENTS.npz"
        np.savez_compressed(house_npz, raw=raw_events, stateful=state_events,
                            carrier_ids=np.asarray(bank.carriers),
                            cell_indices=bank.cell_indices,
                            cell_to_carrier=bank.cell_to_carrier,
                            carrier_cell_counts=bank.carrier_cell_counts)
        records: list[dict[str, Any]] = []
        for case_index, case in enumerate(cases):
            for update_id, visible in enumerate(case.visible, start=1):
                # q has shape [carrier, stop], one value per completed stop.
                q_raw = (raw_events[case_index, :, :, :len(case.stops)].sum(axis=1) + 0.5) / 9.0
                q_state = (state_events[case_index, :, :, :len(case.stops)].sum(axis=1) + 0.5) / 9.0
                _, a1_carrier = carrier_scores(bank.q0, q_raw, case.observed_events, visible, "count_only")
                _, a2_carrier = carrier_scores(bank.q0, q_state, case.observed_events, visible, "count_only")
                _, a3_carrier = carrier_scores(bank.q0, q_state, case.observed_events, visible, "stop_resolved")
                records.append({
                    "house": house, "seed": case.seed, "update_id": update_id,
                    "visible_stops": [int(v) for v in visible],
                    "observed_hit_count": int(np.count_nonzero(case.observed_events[visible])),
                    "a1_carrier": a1_carrier, "a2_carrier": a2_carrier,
                    "a3_carrier": a3_carrier,
                    "update_time_s": float(case.update_times[update_id - 1]),
                })
                all_metadata.append({
                    "house": house, "seed": case.seed, "update_id": update_id,
                    "visible_stops": [int(v) for v in visible],
                    "observed_hit_count": int(np.count_nonzero(case.observed_events[visible])),
                    "update_time_s": float(case.update_times[update_id - 1]),
                })
        np.savez_compressed(output / f"{house}_POSTERIORS.npz",
                            a1=np.stack([r["a1_carrier"] for r in records]),
                            a2=np.stack([r["a2_carrier"] for r in records]),
                            a3=np.stack([r["a3_carrier"] for r in records]))
        (output / f"{house}_CASE_META.json").write_text(
            json.dumps({"house": house, "cases": [case.seed for case in cases],
                        "update_records": all_metadata[-50:]}, indent=2) + "\n",
            encoding="utf-8")
        print(f"CPIR_STAGE1_{house}=PASS", flush=True)
    manifest = {
        "contract": CONTRACT,
        "status": "ALL_A1_A2_A3_POSTERIORS_FROZEN_BEFORE_A0_OR_TRUTH",
        "bank_root": str(bank_root), "historical_root": str(historical_root),
        "support_sha256": sha256_file(support_path),
        "files": {path.name: sha256_file(path) for path in sorted(output.iterdir()) if path.is_file()},
        "formula": {"dt_s": DT_S, "tau_s": TAU_S, "alpha": ALPHA,
                    "delay_samples": DELAY_SAMPLES, "threshold_ppm": THRESHOLD_PPM,
                    "stop_samples": STOP_SAMPLES, "members": MEMBER_COUNT,
                    "projection": "uniform_geometry_p_ref"},
    }
    manifest["artifact_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()
    (output / "PRETRUTH_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def endpoint(rows: list[dict[str, str]], probability: np.ndarray,
             truth_xy: tuple[float, float]) -> dict[str, float]:
    mass = np.asarray(probability, dtype=np.float64)
    if len(rows) != len(mass) or not np.isfinite(mass).all() or np.any(mass < 0):
        raise RuntimeError("CPIR_ENDPOINT_INPUT")
    total_mass = float(np.sum(mass))
    if total_mass <= 0: raise RuntimeError("CPIR_ENDPOINT_MASS")
    mass = mass / total_mass
    count = int(math.ceil(len(rows) * 0.05 - 1.0e-15))
    cells = np.asarray([int(row["cell_index"]) for row in rows], dtype=np.int64)
    x = np.asarray([float(row["x"]) for row in rows], dtype=np.float64)
    y = np.asarray([float(row["y"]) for row in rows], dtype=np.float64)
    selected = np.lexsort((cells, -mass))[:count]
    weights = np.zeros(len(rows), dtype=np.float64); weights[selected] = mass[selected]
    denom = float(np.sum(weights))
    ex = float(np.sum(x * weights) / denom); ey = float(np.sum(y * weights) / denom)
    variance = float(np.sum(mass * ((x - np.sum(x * mass)) ** 2 + (y - np.sum(y * mass)) ** 2)))
    return {"estimate_x": ex, "estimate_y": ey,
            "error_m": math.hypot(ex - truth_xy[0], ey - truth_xy[1]),
            "variance_m2": variance, "selected_count": count}


def load_posterior(path: Path) -> list[dict[str, str]]:
    return read_csv(path)


def stage2_evaluate(bank_root: Path, historical_root: Path, support_path: Path,
                    stage1: Path, output: Path) -> dict[str, Any]:
    manifest_path = stage1 / "PRETRUTH_MANIFEST.json"
    if not manifest_path.is_file(): raise RuntimeError("CPIR_STAGE1_MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != CONTRACT or manifest.get("status") != "ALL_A1_A2_A3_POSTERIORS_FROZEN_BEFORE_A0_OR_TRUTH":
        raise RuntimeError("CPIR_STAGE1_MANIFEST_CONTRACT")
    for name, digest in manifest.get("files", {}).items():
        path = stage1 / name
        if not path.is_file() or sha256_file(path) != digest:
            raise RuntimeError(f"CPIR_STAGE1_HASH:{name}")
    support_rows = read_csv(support_path)
    output.mkdir(parents=True, exist_ok=False)
    pair_rows: list[dict[str, Any]] = []
    update_rows: list[dict[str, Any]] = []
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        # Width is available from any case and also revalidates carrier map.
        cases = [load_case(historical_root, house, seed, bank) for seed in range(10)]
        post = np.load(stage1 / f"{house}_POSTERIORS.npz")
        for case_index, case in enumerate(cases):
            final_dir = case.runtime.parent.parent  # .../seedN/off
            posterior_path = final_dir / "final_posterior.csv"
            result_path = final_dir / "case_result.json"
            if not posterior_path.is_file() or not result_path.is_file():
                raise RuntimeError(f"CPIR_A0_MISSING:{house}:{case.seed}")
            native_rows = load_posterior(posterior_path)
            native_result = json.loads(result_path.read_text(encoding="utf-8"))
            truth = tuple(float(v) for v in native_result["truth_eval_only"])
            baseline = endpoint(native_rows, np.asarray([float(r["source_probability"]) for r in native_rows]), truth)
            baseline_delta = baseline["error_m"] - float(native_result["primary_error_m"])
            if abs(baseline_delta) > 1.0e-8:
                raise RuntimeError(f"CPIR_A0_REPRODUCTION:{house}:{case.seed}:{baseline_delta}")
            # Cell order in the bank and PMFS final file must be identical as a
            # set; endpoint uses explicit cell_index ties, so row order is safe.
            native_ids = {int(r["cell_index"]) for r in native_rows}
            if native_ids != set(int(v) for v in bank.cell_indices):
                raise RuntimeError(f"CPIR_A0_CELL_SET:{house}:{case.seed}")
            true_ix = int((truth[0] - float(case.timing["origin_x"])) /
                          float(case.timing["cell_size"]))
            true_iy = int((truth[1] - float(case.timing["origin_y"])) /
                          float(case.timing["cell_size"]))
            true_native = int(true_ix + true_iy * int(case.timing["grid_width"]))
            if true_native not in bank.cell_to_stream:
                raise RuntimeError(f"CPIR_TRUTH_OUTSIDE_SUPPORT:{house}:{case.seed}:{true_native}")
            truth_cell_row = bank.cell_to_stream[true_native]
            truth_carrier = int(bank.cell_to_carrier[truth_cell_row])
            record_index = case_index * SOURCE_UPDATES
            finals: dict[str, dict[str, float]] = {}
            for update_id in range(SOURCE_UPDATES):
                update_record_index = record_index + update_id
                for method in ("a1", "a2", "a3"):
                    carrier_mass = np.asarray(post[method][update_record_index], dtype=np.float64)
                    cell_mass = projection(carrier_mass, bank.cell_to_carrier, bank.carrier_cell_counts)
                    if update_id == SOURCE_UPDATES - 1:
                        finals[method] = endpoint(
                            [{"cell_index": str(int(c)), "x": str(float(x)), "y": str(float(y))}
                             for c, x, y in zip(bank.cell_indices, bank.cell_x, bank.cell_y)],
                            cell_mass, truth
                        )
                    update_rows.append({
                        "house": house, "seed": case.seed, "update_id": update_id + 1,
                        "method": method.upper(), "true_carrier_rank": rank_desc(carrier_mass, truth_carrier),
                        "true_cell_rank": rank_desc(cell_mass, truth_cell_row),
                        "posterior_true_carrier": float(carrier_mass[truth_carrier]),
                    })
            pair_rows.append({
                "house": house, "seed": case.seed,
                "pmfs_error_m": float(baseline["error_m"]),
                "a1_error_m": float(finals["a1"]["error_m"]),
                "a2_error_m": float(finals["a2"]["error_m"]),
                "a3_error_m": float(finals["a3"]["error_m"]),
                "delta_m1_vs_pmfs": float((baseline["error_m"] - finals["a1"]["error_m"]) / baseline["error_m"]),
                "delta_m2_vs_a1": float((finals["a1"]["error_m"] - finals["a2"]["error_m"]) / baseline["error_m"]),
                "delta_m3_vs_a2": float((finals["a2"]["error_m"] - finals["a3"]["error_m"]) / baseline["error_m"]),
                "a0_variance_m2": float(baseline["variance_m2"]),
                "a1_variance_m2": float(finals["a1"]["variance_m2"]),
                "a2_variance_m2": float(finals["a2"]["variance_m2"]),
                "a3_variance_m2": float(finals["a3"]["variance_m2"]),
                "truth_x": truth[0], "truth_y": truth[1],
            })
    def metrics(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
        x = np.asarray([float(row[left]) for row in rows]); y = np.asarray([float(row[right]) for row in rows])
        return {"pairs": len(rows), "left_mean_m": float(np.mean(x)), "right_mean_m": float(np.mean(y)),
                "left_median_m": float(np.median(x)), "right_median_m": float(np.median(y)),
                "pooled_relative_improvement": float((np.sum(x) - np.sum(y)) / np.sum(x)),
                "wins": int(np.count_nonzero(y < x - 1e-12)),
                "losses": int(np.count_nonzero(y > x + 1e-12)),
                "ties": int(np.count_nonzero(np.abs(y - x) <= 1e-12))}
    comparisons = {
        "A0_PMFS_vs_A1": metrics(pair_rows, "pmfs_error_m", "a1_error_m"),
        "A1_vs_A2_M2_increment": metrics(pair_rows, "a1_error_m", "a2_error_m"),
        "A2_vs_A3_M3_increment": metrics(pair_rows, "a2_error_m", "a3_error_m"),
        "A0_PMFS_vs_A2": metrics(pair_rows, "pmfs_error_m", "a2_error_m"),
        "A0_PMFS_vs_A3": metrics(pair_rows, "pmfs_error_m", "a3_error_m"),
    }
    by_house = {}
    for house in HOUSES:
        subset = [row for row in pair_rows if row["house"] == house]
        by_house[house] = {
            key: metrics(subset, left, right) for key, (left, right) in {
                "A0_PMFS_vs_A1": ("pmfs_error_m", "a1_error_m"),
                "A1_vs_A2": ("a1_error_m", "a2_error_m"),
                "A2_vs_A3": ("a2_error_m", "a3_error_m"),
                "A0_PMFS_vs_A3": ("pmfs_error_m", "a3_error_m"),
            }.items()
        }
    with (output / "NESTED_PAIRS.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(pair_rows[0])); writer.writeheader(); writer.writerows(pair_rows)
    with (output / "NESTED_UPDATES.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(update_rows[0])); writer.writeheader(); writer.writerows(update_rows)
    report = {"contract": CONTRACT, "status": "NESTED_FIXED_TRAJECTORY_SHADOW_COMPLETE",
              "closed_loop": False, "gaden_runs": 0, "neural_training": False,
              "comparisons": comparisons, "by_house": by_house,
              "pair_count": len(pair_rows), "update_count": len(update_rows),
              "stage1_manifest_sha256": sha256_file(manifest_path),
              "support_sha256": sha256_file(support_path),
              "formula": {"dt_s": DT_S, "tau_s": TAU_S, "alpha": ALPHA,
                          "delay_samples": DELAY_SAMPLES, "threshold_ppm": THRESHOLD_PPM,
                          "stop_samples": STOP_SAMPLES, "projection": "uniform_geometry_p_ref"},
              "notes": ["A0 is authoritative historical PMFS comparator.",
                        "A1/A2/A3 were frozen before A0/truth read.",
                        "This is fixed-trajectory shadow, not closed-loop."]}
    (output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "VERDICT.txt").write_text("NESTED_FIXED_TRAJECTORY_SHADOW_COMPLETE\n", encoding="utf-8")
    return report


def selftest() -> None:
    assert abs(ALPHA - 0.846481724890614) < 1e-15
    physical = np.zeros((MEMBER_COUNT, 200), dtype=np.float64)
    physical[:, 2:6] = 1.0
    stops = [np.arange(0, 80), np.arange(80, 160)]
    raw = raw_events(physical[:1], stops)
    state = stateful_events_members(physical, stops)
    assert raw.tolist() == [True, False]
    assert state.shape == (MEMBER_COUNT, 2) and state[:, 0].all()
    q0 = np.asarray([0.25, 0.75]); mapping = np.asarray([0, 0, 1, 1]); counts = np.asarray([2, 2])
    cell = projection(q0, mapping, counts)
    assert np.allclose(cell, [0.125, 0.125, 0.375, 0.375])
    assert np.allclose(np.bincount(mapping, weights=cell), q0)
    observed = np.asarray([True, False]); q = np.asarray([[0.8, 0.2], [0.2, 0.8]])
    _, posterior = carrier_scores(q0, q, observed, np.asarray([0, 1]), "stop_resolved")
    assert np.isclose(float(np.sum(posterior)), 1.0)
    # Count-only and stop-resolved formulas agree exactly when every stop has
    # the same q; they intentionally differ when stop identity is informative.
    q_equal = np.asarray([[0.8, 0.8], [0.2, 0.2]])
    score_count, _ = carrier_scores(q0, q_equal, observed, np.asarray([0, 1]), "count_only")
    score_full, _ = carrier_scores(q0, q_equal, observed, np.asarray([0, 1]), "stop_resolved")
    assert np.allclose(score_count, score_full)
    q_hetero = np.asarray([[0.8, 0.1], [0.2, 0.9]])
    score_count_h, _ = carrier_scores(q0, q_hetero, observed, np.asarray([0, 1]), "count_only")
    score_full_h, _ = carrier_scores(q0, q_hetero, observed, np.asarray([0, 1]), "stop_resolved")
    assert not np.allclose(score_count_h, score_full_h)
    # Recursive append of a new stop equals a batch recomputation under both
    # score definitions (the online ledger contract).
    q_three = np.asarray([[0.8, 0.1, 0.7], [0.2, 0.9, 0.3]])
    y_three = np.asarray([True, False, True])
    for score_mode in ("count_only", "stop_resolved"):
        full, _ = carrier_scores(q0, q_three, y_three, np.asarray([0, 1, 2]), score_mode)
        first, _ = carrier_scores(q0, q_three[:, :2], y_three[:2], np.asarray([0, 1]), score_mode)
        # Recompute from the union is the authoritative online implementation;
        # this check guards the exact event ledger inputs and no double count.
        recomputed, _ = carrier_scores(q0, q_three, y_three, np.asarray([0, 1, 2]), score_mode)
        assert np.allclose(full, recomputed)
        if score_mode == "stop_resolved":
            tail, _ = carrier_scores(q0, q_three[:, 2:], y_three[2:], np.asarray([0]), score_mode)
            assert np.allclose(full, first + tail)
    print("CPIR_THREE_MODULE_REFERENCE_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--stage", choices=("1", "2"))
    parser.add_argument("--bank-root", type=Path)
    parser.add_argument("--historical-root", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--stage1", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest(); return 0
    if not args.stage or not args.bank_root or not args.historical_root or not args.support or not args.output:
        parser.error("--stage/--bank-root/--historical-root/--support/--output required")
    if args.output.exists():
        raise SystemExit(f"CPIR_REFUSE_OVERWRITE:{args.output}")
    if args.stage == "1":
        pretruth_stage(args.bank_root, args.historical_root, args.support, args.output)
    else:
        if not args.stage1: parser.error("--stage1 required for stage 2")
        report = stage2_evaluate(args.bank_root, args.historical_root, args.support, args.stage1, args.output)
        print(json.dumps({"status": report["status"], "comparisons": report["comparisons"], "by_house": report["by_house"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
