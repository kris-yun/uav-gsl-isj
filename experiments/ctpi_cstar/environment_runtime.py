"""Reusable evaluator-side environment checks, not learner inputs or a gate PASS.

The raw adapter reads simulator headers/winds and MUST remain outside production
model ingress. Historical evidence readers are deliberately not rewritten.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
import struct
import zlib

import numpy as np


def require(ok, reason):
    if not ok:
        raise ValueError("CSTAR_ENV:" + reason)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def numeric_sequence(directory, prefix):
    """Reject gaps, aliases (01), suffix junk and non-files; never lexical order."""
    files = {}
    for path in Path(directory).iterdir():
        if not path.name.startswith(prefix):
            continue
        suffix = path.name[len(prefix):]
        require(bool(re.fullmatch(r"0|[1-9][0-9]*", suffix)), "NON_CANONICAL_INDEX:" + path.name)
        require(path.is_file(), "INDEX_NOT_FILE:" + path.name)
        files[int(suffix)] = path
    require(bool(files), "EMPTY_SEQUENCE:" + prefix)
    require(sorted(files) == list(range(len(files))), "NON_CONTIGUOUS_SEQUENCE:" + prefix)
    return [files[i] for i in range(len(files))]


@dataclass(frozen=True)
class Grid3D:
    minimum: tuple
    maximum: tuple
    dimensions: tuple
    cell_size: float

    @classmethod
    def from_occupancy(cls, path):
        metadata = {}
        with Path(path).open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                if not line.startswith("#"):
                    break
                fields = line.split()
                metadata[fields[0].split("(")[0]] = fields[1:]
        result = cls(tuple(map(float, metadata["#env_min"])),
                     tuple(map(float, metadata["#env_max"])),
                     tuple(map(int, metadata["#num_cells"])),
                     float(metadata["#cell_size"][0]))
        require(len(result.minimum) == len(result.maximum) == len(result.dimensions) == 3,
                "GRID_SHAPE")
        require(all(math.isfinite(x) for x in result.minimum + result.maximum) and
                math.isfinite(result.cell_size) and result.cell_size > 0 and
                all(n > 0 for n in result.dimensions), "GRID_INVALID")
        require(all(b > a for a, b in zip(result.minimum, result.maximum)), "GRID_BOUNDS")
        return result

    def flat_index(self, point):
        require(len(point) == 3 and all(math.isfinite(x) for x in point), "POINT_INVALID")
        # GADEN samples float32 positions with float32 geometry, not double floor.
        position = np.asarray(point, dtype=np.float32)
        require(np.isfinite(position).all(), "POINT_FLOAT_OVERFLOW")
        indices = np.floor((position - np.asarray(self.minimum, dtype=np.float32)) /
                           np.float32(self.cell_size)).astype(np.int64)
        require(all(0 <= int(i) < n for i, n in zip(indices, self.dimensions)), "POINT_OUTSIDE_GRID")
        x, y, z = map(int, indices)
        nx, ny, _ = self.dimensions
        return x + nx * y + nx * ny * z


def legacy_header(path, grid):
    """Bound decompression to 136 bytes; never decode gas/filament records."""
    decoder, decoded, consumed = zlib.decompressobj(), b"", 0
    with Path(path).open("rb") as stream:
        while len(decoded) < 136:
            block = stream.read(16)
            if not block:
                break
            consumed += len(block)
            require(consumed <= 4096, "HEADER_COMPRESSED_BOUND")
            decoded += decoder.decompress(block, 136 - len(decoded))
    require(len(decoded) == 136, "HEADER_TRUNCATED")
    require(struct.unpack_from("<i", decoded)[0] == 1, "UNSUPPORTED_GAS_HEADER")
    require(tuple(struct.unpack_from("<3i", decoded, 52)) == grid.dimensions, "HEADER_GRID_DIMENSIONS")
    require(math.isclose(struct.unpack_from("<d", decoded, 64)[0], grid.cell_size,
                         rel_tol=1e-6, abs_tol=1e-7), "HEADER_CELL_SIZE")
    original = np.array(grid.minimum + grid.maximum)
    encodings = {"native_double": struct.unpack_from("<6d", decoded, 4),
                 "legacy_float_prefix": [struct.unpack_from("<f", decoded, 4 + 8*i)[0] for i in range(6)]}
    matches = [(name, values) for name, values in encodings.items()
               if np.isfinite(values).all() and np.allclose(values, original, rtol=0, atol=2e-5)]
    require(bool(matches), "HEADER_OCCUPANCY_COORDINATES")
    # Several encodings may coincide at zero; their float32 sampling must agree.
    require(all(np.array_equal(np.asarray(matches[0][1], dtype=np.float32),
                               np.asarray(values, dtype=np.float32)) for _, values in matches),
            "AMBIGUOUS_HEADER_COORDINATES")
    name, coordinates = matches[0]
    index = struct.unpack_from("<i", decoded, 132)[0]
    require(index >= 0, "NEGATIVE_WIND_INDEX")
    # Use header coordinates, just as PlaybackSimulation does; the occupancy is
    # an independent authority for selecting the old float-prefix encoding.
    sample_grid = Grid3D(tuple(coordinates[:3]), tuple(coordinates[3:]), grid.dimensions, grid.cell_size)
    return {"wind_index": index, "encoding": name, "sample_grid": sample_grid,
            "header_sha256": hashlib.sha256(decoded).hexdigest(), "compressed_bytes": consumed}


def decode_wind(path, cells):
    raw = Path(path).read_bytes()
    if len(raw) == cells * 24:
        vectors = np.frombuffer(raw, dtype="<f8").reshape(3, cells).T.astype("<f4")
        layout = "legacy_component_major_double"
    elif len(raw) == cells * 12 + 8 and struct.unpack_from("<i", raw)[0] in (2, 3):
        vectors = np.frombuffer(raw, dtype="<f4", offset=8).reshape(cells, 3).copy()
        layout = "modern_interleaved_float32"
    else:
        raise ValueError("CSTAR_ENV:UNSUPPORTED_WIND_LAYOUT:" + str(path))
    require(np.isfinite(vectors).all(), "NONFINITE_WIND")
    vectors = np.ascontiguousarray(vectors)
    vectors[vectors == 0] = 0
    return vectors, {"path": str(Path(path).resolve()), "layout": layout,
                     "sha256": hashlib.sha256(raw).hexdigest(), "cells": cells,
                     "vector_sha256": hashlib.sha256(vectors.tobytes()).hexdigest()}


class NumericWindReader:
    """One immutable read session. Re-create and fingerprint for each new run."""
    def __init__(self, realization, occupancy):
        self.realization = Path(realization)
        self.grid = Grid3D.from_occupancy(occupancy)
        self.files = numeric_sequence(self.realization / "wind", "wind_iteration_")
        self._cache = {}

    def vectors(self, index):
        require(isinstance(index, int) and 0 <= index < len(self.files), "WIND_INDEX_RANGE")
        if index not in self._cache:
            self._cache[index] = decode_wind(self.files[index], math.prod(self.grid.dimensions))
        return self._cache[index]

    def expected(self, iteration, point):
        require(isinstance(iteration, int) and iteration >= 0, "ITERATION_INVALID")
        header = legacy_header(self.realization / f"iteration_{iteration}", self.grid)
        vectors, _ = self.vectors(header["wind_index"])
        return vectors[header["sample_grid"].flat_index(point)], header

    def verify_reply(self, iteration, point, reply, tolerance=1e-6):
        require(math.isfinite(tolerance) and 0 <= tolerance <= 1e-6, "WIND_TOLERANCE")
        fields = reply.split()
        require(len(fields) == 6 and fields[0] == "OK", "QUERY_RESPONSE")
        values = list(map(float, fields[1:5]))
        require(all(math.isfinite(x) for x in values) and values[0] >= 0, "QUERY_NONFINITE_OR_NEGATIVE")
        expected, header = self.expected(iteration, point)
        require(int(fields[5]) == header["wind_index"], "QUERY_HEADER_WIND_INDEX")
        error = max(abs(x - float(y)) for x, y in zip(values[1:], expected))
        require(error <= tolerance, "QUERY_WRONG_PHYSICAL_WIND")
        return error


def validate_clock_sensor(clock, sensor_manifest):
    """Require resolved parameters, an explicit replay ratio, no hidden alias."""
    sensor = sensor_manifest["sensor"]
    cfg = sensor["config"]
    require(clock["frame_id"] == "map", "FRAME_ID_UNSUPPORTED")
    require(clock["stamp_zero_is_bootstrap"] is True, "BOOTSTRAP_POLICY")
    require(clock["replay_mode"] == sensor_manifest["gaden_iteration_mode"] == "seeded_time_replay",
            "REPLAY_MODE")
    dt, field_dt = float(clock["sensor_dt_s"]), float(clock["stored_field_dt_s"])
    require(all(math.isfinite(x) and x > 0 for x in (dt, field_dt)), "CLOCK_STEP")
    require(math.isclose(dt, sensor_manifest["sim_dt_s"], rel_tol=0, abs_tol=1e-12), "SENSOR_CLOCK_MISMATCH")
    require(math.isclose(field_dt / dt, clock["field_replay_speed_ratio"], rel_tol=0, abs_tol=1e-12),
            "IMPLICIT_FIELD_REPLAY_SPEED")
    require(isinstance(clock["seed"], int) and clock["seed"] == sensor["seed"], "SENSOR_SEED_MISMATCH")
    require(clock["sensor_internal_state_available_to_model"] is False, "ORACLE_SENSOR_STATE")
    require(sensor["model_version"] == "mcos-sensor-v1", "SENSOR_VERSION")
    require(cfg["mode"] in ("asymmetric", "fopdt", "mismatch", "ideal"), "UNRESOLVED_SENSOR_ALIAS")
    names = ("baseline", "dead_time_s", "drift_rate_ppm_s", "gain", "initial_input_ppm",
             "initial_state_ppm", "noise_std_ppm", "saturation_max_ppm", "saturation_min_ppm",
             "tau_recovery_s", "tau_rise_s")
    require(all(math.isfinite(cfg[name]) for name in names), "SENSOR_NONFINITE")
    require(all(cfg[name] >= 0 for name in ("dead_time_s", "noise_std_ppm", "tau_recovery_s", "tau_rise_s")),
            "SENSOR_NEGATIVE_PARAMETER")
    require(cfg["gain"] > 0 and cfg["saturation_max_ppm"] > cfg["saturation_min_ppm"], "SENSOR_RANGE")
    return {"resolved_sensor": sensor, "clock": clock, "is_physical_time_replay": field_dt == dt}


def verify_bindings(bindings):
    """No mtime-only cache: a previous PASS expires if any bound byte changes."""
    require(bool(bindings), "EMPTY_FILE_BINDINGS")
    for item in bindings:
        require(sha256(item["path"]) == item["sha256"], "STALE_BINDING:" + item["path"])


def verify_qualified_helper(executable, source, attestation):
    require(attestation.get("contract") == "CSTAR_NUMERIC_WIND_RUNTIME_CORRECTION_V1" and
            attestation.get("pass") is True and attestation.get("live_frames", 0) >= 8,
            "HELPER_NOT_LIVE_QUALIFIED")
    require(sha256(executable) == attestation["corrected_helper_sha256"], "UNQUALIFIED_HELPER_BINARY")
    require(sha256(source) == attestation["corrected_helper_source_sha256"], "UNQUALIFIED_HELPER_SOURCE")
