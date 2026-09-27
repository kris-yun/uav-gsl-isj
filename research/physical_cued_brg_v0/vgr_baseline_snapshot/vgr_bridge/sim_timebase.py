"""ROS-independent deterministic timebase for VGR replay and UAV motion."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class DeterministicTimebase:
    sim_dt_s: float
    realtime_factor: float = 1.0
    step: int = 0

    def __post_init__(self) -> None:
        if not math.isfinite(self.sim_dt_s) or self.sim_dt_s <= 0.0:
            raise ValueError("sim_dt_s must be finite and positive")
        if not math.isfinite(self.realtime_factor) or self.realtime_factor <= 0.0:
            raise ValueError("realtime_factor must be finite and positive")
        if self.step < 0:
            raise ValueError("step must be nonnegative")

    @property
    def time_s(self) -> float:
        return self.step * self.sim_dt_s

    @property
    def wall_step_period_s(self) -> float:
        return self.sim_dt_s / self.realtime_factor

    def advance(self) -> tuple[int, float]:
        self.step += 1
        return self.step, self.time_s

    def maximum_motion_distance(self, max_speed_m_s: float, step_cap_m: float) -> float:
        if max_speed_m_s <= 0.0 or step_cap_m <= 0.0:
            raise ValueError("speed and step cap must be positive")
        return min(step_cap_m, max_speed_m_s * self.sim_dt_s)

    def replay_iteration(self, max_iteration: int, seed: int, mode: str) -> int:
        if max_iteration <= 0:
            return 0
        if mode == "fixed_debug":
            return min(1500, max_iteration)
        if mode == "seeded_time_replay":
            usable = max(1, max_iteration - 1)
            offset = (7919 * (int(seed) + 1)) % usable
            return int((offset + self.step) % usable)
        raise ValueError(f"unknown replay mode {mode!r}")

    def stamp_parts(self) -> tuple[int, int]:
        seconds = int(math.floor(self.time_s))
        nanoseconds = int(round((self.time_s - seconds) * 1.0e9))
        if nanoseconds >= 1_000_000_000:
            seconds += 1
            nanoseconds -= 1_000_000_000
        return seconds, nanoseconds
