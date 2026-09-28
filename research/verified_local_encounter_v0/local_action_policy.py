"""Source-blind, opt-in local sampling action policy for Native PMFS.

Only the next navigation goal can change. The caller must send each completed
ten-sample stop window through the unchanged Native observation/update path
exactly once before asking this policy for its next goal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable


XY = tuple[float, float]
PathLength = Callable[[XY], float | None]


@dataclass(frozen=True)
class StopEvent:
    cycle_id: int
    time_s: float
    xy: XY
    concentration_ppm: float
    hit: bool
    sample_count: int


@dataclass(frozen=True)
class Decision:
    goal_xy: XY
    native_goal_xy: XY
    reason: str
    phase: str
    cycle_id: int | None
    d_ab_ppm: float | None = None
    validated_boundary: bool = False


class LocalActionPolicy:
    """One A-B-A(-C) attempt with fixed last-hit or verified-memory semantics."""

    def __init__(self, arm: str):
        if arm not in ("last_hit", "verified_local"):
            raise ValueError("Only the two frozen non-Native arms are supported")
        self.arm = arm
        self.phase = "global"
        self.trigger_consumed = False
        self.anchor: StopEvent | None = None
        self.departure: StopEvent | None = None
        self.b_goal: XY | None = None
        self.c_goal: XY | None = None
        self.last_cycle = 0
        self.last_event_time = -math.inf
        self.last_decision: Decision | None = None
        self.revocations: list[str] = []

    @staticmethod
    def _valid_event(event: StopEvent, now_s: float) -> bool:
        return (event.cycle_id >= 1 and event.sample_count == 10
                and math.isfinite(event.time_s) and 0 <= event.time_s <= now_s + 0.01
                and all(math.isfinite(v) for v in event.xy)
                and math.isfinite(event.concentration_ppm)
                and event.concentration_ppm >= 0)

    @staticmethod
    def _distance(a: XY, b: XY) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _reachable(goal: XY, path_length: PathLength, max_length: float = 2.7) -> bool:
        length = path_length(goal)
        return length is not None and math.isfinite(length) and 0 <= length <= max_length + 1e-9

    def _candidate_b(self, anchor: XY, native: XY, free_centers: Iterable[XY],
                     path_length: PathLength) -> XY | None:
        dx, dy = native[0] - anchor[0], native[1] - anchor[1]
        norm = math.hypot(dx, dy)
        direction = (1.0, 0.0) if norm <= 1e-12 else (dx / norm, dy / norm)
        candidates = []
        for point in free_centers:
            point = (float(point[0]), float(point[1]))
            r = self._distance(anchor, point)
            if 0.6 - 1e-9 <= r <= 1.2 + 1e-9 and self._reachable(point, path_length):
                cosine = ((point[0] - anchor[0]) * direction[0]
                          + (point[1] - anchor[1]) * direction[1]) / r
                candidates.append((-cosine, abs(r - 0.9), point[0], point[1], point))
        return min(candidates)[-1] if candidates else None

    def _candidate_c(self, anchor: XY, b: XY, free_centers: Iterable[XY],
                     path_length: PathLength) -> XY | None:
        mirror = (2 * anchor[0] - b[0], 2 * anchor[1] - b[1])
        candidates = []
        for point in free_centers:
            point = (float(point[0]), float(point[1]))
            mirror_error = self._distance(point, mirror)
            radial = self._distance(point, anchor)
            if (mirror_error <= 0.3 + 1e-9 and 0.6 - 1e-9 <= radial <= 1.2 + 1e-9
                    and self._reachable(point, path_length)):
                candidates.append((mirror_error, abs(radial - 0.9), point[0], point[1], point))
        return min(candidates)[-1] if candidates else None

    def _revoke(self, reason: str):
        self.revocations.append(reason)
        self.phase = "global"
        self.anchor = None
        self.departure = None
        self.b_goal = None
        self.c_goal = None

    def decide(self, native_goal_xy: XY, now_s: float, event: StopEvent | None,
               free_centers: Iterable[XY], path_length: PathLength) -> Decision:
        """Return the actual next stop; the caller remains responsible for navigation.

        `path_length(goal)` must use the unchanged VGR occupancy/BFS geometry
        from the current actual robot position. This method never sees source
        identity, source posterior, or a plume prediction.
        """
        native = (float(native_goal_xy[0]), float(native_goal_xy[1]))
        if not all(math.isfinite(v) for v in native) or not math.isfinite(now_s):
            raise ValueError("Invalid Native goal or clock")

        def emit(goal: XY, reason: str, cycle: int | None,
                 d_ab: float | None = None, validated: bool = False) -> Decision:
            decision = Decision(goal, native, reason, self.phase, cycle, d_ab, validated)
            self.last_decision = decision
            return decision

        if event is None:
            if self.phase != "global":
                self._revoke("missing_completed_stop_window")
            return emit(native, "native_no_completed_window", None)
        if not self._valid_event(event, now_s):
            if self.phase != "global":
                self._revoke("invalid_or_non_ten_sample_window")
            return emit(native, "native_invalid_window", event.cycle_id)
        if event.cycle_id == self.last_cycle:
            if self.last_decision is not None and native == self.last_decision.native_goal_xy:
                return self.last_decision
            if self.phase != "global":
                self._revoke("duplicate_cycle_with_changed_native_goal")
            return emit(native, "native_duplicate_cycle", event.cycle_id)
        if event.cycle_id < self.last_cycle or event.time_s <= self.last_event_time:
            if self.phase != "global":
                self._revoke("nonmonotonic_cycle_or_time")
            return emit(native, "native_nonmonotonic_window", event.cycle_id)
        if self.phase != "global" and event.cycle_id != self.last_cycle + 1:
            self._revoke("skipped_window_during_local_cycle")
        self.last_cycle = event.cycle_id
        self.last_event_time = event.time_s

        if self.phase == "global":
            if self.trigger_consumed or not event.hit or event.time_s > 180:
                return emit(native, "native_global", event.cycle_id)
            self.trigger_consumed = True
            b = self._candidate_b(event.xy, native, free_centers, path_length)
            if b is None:
                self._revoke("no_reachable_local_departure")
                return emit(native, "native_no_local_departure", event.cycle_id)
            self.anchor = event
            self.b_goal = b
            self.phase = "to_b"
            return emit(b, "local_departure", event.cycle_id)

        assert self.anchor is not None and self.b_goal is not None
        if event.time_s - self.anchor.time_s > 75:
            self._revoke("anchor_memory_expired")
            return emit(native, "native_expired", event.cycle_id)

        if self.phase == "to_b":
            if self._distance(event.xy, self.b_goal) > 0.15:
                self._revoke("departure_stop_pose_mismatch")
                return emit(native, "native_departure_mismatch", event.cycle_id)
            self.departure = event
            if self.arm == "last_hit" and event.hit:
                self._revoke("new_hit_replaces_last_hit")
                return emit(native, "native_new_hit", event.cycle_id)
            if not self._reachable(self.anchor.xy, path_length):
                self._revoke("anchor_return_unreachable")
                return emit(native, "native_anchor_unreachable", event.cycle_id)
            self.phase = "to_a"
            return emit(self.anchor.xy, "last_hit_return" if self.arm == "last_hit" else "verification_return",
                        event.cycle_id)

        if self.phase == "to_a":
            if self._distance(event.xy, self.anchor.xy) > 0.15:
                self._revoke("revisit_stop_pose_mismatch")
                return emit(native, "native_revisit_mismatch", event.cycle_id)
            assert self.departure is not None
            dt = event.time_s - self.anchor.time_s
            w = (self.departure.time_s - self.anchor.time_s) / dt
            d_ab = (self.departure.concentration_ppm
                    - (1 - w) * self.anchor.concentration_ppm
                    - w * event.concentration_ppm)
            if self.arm == "last_hit":
                self._revoke("last_hit_return_completed")
                return emit(native, "native_after_last_hit_return", event.cycle_id, d_ab)
            if not event.hit or self.departure.hit or event.time_s > 250:
                reason = ("revisit_miss" if not event.hit else
                          "departure_not_a_boundary" if self.departure.hit else "late_validation")
                self._revoke(reason)
                return emit(native, "native_unvalidated_local_memory", event.cycle_id, d_ab)
            c = self._candidate_c(self.anchor.xy, self.b_goal, free_centers, path_length)
            if c is None:
                self._revoke("mirror_goal_unreachable")
                return emit(native, "native_no_mirror_goal", event.cycle_id, d_ab)
            self.c_goal = c
            self.phase = "to_c"
            return emit(c, "validated_boundary_mirror_sample", event.cycle_id, d_ab, True)

        if self.phase == "to_c":
            if self.c_goal is not None and self._distance(event.xy, self.c_goal) > 0.15:
                self._revoke("mirror_stop_pose_mismatch")
                return emit(native, "native_mirror_mismatch", event.cycle_id)
            self._revoke("local_cycle_completed")
            return emit(native, "native_after_verified_cycle", event.cycle_id)

        raise RuntimeError(f"Unknown local phase: {self.phase}")
