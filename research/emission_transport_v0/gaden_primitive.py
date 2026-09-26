"""Deterministic pinned-GADEN primitives; not an independent-packet kernel.

No RNG, full-plume simulation, bank fitting, likelihood floor, or target scorer.
Caller supplies a noise table and its global call clock. That distinction is
intentional: the fixed simulator's cyclic table cannot be replaced with IID
Gaussian increments without changing the model.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np


class PrimitiveClosureError(RuntimeError):
    pass


@dataclass(frozen=True)
class Parameters:
    dt: float = .1
    release_per_second: float = 7
    initial_sigma_cm: float = 10
    initial_ppm: float = 10
    gamma_cm2_per_second: float = 15
    configured_noise_std: float = .01
    gas_specific_gravity: float = 2.0061  # pinned gas_type=10, butane


def schedule(max_seconds: float = 300, p: Parameters = Parameters()) -> list[dict]:
    """Float32 release/save/wind clock, source of snapshot-time reconstruction.

    Save is AFTER move and BEFORE currentTime/wind update. Snapshots themselves
    do not serialize currentTime. This is a code-derived clock, not metadata.
    """
    f = np.float32
    current, last_save, last_wind, accumulator = map(f, (0, -np.finfo(f).max, 0, 0))
    wind, snapshot, total_births, step = 0, 0, 0, 0
    rows = []
    dt, rate, save_dt, wind_dt = map(f, (p.dt, p.release_per_second, .5, 1))
    while current < f(max_seconds):
        accumulator = f(accumulator + f(rate * dt))
        births = int(np.floor(accumulator))
        total_births += births
        accumulator = f(float(accumulator) - np.floor(float(accumulator)))
        if current > f(last_save + save_dt):
            rows.append(dict(snapshot_index=snapshot, step=step,
                             current_time_before_increment_seconds=float(current),
                             moves_completed=step + 1, births_total=total_births,
                             wind_index_during_move=wind))
            snapshot += 1
            last_save = current
        if current > f(last_wind + wind_dt):
            wind += 1
            if wind > 10:
                wind = 1
            last_wind = current
        current = f(current + dt)
        step += 1
    return rows


class CyclicTable:
    """The exact nextValue indexing; fixed table input, never new draws."""
    def __init__(self, table: np.ndarray, cursor: int = 0):
        self.table = np.asarray(table, dtype=np.float32)
        if self.table.shape != (1000,) or not np.isfinite(self.table).all():
            raise ValueError("expected a supplied finite 1000-entry table")
        if not 0 <= cursor < 1000:
            raise ValueError("invalid initial cursor")
        self.cursor = cursor

    def next_value(self, mean: float, std: float) -> np.float32:
        self.cursor = (self.cursor + 1) % 1000
        return np.float32(np.float32(mean) + np.float32(std) * self.table[self.cursor])

    def triple(self, p: Parameters = Parameters()) -> np.ndarray:
        # RunningSimulation ctor multiplies configured std by ten, then move
        # multiplies nextValue by dt. Preserve both operations, not sqrt(dt).
        scale = np.float32(np.float32(p.configured_noise_std) * np.float32(10))
        return np.asarray([np.float32(self.next_value(0, scale) * np.float32(p.dt))
                           for _ in range(3)], dtype=np.float32)


def require_independent_packet_closure(noise_contract: str) -> None:
    if noise_contract != "proved_exogenous_conditionally_independent_packet_kernel":
        raise PrimitiveClosureError(
            "Pinned GADEN cyclic per-thread table has population-dependent "
            "call clocks; no closed independent single-packet transition provided.")


def grow_sigma(sigma_cm: float, p: Parameters = Parameters()) -> np.float32:
    f = np.float32
    return f(f(sigma_cm) + f(f(f(p.gamma_cm2_per_second) / f(2 * f(sigma_cm))) * f(p.dt)))


def center_ppm(sigma_cm: float, p: Parameters = Parameters()) -> float:
    # Algebraic cancellation of stored moles/air constants, not a claim of
    # byte identity to the linked library's floating-point evaluation order.
    return p.initial_ppm * (p.initial_sigma_cm / float(sigma_cm)) ** 3


def read_legacy_wind(path: Path, shape_zxy: tuple[int, int, int]) -> np.ndarray:
    nz, nx, ny = shape_zxy
    raw = np.fromfile(path, dtype="<f8")
    if raw.size != 3 * nz * nx * ny or not np.isfinite(raw).all():
        raise ValueError("invalid legacy wind payload")
    # indexFrom3D=x+y*nx+z*nx*ny. Legacy file has three consecutive
    # component arrays in that index order, not occupancy text row order.
    return raw.reshape(3, nz, ny, nx).transpose(0, 1, 3, 2).astype(np.float32)


@dataclass
class Environment:
    cells: np.ndarray  # z,x,y, matching legacy text payload
    minimum: np.ndarray
    cell_size: float

    @classmethod
    def read(cls, path: Path) -> "Environment":
        header, payload = {}, []
        for line in path.read_text().splitlines():
            if line.startswith("#"):
                key, *values = line[1:].split()
                header[key] = list(map(float, values))
            elif line.strip() != ";":
                payload.extend(map(int, line.split()))
        nx, ny, nz = map(int, header["num_cells"])
        return cls(np.asarray(payload, dtype=np.uint8).reshape(nz, nx, ny),
                   np.asarray(header["env_min(m)"], dtype=np.float32),
                   np.float32(header["cell_size(m)"][0]))

    def indices(self, point: np.ndarray) -> np.ndarray:
        # glm::ivec3(float vec) truncates toward zero, NOT mathematical floor.
        return np.trunc((np.asarray(point, dtype=np.float32) - self.minimum)
                        / np.float32(self.cell_size)).astype(np.int64)

    def state(self, point: np.ndarray) -> int:
        x, y, z = self.indices(point)
        nz, nx, ny = self.cells.shape
        if x < 0 or y < 0 or z < 0 or x >= nx or y >= ny or z >= nz:
            return 3
        return int(self.cells[z, x, y])

    def los(self, start: np.ndarray, end: np.ndarray) -> bool:
        start, end = map(lambda a: np.asarray(a, dtype=np.float32), (start, end))
        if self.state(start) != 0 or self.state(end) != 0:
            return False
        delta = end - start
        distance = np.float32(np.linalg.norm(delta))
        steps = int(distance / np.float32(self.cell_size))
        # Original C++ executes no loop when steps<=1, even if its intermediate
        # divide-by-zero produces NaN/Inf. Return the same Boolean, explicitly.
        if steps <= 1:
            return True
        vector = delta / distance
        increment = np.float32(distance / steps)
        return all(self.state(start + vector * np.float32(increment * i)) == 0
                   for i in range(1, steps))

    def slide(self, start: np.ndarray, end: np.ndarray, depth: int = 0) -> tuple[np.ndarray, int]:
        """Recursive StepTowards equations, with explicit nonconvergence stop."""
        if depth > 32:
            raise PrimitiveClosureError("wall-slide recursion unresolved; no substitute boundary")
        start, end = map(lambda a: np.asarray(a, dtype=np.float32), (start, end))
        initial = self.indices(start)
        final = self.indices(end)
        if np.array_equal(initial, final):
            return end.copy(), self.state(end)
        movement = end - start
        distance = np.float32(np.linalg.norm(movement))
        direction = movement / distance
        steps = int(np.ceil(distance / np.float32(self.cell_size)))
        increment = np.float32(distance / steps)
        position = start.copy()
        previous_cell = initial
        for _ in range(steps):
            previous_position = position.copy()
            position = position + direction * increment
            current_cell = self.indices(position)
            state = self.state(position)
            if state in (1, 3):
                normal = (previous_cell - current_cell).astype(np.float32)
                normal /= np.float32(np.linalg.norm(normal))
                remaining = end - previous_position
                projection = np.float32(np.dot(remaining, normal)) * normal
                return self.slide(previous_position, end - projection, depth + 1)
            if state == 2:
                return position, 2
            previous_cell = current_cell
        return position, 0


def single_step(position: np.ndarray, sigma: float, wind: np.ndarray,
                clock: CyclicTable, env: Environment, p: Parameters = Parameters()
                ) -> tuple[np.ndarray, np.float32, bool]:
    """Conditional deterministic step, not a closed Markov transition law."""
    f = np.float32
    new = np.asarray(position, dtype=f) + np.asarray(wind, dtype=f) * f(p.dt)
    terminal = (9.8 * (1 - p.gas_specific_gravity) * 1.205 * center_ppm(sigma, p)
                * 1e-6 / (18 * 19e-6))
    new[2] = f(new[2] + f(terminal * p.dt))
    new = new + clock.triple(p)
    new, state = env.slide(position, new)
    return new, grow_sigma(sigma, p), state != 2


def filament_mark(position: np.ndarray, sigma: float, sample: np.ndarray,
                  env: Environment, p: Parameters = Parameters()) -> float:
    delta = np.asarray(position, dtype=np.float32) - np.asarray(sample, dtype=np.float32)
    distance2 = float(np.dot(delta, delta))
    if distance2 >= (float(sigma) * 3 / 100) ** 2 or not env.los(sample, position):
        return 0.0
    return center_ppm(sigma, p) * np.exp(-(10000 * distance2) / (2 * float(sigma)**2))


def pooled_probe_points(contract: dict, env: Environment) -> list[np.ndarray]:
    """Four true extractor samples per probe; not concentration at pool center."""
    out = []
    f = np.float32
    for probe in contract["probe_points"]:
        points = []
        for x in range(probe["native_x0"], probe["native_x1_exclusive"]):
            for y in range(probe["native_y0"], probe["native_y1_exclusive"]):
                points.append([f(env.minimum[0] + f(f(x) + f(.5)) * f(env.cell_size)),
                               f(env.minimum[1] + f(f(y) + f(.5)) * f(env.cell_size)),
                               f(probe["z_m"])])
        out.append(np.asarray(points, dtype=f))
    return out
