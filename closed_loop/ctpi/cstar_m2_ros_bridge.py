"""ROS callback bridge for the strict online M2 session.

The ROS node remains responsible for message-envelope checks (frame, units and
stamp extraction). This bridge receives the normalized ``kind/stamp/values``
triples used by :mod:`ctpi_v2_ingress`, so the scientific session cannot be
silently fed callback-order or future data. A route must be explicitly armed
between joined frames by the controller/planner; no route or source truth is
invented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from cstar_m2_online import OnlineM2Session, RouteLawProvider


@dataclass(frozen=True)
class BridgeStats:
    joined_frames: int
    predictions: int
    observations: int


class CstarM2RosBridge:
    """Small, testable adapter used from real ROS subscriber callbacks."""

    def __init__(self, provider: RouteLawProvider,
                 on_frame: Callable[[object], None] | None = None):
        self.session = OnlineM2Session(provider)
        self.on_frame = on_frame
        self._joined = 0

    @property
    def stats(self) -> BridgeStats:
        return BridgeStats(self._joined, self.session.prediction_count,
                           self.session.observation_count)

    @property
    def ready(self) -> bool:
        return self.session.ready

    def push_normalized(self, kind: str, stamp_ns: int, values: Sequence[float]) -> int:
        before = len(self.session.prefix)
        accepted = self.session.ingest(kind, stamp_ns, values)
        after = len(self.session.prefix)
        if after > before:
            self._joined += after - before
            if self.on_frame is not None:
                for frame in self.session.prefix[before:after]:
                    self.on_frame(frame)
        return accepted

    def arm_route(self, source_xy, route_xy):
        if not self.ready:
            raise ValueError("CSTAR_M2_ROS_NOT_READY")
        return self.session.predict_before_observe(source_xy, route_xy)

    def finish(self, final_stamp_ns: int) -> None:
        self.session.finish(final_stamp_ns)

